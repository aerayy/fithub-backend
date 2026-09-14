"""
WebSocket connection manager — çoklu worker'da tutarlı anlık iletim.

Bağlantılar her gunicorn worker'ının kendi belleğinde tutulur (3 worker).
Eskiden `send_to_user` yalnızca aynı worker'daki bağlantılara ulaşıyordu:
gönderen A worker'ında, alıcı B'deyse mesaj kaydediliyor ama anlık gitmiyordu.

Çözüm: PostgreSQL LISTEN/NOTIFY ile worker'lar arası yayın (ek altyapı yok).
- send_to_user: önce yerel bağlantılara verir, sonra `ws_fanout` kanalına
  NOTIFY basar (payload: origin worker id + user_id + mesaj).
- Her worker açılışta bir dinleyici thread başlatır (start_fanout_listener):
  kendi origin'inden gelenleri atlar, diğerlerini yerel bağlantılara iletir.
- NOTIFY payload sınırı 8000 bayt; daha büyük mesajlar yalnızca yerel
  teslim edilir (alıcı ekranı açınca DB'den alır) ve uyarı loglanır.
"""
import asyncio
import json
import logging
import select
import threading
import time
import uuid
from typing import Dict, Optional, Set

import psycopg2
from fastapi import WebSocket

logger = logging.getLogger(__name__)

FANOUT_CHANNEL = "ws_fanout"
_NOTIFY_MAX_BYTES = 7900


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.origin_id = uuid.uuid4().hex
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._listener_thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    # ── bağlantı yönetimi ────────────────────────────────────────────────
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        total = sum(len(v) for v in self.active_connections.values())
        logger.info(f"WS connected: user_id={user_id}, total_connections={total}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WS disconnected: user_id={user_id}")

    def is_online(self, user_id: int) -> bool:
        """Yalnızca BU worker'daki bağlantıları bilir (fanout sonrası yaklaşık)."""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0

    # ── teslim ───────────────────────────────────────────────────────────
    async def _send_local(self, user_id: int, message: dict) -> int:
        """Bu worker'daki bağlantılara gönder; teslim sayısını döndür."""
        connections = self.active_connections.get(user_id, set())
        dead = []
        delivered = 0
        for ws in list(connections):
            try:
                await ws.send_json(message)
                delivered += 1
            except Exception:
                dead.append(ws)
        for ws in dead:
            connections.discard(ws)
        return delivered

    async def send_to_user(self, user_id: int, message: dict):
        """Kullanıcının TÜM worker'lardaki bağlantılarına gönder."""
        await self._send_local(user_id, message)
        self._publish(user_id, message)

    def _publish(self, user_id: int, message: dict) -> None:
        """Diğer worker'lara NOTIFY. Hata anlık iletimi bozmaz, sadece loglanır."""
        try:
            payload = json.dumps(
                {"o": self.origin_id, "u": user_id, "m": message},
                ensure_ascii=False, default=str,
            )
            if len(payload.encode("utf-8")) > _NOTIFY_MAX_BYTES:
                logger.warning(
                    "WS fanout: payload %d bayt > sınır, diğer worker'lara iletilmedi (user=%s type=%s)",
                    len(payload), user_id, message.get("type"),
                )
                return
            from app.core.database import _get_pool
            pool = _get_pool()
            conn = pool.getconn()
            try:
                cur = conn.cursor()
                cur.execute("SELECT pg_notify(%s, %s)", (FANOUT_CHANNEL, payload))
                conn.commit()
            finally:
                try:
                    pool.putconn(conn)
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"WS fanout publish hatası: {e}")

    # ── dinleyici ────────────────────────────────────────────────────────
    def start_fanout_listener(self, loop: asyncio.AbstractEventLoop) -> None:
        """Uygulama açılışında (her worker) bir kez çağrılır."""
        if self._listener_thread is not None:
            return
        self._loop = loop
        t = threading.Thread(target=self._listen_loop, name="ws-fanout-listener", daemon=True)
        t.start()
        self._listener_thread = t

    def stop_fanout_listener(self) -> None:
        self._stop.set()

    def _listen_loop(self) -> None:
        from app.core.config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
        backoff = 1
        while not self._stop.is_set():
            conn = None
            try:
                conn = psycopg2.connect(
                    dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
                    host=DB_HOST, port=DB_PORT, connect_timeout=10,
                )
                conn.autocommit = True
                cur = conn.cursor()
                cur.execute(f"LISTEN {FANOUT_CHANNEL}")
                logger.info("WS fanout listener bağlı (origin=%s)", self.origin_id[:8])
                backoff = 1
                while not self._stop.is_set():
                    ready, _, _ = select.select([conn], [], [], 5.0)
                    if not ready:
                        continue
                    conn.poll()
                    while conn.notifies:
                        notify = conn.notifies.pop(0)
                        self._on_notify(notify.payload)
            except Exception as e:
                logger.warning("WS fanout listener hatası: %s — %ss sonra yeniden bağlanılacak", e, backoff)
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except Exception:
                        pass

    def _on_notify(self, payload: str) -> None:
        try:
            data = json.loads(payload)
        except Exception:
            return
        if data.get("o") == self.origin_id:
            return  # kendi yayınımız, yerelde zaten teslim edildi
        user_id = data.get("u")
        message = data.get("m")
        if user_id is None or message is None or self._loop is None:
            return
        try:
            user_id = int(user_id)
        except Exception:
            return
        if user_id not in self.active_connections:
            return  # bu worker'da bağlantısı yok
        asyncio.run_coroutine_threadsafe(self._send_local(user_id, message), self._loop)


manager = ConnectionManager()

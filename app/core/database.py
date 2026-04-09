from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from app.core.config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

# Connection pool: min 5, max 20 connections
# 3000 users with 3 gunicorn workers = ~1000 concurrent per worker
# 20 pool connections per worker handles burst traffic
_pool = None


def _get_pool():
    global _pool
    if _pool is None or _pool.closed:
        _pool = ThreadedConnectionPool(
            minconn=5,
            maxconn=20,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            cursor_factory=RealDictCursor,
        )
    return _pool


def get_db():
    """FastAPI dependency — yields a pooled connection, returns it after request."""
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)


def close_pool():
    """Call on app shutdown to close all connections."""
    global _pool
    if _pool and not _pool.closed:
        _pool.closeall()
        _pool = None

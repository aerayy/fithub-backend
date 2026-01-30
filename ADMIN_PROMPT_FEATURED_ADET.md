# CURSOR PROMPT (ADMIN PANEL) — Featured Foods + Adet (Piece) Unit

**Backend güncellendi.** Şimdi admin panelde şu değişiklikleri yap:

---

## A) API çağrısını güncelle

`searchFoods` artık `featured_only=true` (varsayılan) ile çağrılsın. Böylece sadece öne çıkarılan besinler listelenir.

```js
// api.js veya ilgili yerde
export async function searchFoods(query, featuredOnly = true) {
  const params = new URLSearchParams({ q: query, limit: 10 });
  if (featuredOnly !== false) params.set('featured_only', 'true');
  const res = await api.get(`/foods/search?${params}`);
  return res.data.foods;
}
```

API response'a `piece_weight_g` eklendi:
```json
{
  "id": 9,
  "name_tr": "Büyük Yumurta",
  "piece_weight_g": 50,
  "nutrients": { "calories_kcal": 148, "protein_g": 12.4, ... }
}
```
- `piece_weight_g`: 1 adet için ortalama gram (null = sadece gram kullanılır)

---

## B) Gram / Adet birim seçimi

Her food item row'da:
- Eğer `piece_weight_g` varsa: **birim seçimi** göster (radio veya select): `Gram` | `Adet`
- `Gram` seçiliyse: mevcut gibi gram input, makro = (gram/100) * per_100g
- `Adet` seçiliyse: adet input (1, 2, 3...), `grams = adet * piece_weight_g`, makro aynı formül

**Item state genişlet:**
```js
{
  ...existing,
  unit: "g" | "adet",  // varsayılan: piece_weight_g varsa "adet", yoksa "g"
  amount: 100,         // gram veya adet (unit'e göre)
  // Hesaplanan grams (makro hesabı için):
  grams: unit === "g" ? amount : amount * piece_weight_g
}
```

**UI:**
```
[Besin: Tavuk Göğsü] [○ Gram ● Adet] [2] [444 kcal | 37g P | ...]
```
- piece_weight_g yoksa sadece: `[Besin] [150] gram [222 kcal | ...]`

---

## C) Tüm besinleri göster seçeneği (opsiyonel)

FoodSearchInput içinde veya yanında küçük bir checkbox/link:
- "Tüm besinleri göster" işaretlenince `featured_only=false` ile ara
- Varsayılan: kapalı (sadece featured)

---

## Özet

1. `searchFoods(query, featuredOnly=true)` — featured_only parametresi
2. `piece_weight_g` değerini response'dan al, item'a ekle
3. unit: "g" | "adet" — piece_weight_g varsa seçenek sun
4. amount + unit ile grams hesapla, makroları güncelle

# Food Database (USDA Integration)

USDA FoodData Central tabanlı besin veritabanı altyapısı.

## 📋 Özellikler

- **Food Search API**: Türkçe/İngilizce besin arama
- **Food Detail API**: Detaylı besin bilgisi ve 100g bazlı makro değerler
- **USDA Import Script**: USDA FoodData Central'dan otomatik besin içe aktarma
- **Turkish Localization**: Türkçe isim ve alias desteği

## 🗄️ Veritabanı Yapısı

### Tablolar

1. **food_items**: Besin kayıtları (USDA FDC ID, İngilizce isim)
2. **food_nutrients_100g**: 100g bazlı makro değerler (kalori, protein, yağ, karbonhidrat, lif, şeker, sodyum)
3. **food_localization_tr**: Türkçe isim ve arama aliasları

### Migration

```bash
# Migration zaten uygulandı (004_create_food_tables.sql)
psql -h localhost -p 5433 -U postgres -d fithub -f migrations/004_create_food_tables.sql
```

## 🔌 API Endpoints

### 1. Search Foods

**GET** `/foods/search?q=<query>&limit=20&offset=0`

Türkçe/İngilizce besin arama. Öncelik sırası:
1. Türkçe isim (food_localization_tr.name_tr)
2. Türkçe aliaslar (food_localization_tr.aliases_tr)
3. İngilizce isim (food_items.name_en)

**Query Parameters:**
- `q` (required): Arama terimi (min 2 karakter)
- `limit` (optional): Sonuç sayısı (default: 20, max: 100)
- `offset` (optional): Sayfalama offset (default: 0)

**Response:**
```json
{
  "foods": [
    {
      "id": 1,
      "fdc_id": 747447,
      "name_en": "Chicken, broiler, breast, skinless, boneless, meat, raw",
      "name_tr": "Tavuk göğsü",
      "description": "...",
      "data_type": "Foundation",
      "nutrients": {
        "energy_kcal": 120,
        "protein_g": 22.5,
        "fat_g": 2.6,
        "carbohydrate_g": 0,
        "fiber_g": 0,
        "sugar_g": 0,
        "sodium_mg": 63
      }
    }
  ],
  "total": 1
}
```

### 2. Get Food Detail

**GET** `/foods/{food_id}`

Belirli bir besinin detaylı bilgisi.

**Response:** (Search ile aynı format, tek besin)

## 📥 USDA Import Script

USDA FoodData Central API'den besin verisi içe aktarma.

### Gereksinimler

1. **USDA API Key** (ücretsiz): https://fdc.nal.usda.gov/api-key-signup.html
2. `.env` dosyasına ekle:
   ```env
   USDA_API_KEY=your_api_key_here
   ```

### Kullanım

```bash
# Tavuk göğsü ara ve import et
python3 scripts/usda_import.py --search "chicken breast" --limit 10

# Elma ara ve import et
python3 scripts/usda_import.py --search "apple" --limit 5

# Yumurta ara ve import et
python3 scripts/usda_import.py --search "egg" --limit 10
```

### Script Özellikleri

- USDA FoodData Central API ile arama
- Foundation ve SR Legacy veri setleri (kaliteli veriler)
- 100g bazlı normalize makro değerler
- Duplicate kontrolü (fdc_id bazlı)
- Otomatik commit

### İçe Aktarılan Nutrient'ler

- **Energy**: Kalori (kcal/100g)
- **Protein**: Protein (g/100g)
- **Total lipid (fat)**: Toplam yağ (g/100g)
- **Carbohydrate**: Karbonhidrat (g/100g)
- **Fiber**: Posa (g/100g)
- **Sugar**: Şeker (g/100g)
- **Sodium**: Sodyum (mg/100g)

## 🔧 Manuel Türkçe Ekleme

USDA'den gelen besinlere Türkçe isim eklemek için:

```sql
-- Örnek: "Chicken breast" için Türkçe ekle
INSERT INTO food_localization_tr (food_id, name_tr, aliases_tr, created_at, updated_at)
VALUES (
    1,  -- food_items.id
    'Tavuk göğsü',
    ARRAY['tavuk', 'göğüs', 'chicken', 'piliç'],
    NOW(),
    NOW()
)
ON CONFLICT (food_id) DO UPDATE SET
    name_tr = EXCLUDED.name_tr,
    aliases_tr = EXCLUDED.aliases_tr,
    updated_at = NOW();
```

## 📊 Test Örnekleri

### Swagger UI

1. Server'ı başlat: `uvicorn app.main:app --reload`
2. Swagger: http://localhost:8000/docs
3. `/foods/search` endpoint'i test et

### cURL

```bash
# Search
curl "http://localhost:8000/foods/search?q=chicken&limit=5"

# Detail
curl "http://localhost:8000/foods/1"
```

## 🚀 Production Kullanımı

### 1. USDA API Key Ekle

Render/Heroku environment variables:
```
USDA_API_KEY=your_production_key
```

### 2. İlk Veri Yükleme

```bash
# Yaygın besinleri import et
python3 scripts/usda_import.py --search "chicken" --limit 20
python3 scripts/usda_import.py --search "beef" --limit 20
python3 scripts/usda_import.py --search "fish" --limit 20
python3 scripts/usda_import.py --search "egg" --limit 10
python3 scripts/usda_import.py --search "milk" --limit 10
python3 scripts/usda_import.py --search "apple" --limit 10
python3 scripts/usda_import.py --search "banana" --limit 10
python3 scripts/usda_import.py --search "rice" --limit 10
python3 scripts/usda_import.py --search "bread" --limit 10
python3 scripts/usda_import.py --search "pasta" --limit 10
```

### 3. Türkçe Lokalizasyon Batch

Excel/CSV'den toplu Türkçe import için script yazılabilir (ihtiyaç halinde).

## 📝 Notlar

- **100g Base**: Tüm makro değerler 100g bazlı normalize
- **No Auth**: Food endpoints auth gerektirmez (public data)
- **USDA Datasets**: Foundation ve SR Legacy kullanıyoruz (Branded eklenebilir)
- **Turkish Search**: Türkçe arama için food_localization_tr tablosu manuel doldurulmalı
- **Rate Limit**: USDA API free tier: 1000 req/hour

## 🔗 Kaynaklar

- [USDA FoodData Central](https://fdc.nal.usda.gov/)
- [API Documentation](https://fdc.nal.usda.gov/api-guide.html)
- [Get API Key](https://fdc.nal.usda.gov/api-key-signup.html)

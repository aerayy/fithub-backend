"""
Foods API - USDA FoodData Central based food database
Endpoints for searching and retrieving food items with macros (100g base)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.database import get_db
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/foods", tags=["foods"])


# ---- Schemas ----
class FoodNutrients(BaseModel):
    calories_kcal: Optional[float] = None
    protein_g: Optional[float] = None
    fat_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    sodium_mg: Optional[float] = None


class FoodItemOut(BaseModel):
    id: int
    fdc_id: Optional[int] = None
    name_en: str
    name_tr: Optional[str] = None
    description: Optional[str] = None
    data_type: Optional[str] = None
    piece_weight_g: Optional[float] = None  # 1 adet = X gram (null = sadece gram)
    nutrients: FoodNutrients


class FoodSearchResult(BaseModel):
    foods: List[FoodItemOut]
    total: int


# ---- Endpoints ----
@router.get("/search", response_model=FoodSearchResult)
def search_foods(
    q: str = Query(..., min_length=2, description="Search query (min 2 chars)"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    featured_only: bool = Query(True, description="Show only curated featured foods"),
    db=Depends(get_db),
):
    """
    Search foods by name (Turkish or English).
    
    featured_only=True (default): Sadece öne çıkarılan besinler - daha temiz liste.
    featured_only=False: Tüm eşleşen besinler.
    
    piece_weight_g: Varsa "Adet" birimi kullanılabilir (1 adet = X gram).
    """
    cur = db.cursor()
    search_pattern = f"%{q.lower()}%"

    cur.execute(
        """
        WITH matched_foods AS (
            SELECT DISTINCT
                fi.id,
                fi.fdc_id,
                fi.name_en,
                fi.description,
                fi.data_type,
                COALESCE(fl.name_tr, fi.name_en) as name_tr,
                fl.piece_weight_g,
                CASE
                    WHEN fl.name_tr ILIKE %s THEN 3
                    WHEN fl.aliases_tr IS NOT NULL AND EXISTS (
                        SELECT 1 FROM unnest(fl.aliases_tr) alias
                        WHERE alias ILIKE %s
                    ) THEN 2
                    WHEN fi.name_en ILIKE %s THEN 1
                    ELSE 0
                END as match_score
            FROM food_items fi
            LEFT JOIN food_localization_tr fl ON fi.id = fl.food_id
            WHERE
                (fl.name_tr ILIKE %s
                OR (fl.aliases_tr IS NOT NULL AND EXISTS (
                    SELECT 1 FROM unnest(fl.aliases_tr) alias
                    WHERE alias ILIKE %s
                ))
                OR fi.name_en ILIKE %s)
                AND (%s = FALSE OR COALESCE(fl.is_featured, FALSE) = TRUE)
        )
        SELECT
            mf.id,
            mf.fdc_id,
            mf.name_en,
            mf.name_tr,
            mf.description,
            mf.data_type,
            mf.piece_weight_g,
            fn.calories_kcal,
            fn.protein_g,
            fn.fat_g,
            fn.carbs_g,
            fn.fiber_g,
            fn.sugar_g,
            fn.sodium_mg
        FROM matched_foods mf
        LEFT JOIN food_nutrients_100g fn ON mf.id = fn.food_id
        ORDER BY mf.match_score DESC, mf.name_tr ASC
        LIMIT %s OFFSET %s
        """,
        (
            search_pattern,
            search_pattern,
            search_pattern,
            search_pattern,
            search_pattern,
            search_pattern,
            featured_only,
            limit,
            offset,
        ),
    )
    rows = cur.fetchall() or []

    # Count total matches
    cur.execute(
        """
        SELECT COUNT(DISTINCT fi.id)
        FROM food_items fi
        LEFT JOIN food_localization_tr fl ON fi.id = fl.food_id
        WHERE
            (fl.name_tr ILIKE %s
            OR (fl.aliases_tr IS NOT NULL AND EXISTS (
                SELECT 1 FROM unnest(fl.aliases_tr) alias
                WHERE alias ILIKE %s
            ))
            OR fi.name_en ILIKE %s)
            AND (%s = FALSE OR COALESCE(fl.is_featured, FALSE) = TRUE)
        """,
        (search_pattern, search_pattern, search_pattern, featured_only),
    )
    total = cur.fetchone()["count"] or 0

    foods = []
    for row in rows:
        foods.append(
            FoodItemOut(
                id=row["id"],
                fdc_id=row.get("fdc_id"),
                name_en=row["name_en"],
                name_tr=row.get("name_tr"),
                description=row.get("description"),
                data_type=row.get("data_type"),
                piece_weight_g=row.get("piece_weight_g"),
                nutrients=FoodNutrients(
                    calories_kcal=row.get("calories_kcal"),
                    protein_g=row.get("protein_g"),
                    fat_g=row.get("fat_g"),
                    carbs_g=row.get("carbs_g"),
                    fiber_g=row.get("fiber_g"),
                    sugar_g=row.get("sugar_g"),
                    sodium_mg=row.get("sodium_mg"),
                ),
            )
        )

    return FoodSearchResult(foods=foods, total=total)


@router.get("/{food_id}", response_model=FoodItemOut)
def get_food_detail(
    food_id: int,
    db=Depends(get_db),
):
    """
    Get detailed food info by ID.
    
    Returns: Food item with 100g macro values
    """
    cur = db.cursor()

    cur.execute(
        """
        SELECT
            fi.id,
            fi.fdc_id,
            fi.name_en,
            fi.description,
            fi.data_type,
            COALESCE(fl.name_tr, fi.name_en) as name_tr,
            fl.piece_weight_g,
            fn.calories_kcal,
            fn.protein_g,
            fn.fat_g,
            fn.carbs_g,
            fn.fiber_g,
            fn.sugar_g,
            fn.sodium_mg
        FROM food_items fi
        LEFT JOIN food_localization_tr fl ON fi.id = fl.food_id
        LEFT JOIN food_nutrients_100g fn ON fi.id = fn.food_id
        WHERE fi.id = %s
        """,
        (food_id,),
    )
    row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Food not found")

    return FoodItemOut(
        id=row["id"],
        fdc_id=row.get("fdc_id"),
        name_en=row["name_en"],
        name_tr=row.get("name_tr"),
        description=row.get("description"),
        data_type=row.get("data_type"),
        piece_weight_g=row.get("piece_weight_g"),
        nutrients=FoodNutrients(
            calories_kcal=row.get("calories_kcal"),
            protein_g=row.get("protein_g"),
            fat_g=row.get("fat_g"),
            carbs_g=row.get("carbs_g"),
            fiber_g=row.get("fiber_g"),
            sugar_g=row.get("sugar_g"),
            sodium_mg=row.get("sodium_mg"),
        ),
    )

# app/api/client/daily_targets.py
"""
Daily Targets endpoint for clients.

Computes daily water, calorie, and step goals based on client profile.
Uses Mifflin-St Jeor BMR formula with MVP assumptions.

Example curl test:
  curl -X GET "http://localhost:8000/client/daily-targets" \
    -H "Authorization: Bearer YOUR_TOKEN"

Expected output:
  {
    "water_liters": 2.8,
    "kcal_goal": 2200,
    "step_goal": 10000,
    "assumptions": {
      "age": 30,
      "activity_multiplier": 1.55
    }
  }
"""
from fastapi import Depends, HTTPException
from app.core.database import get_db
from app.core.security import require_role
from .routes import router


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(value, max_val))


def normalize_goal_type(goal_type: str) -> str:
    """
    Normalize goal_type to: lose_weight, gain_muscle, or maintain.
    Returns 'maintain' for unknown/other values.
    """
    if not goal_type:
        return "maintain"
    
    goal_lower = goal_type.lower().strip()
    
    # Check for lose_weight variations
    if any(keyword in goal_lower for keyword in ["lose", "weight loss", "fat loss", "cutting"]):
        return "lose_weight"
    
    # Check for gain_muscle variations
    if any(keyword in goal_lower for keyword in ["gain", "muscle", "bulk", "bulking"]):
        return "gain_muscle"
    
    # Default to maintain
    return "maintain"


def normalize_gender(gender: str) -> str:
    """
    Normalize gender to: male, female, or unknown.
    """
    if not gender:
        return "unknown"
    
    gender_lower = gender.lower().strip()
    
    if gender_lower in ["male", "m", "man", "erkek"]:
        return "male"
    elif gender_lower in ["female", "f", "woman", "kadın"]:
        return "female"
    else:
        return "unknown"


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """
    Calculate Basal Metabolic Rate using Mifflin-St Jeor formula.
    
    male:   BMR = 10*w + 6.25*h - 5*age + 5
    female: BMR = 10*w + 6.25*h - 5*age - 161
    unknown: BMR = 10*w + 6.25*h - 5*age (no adjustment)
    """
    base_bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age
    
    if gender == "male":
        return base_bmr + 5
    elif gender == "female":
        return base_bmr - 161
    else:  # unknown
        return base_bmr


def calculate_water_liters(weight_kg: float) -> float:
    """
    Calculate daily water intake in liters.
    Formula: weight_kg * 0.035, clamped between 2.0 and 4.0 liters.
    """
    water = weight_kg * 0.035
    return round(clamp(water, 2.0, 4.0), 1)


def calculate_kcal_goal(weight_kg: float, height_cm: float, gender: str, goal_type: str) -> int:
    """
    Calculate daily calorie goal.
    
    Uses:
    - Assumed age: 30
    - Activity multiplier: 1.55 (moderate)
    - Goal adjustments:
      - lose_weight: TDEE - 300
      - gain_muscle: TDEE + 250
      - maintain: TDEE
    - Minimum: 1200 kcal (safety clamp)
    """
    assumed_age = 30
    activity_multiplier = 1.55
    
    # Calculate BMR
    bmr = calculate_bmr(weight_kg, height_cm, assumed_age, gender)
    
    # Calculate TDEE
    tdee = bmr * activity_multiplier
    
    # Apply goal adjustment
    normalized_goal = normalize_goal_type(goal_type)
    
    if normalized_goal == "lose_weight":
        kcal = tdee - 300
    elif normalized_goal == "gain_muscle":
        kcal = tdee + 250
    else:  # maintain
        kcal = tdee
    
    # Round to nearest integer and apply minimum
    kcal = max(1200, round(kcal))
    
    return int(kcal)


def calculate_step_goal(goal_type: str) -> int:
    """
    Calculate daily step goal based on goal type.
    
    - lose_weight: 11000 steps
    - gain_muscle: 9000 steps
    - maintain/other: 10000 steps
    """
    normalized_goal = normalize_goal_type(goal_type)
    
    if normalized_goal == "lose_weight":
        return 11000
    elif normalized_goal == "gain_muscle":
        return 9000
    else:  # maintain
        return 10000


@router.get("/daily-targets")
def get_daily_targets(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """
    Get daily targets (water, calories, steps) for the logged-in client.
    
    Requires:
    - Client must have completed onboarding (onboarding_done = true)
    - Client must have weight_kg and height_cm in clients table
    
    Returns computed targets based on client profile with MVP assumptions.
    """
    client_user_id = current_user["id"]
    cur = db.cursor()
    
    try:
        # Fetch client profile from clients table
        cur.execute(
            """
            SELECT 
                weight_kg,
                height_cm,
                gender,
                goal_type,
                onboarding_done
            FROM clients
            WHERE user_id = %s
            """,
            (client_user_id,),
        )
        
        client_row = cur.fetchone()
        
        # Check if client row exists
        if not client_row:
            raise HTTPException(
                status_code=400,
                detail="Onboarding not completed"
            )
        
        # Check if onboarding is done
        if not client_row["onboarding_done"]:
            raise HTTPException(
                status_code=400,
                detail="Onboarding not completed"
            )
        
        # Check if required measurements exist
        weight_kg = client_row["weight_kg"]
        height_cm = client_row["height_cm"]
        
        if weight_kg is None or height_cm is None:
            raise HTTPException(
                status_code=400,
                detail="Missing client measurements"
            )
        
        # Get other fields (may be None)
        gender = client_row["gender"]
        goal_type = client_row["goal_type"]
        
        # Normalize gender
        normalized_gender = normalize_gender(gender)
        
        # Calculate targets
        water_liters = calculate_water_liters(weight_kg)
        kcal_goal = calculate_kcal_goal(weight_kg, height_cm, normalized_gender, goal_type)
        step_goal = calculate_step_goal(goal_type)
        
        return {
            "water_liters": water_liters,
            "kcal_goal": kcal_goal,
            "step_goal": step_goal,
            "assumptions": {
                "age": 30,
                "activity_multiplier": 1.55
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log and return 500 for unexpected errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting daily targets for user_id={client_user_id}: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get daily targets: {str(e)}"
        )

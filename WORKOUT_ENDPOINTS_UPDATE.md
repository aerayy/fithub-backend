# Workout Endpoints Update - Implementation Summary

## Overview
Added support for structured workout day payloads (JSONB) while maintaining backward compatibility with existing flat exercise arrays.

## Files Changed

### 1. Migration
- **File**: `migrations/003_add_day_payload_to_workout_days.sql`
- **Change**: Added `day_payload JSONB` column to `workout_days` table

### 2. New Client Endpoint
- **File**: `app/api/client/workouts.py` (NEW)
- **Endpoint**: `GET /client/workouts/active`
- **Auth**: Requires `client` role
- **Purpose**: Returns active workout program in UI-friendly structure

### 3. Coach Save Endpoint Update
- **File**: `app/api/coach/routes.py`
- **Endpoint**: `POST /coach/students/{student_user_id}/workout-programs`
- **Change**: Now accepts both old format (array) and new format (object with structured payload)

### 4. Router Registration
- **File**: `app/api/client/routes.py`
- **Change**: Added import for `workouts` module

---

## SQL Migration

Run this SQL on Render (or your PostgreSQL database):

```sql
-- Migration: Add day_payload JSONB column to workout_days table
ALTER TABLE workout_days 
ADD COLUMN IF NOT EXISTS day_payload jsonb;

-- Add comment for documentation
COMMENT ON COLUMN workout_days.day_payload IS 'Structured workout day data: {title, kcal, coach_note, warmup: {duration_min, items[]}, blocks: [{title, items[]}]}';
```

---

## API Endpoints

### GET /client/workouts/active

**Request:**
```bash
GET /client/workouts/active
Authorization: Bearer <client_token>
```

**Response (200 OK):**
```json
{
  "program": {
    "id": 1,
    "title": "Upper Body Power",
    "week_number": 1,
    "created_at": "2024-01-15T10:00:00",
    "updated_at": "2024-01-15T10:00:00"
  },
  "week": {
    "mon": {
      "title": "Upper Body Power",
      "kcal": "500",
      "coach_note": "Focus on form, rest 60s between sets",
      "warmup": {
        "duration_min": "10",
        "items": [
          {
            "type": "exercise",
            "name": "Arm Circles",
            "sets": 2,
            "reps": "10 each",
            "notes": "Forward and backward"
          }
        ]
      },
      "blocks": [
        {
          "title": "Main Workout",
          "items": [
            {
              "type": "exercise",
              "name": "Bench Press",
              "sets": 4,
              "reps": "8-10",
              "notes": "Full range of motion"
            },
            {
              "type": "superset",
              "items": [
                {
                  "name": "Pull-ups",
                  "sets": 3,
                  "reps": "8-12",
                  "notes": "Assisted if needed"
                },
                {
                  "name": "Dips",
                  "sets": 3,
                  "reps": "10-15",
                  "notes": "Bodyweight"
                }
              ]
            }
          ]
        }
      ]
    },
    "tue": null,
    "wed": {
      "title": "Leg Day",
      "kcal": "600",
      "coach_note": "",
      "warmup": {
        "duration_min": "5",
        "items": []
      },
      "blocks": [
        {
          "title": "Workout Block",
          "items": [
            {
              "type": "exercise",
              "name": "Squats",
              "sets": 5,
              "reps": "8",
              "notes": ""
            }
          ]
        }
      ]
    },
    "thu": null,
    "fri": null,
    "sat": null,
    "sun": null
  }
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Active workout program not found"
}
```

---

### POST /coach/students/{student_user_id}/workout-programs

#### New Format (Structured Object)

**Request:**
```json
{
  "week": {
    "mon": {
      "title": "Upper Body Power",
      "kcal": "500",
      "coach_note": "Focus on form",
      "warmup": {
        "duration_min": "10",
        "items": [
          {
            "type": "exercise",
            "name": "Arm Circles",
            "sets": 2,
            "reps": "10 each",
            "notes": ""
          }
        ]
      },
      "blocks": [
        {
          "title": "Main Workout",
          "items": [
            {
              "type": "exercise",
              "name": "Bench Press",
              "sets": 4,
              "reps": "8-10",
              "notes": "Full ROM"
            },
            {
              "type": "superset",
              "items": [
                {
                  "name": "Pull-ups",
                  "sets": 3,
                  "reps": "8-12",
                  "notes": "Assisted"
                },
                {
                  "name": "Dips",
                  "sets": 3,
                  "reps": "10-15",
                  "notes": ""
                }
              ]
            }
          ]
        }
      ]
    },
    "wed": {
      "title": "Leg Day",
      "kcal": "",
      "coach_note": "",
      "warmup": {
        "duration_min": "",
        "items": []
      },
      "blocks": [
        {
          "title": "Workout Block",
          "items": [
            {
              "type": "exercise",
              "name": "Squats",
              "sets": 5,
              "reps": "8",
              "notes": ""
            }
          ]
        }
      ]
    }
  }
}
```

#### Old Format (Array - Still Supported)

**Request:**
```json
{
  "week": {
    "mon": [
      {
        "name": "Bench Press",
        "sets": 4,
        "reps": "8-10",
        "notes": "Full ROM"
      },
      {
        "name": "Pull-ups",
        "sets": 3,
        "reps": "8-12",
        "notes": ""
      }
    ],
    "wed": [
      {
        "name": "Squats",
        "sets": 5,
        "reps": "8",
        "notes": ""
      }
    ]
  }
}
```

**Response (200 OK):**
```json
{
  "ok": true,
  "program_id": 1
}
```

---

## Backward Compatibility

### Old Programs (day_payload = NULL)
- If `day_payload` is NULL or missing, the endpoint builds a minimal structure from `workout_exercises`:
  - `title`: Program title (or empty string)
  - `kcal`: Empty string
  - `coach_note`: Empty string
  - `warmup`: Empty
  - `blocks`: Single block with title "Workout Block" containing all exercises as `type: "exercise"`

### New Programs (day_payload populated)
- Full structured data is returned as stored
- Exercises are still flattened into `workout_exercises` table for compatibility

---

## Implementation Details

### Helper Functions

1. **`fetch_active_program_with_payload(client_user_id, db)`**
   - Fetches active program with days and exercises
   - Includes `day_payload` JSONB column
   - Returns program dict with days list

2. **`build_day_payload_from_flat_exercises(exercises, program_title)`**
   - Converts flat exercise array to structured day payload
   - Used for backward compatibility

3. **`build_week_response(program, days)`**
   - Builds week response structure
   - Handles both JSONB (dict) and string JSON parsing
   - Returns `{mon: payloadOrNull, tue: ..., ...}`

4. **`_flatten_day_to_exercises(day_data)`**
   - Flattens structured day payload to exercise list
   - Handles warmup items, block items, and supersets
   - Used when saving new format to populate `workout_exercises` table

### Data Flow

**Saving (Coach):**
1. Accepts either old format (array) or new format (object)
2. If new format: saves `day_payload` as JSONB + flattens to `workout_exercises`
3. If old format: saves exercises only (day_payload = NULL)

**Reading (Client):**
1. Fetches program with days and exercises
2. For each day:
   - If `day_payload` exists: use it directly
   - If `day_payload` is NULL: build from `workout_exercises` (backward compatibility)
3. Returns structured week response

---

## Testing

### Test New Endpoint
```bash
# Get active workout for client
curl -X GET "http://localhost:8000/client/workouts/active" \
  -H "Authorization: Bearer <client_token>"
```

### Test Coach Save (New Format)
```bash
curl -X POST "http://localhost:8000/coach/students/36/workout-programs" \
  -H "Authorization: Bearer <coach_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "week": {
      "mon": {
        "title": "Upper Body",
        "kcal": "500",
        "coach_note": "Focus on form",
        "warmup": {"duration_min": "10", "items": []},
        "blocks": [{
          "title": "Main",
          "items": [
            {"type": "exercise", "name": "Bench Press", "sets": 4, "reps": "8-10", "notes": ""},
            {"type": "superset", "items": [
              {"name": "Pull-ups", "sets": 3, "reps": "8-12", "notes": ""},
              {"name": "Dips", "sets": 3, "reps": "10-15", "notes": ""}
            ]}
          ]
        }]
      }
    }
  }'
```

### Test Coach Save (Old Format - Still Works)
```bash
curl -X POST "http://localhost:8000/coach/students/36/workout-programs" \
  -H "Authorization: Bearer <coach_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "week": {
      "mon": [
        {"name": "Bench Press", "sets": 4, "reps": "8-10", "notes": ""},
        {"name": "Pull-ups", "sets": 3, "reps": "8-12", "notes": ""}
      ]
    }
  }'
```

---

## Notes

- All endpoints use `RealDictCursor` for consistent dict-based responses
- Transaction safety: coach save endpoint uses try/except with rollback
- Empty days return `null` in week response (consistent behavior)
- Superset notes are prefixed with `[SUPERSET]` when flattened to `workout_exercises`
- Migration is idempotent (uses `IF NOT EXISTS`)

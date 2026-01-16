# Workout Program Assign Flow - Implementation Summary

## Overview
Changed the workflow so that saving a workout program from admin creates a **draft** program (not active). The program only becomes active when the coach explicitly assigns it via the new "Assign Program" endpoint.

## Changes Made

### 1. Updated Save Endpoint (Draft Creation)
**File**: `app/api/coach/routes.py`  
**Endpoint**: `POST /coach/students/{student_user_id}/workout-programs`

**Changes**:
- ✅ Removed auto-deactivation of existing active programs
- ✅ Changed `is_active=TRUE` to `is_active=FALSE` (creates draft)
- ✅ Program is saved but NOT activated automatically

**Before**:
```python
# Deactivated existing programs
cur.execute("UPDATE workout_programs SET is_active=FALSE WHERE ...")
# Created as active
cur.execute("INSERT ... VALUES (..., TRUE)")
```

**After**:
```python
# Creates draft (is_active=FALSE)
cur.execute("INSERT ... VALUES (..., FALSE)")
# No deactivation - existing active program stays active
```

### 2. New Assign Endpoint
**File**: `app/api/coach/routes.py`  
**Endpoint**: `POST /coach/students/{student_user_id}/workout-programs/{program_id}/assign`

**Purpose**: Activate a draft program (makes it visible to client)

**Auth**: Requires `coach` role

**Validation**:
- Verifies student is assigned to this coach
- Verifies program exists and belongs to this coach/student

**Transaction**:
1. Deactivates all active programs for the student
2. Activates the specified program

**Response**:
```json
{
  "ok": true,
  "active_program_id": 123
}
```

**Error Responses**:
- `403`: Student not assigned to this coach
- `404`: Program not found or permission denied
- `500`: Database error

### 3. Client Endpoint (Already Correct)
**File**: `app/api/client/workouts.py`  
**Endpoint**: `GET /client/workouts/active`

**Status**: ✅ Already returns 404 when no active program exists

The endpoint queries:
```sql
WHERE client_user_id = %s AND is_active = TRUE
```

If no program matches, it returns:
```json
{
  "detail": "Active workout program not found"
}
```

---

## Workflow

### Before (Old Flow)
1. Coach saves program → **Immediately active** → Client sees it
2. No way to create drafts

### After (New Flow)
1. Coach saves program → **Created as draft** (`is_active=false`) → Client does NOT see it
2. Coach clicks "Assign Program" → Calls assign endpoint → Program becomes active → Client sees it

---

## API Usage Examples

### 1. Save Draft Program
```bash
POST /coach/students/36/workout-programs
Authorization: Bearer <coach_token>
Content-Type: application/json

{
  "week": {
    "mon": {
      "title": "Upper Body",
      "kcal": "500",
      "coach_note": "Focus on form",
      "warmup": {"duration_min": "10", "items": []},
      "blocks": [{
        "title": "Main",
        "items": [
          {"type": "exercise", "name": "Bench Press", "sets": 4, "reps": "8-10", "notes": ""}
        ]
      }]
    }
  }
}

# Response:
{
  "ok": true,
  "program_id": 123  # Created as draft (is_active=false)
}
```

### 2. Assign Program (Make Active)
```bash
POST /coach/students/36/workout-programs/123/assign
Authorization: Bearer <coach_token>

# Response:
{
  "ok": true,
  "active_program_id": 123
}
```

### 3. Client Views Active Program
```bash
GET /client/workouts/active
Authorization: Bearer <client_token>

# Response (if program 123 is active):
{
  "program": {
    "id": 123,
    "title": "Upper Body",
    ...
  },
  "week": { ... }
}

# Response (if no active program):
{
  "detail": "Active workout program not found"
}
```

---

## Database State Examples

### Scenario 1: Draft Program
```sql
-- Coach saves program
INSERT INTO workout_programs (client_user_id, coach_user_id, title, is_active)
VALUES (36, 5, 'Upper Body', FALSE);

-- Result: program exists but is_active=false
-- Client GET /client/workouts/active → 404
```

### Scenario 2: Assign Draft Program
```sql
-- Before assign:
-- Program 123: is_active=false
-- Program 100: is_active=true (old active program)

-- After POST /assign (program_id=123):
UPDATE workout_programs SET is_active=FALSE WHERE client_user_id=36 AND is_active=TRUE;
UPDATE workout_programs SET is_active=TRUE WHERE id=123;

-- Result:
-- Program 100: is_active=false (deactivated)
-- Program 123: is_active=true (now active)
-- Client GET /client/workouts/active → Returns program 123
```

---

## Testing Checklist

- [x] Save program creates draft (is_active=false)
- [x] Save program does NOT deactivate existing active program
- [x] Assign endpoint validates coach ownership
- [x] Assign endpoint deactivates old active program
- [x] Assign endpoint activates specified program
- [x] Client endpoint returns 404 when no active program
- [x] Client endpoint returns program when active program exists
- [x] Transaction safety (rollback on error)

---

## Files Modified

1. **app/api/coach/routes.py**
   - Updated `save_workout_program()`: Creates draft instead of active
   - Added `assign_workout_program()`: New endpoint to activate program

2. **app/api/client/workouts.py**
   - ✅ No changes needed (already checks is_active=TRUE)

---

## Migration Notes

**No database migration required** - The `is_active` column already exists in `workout_programs` table.

Existing programs with `is_active=true` will remain active until explicitly deactivated via the assign endpoint.

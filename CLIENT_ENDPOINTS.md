# Client-Facing Endpoints Documentation

## Overview
This document describes the client-facing endpoints for coach discovery and checkout functionality.

## Authentication
All endpoints require Bearer token authentication:
```
Authorization: Bearer <token>
```

## Endpoints

### GET /client/coaches
Get list of active coaches with optional search and pagination.

**Query Parameters:**
- `q` (optional): Search query (searches in full_name, bio, specialties)
- `limit` (optional, default: 20, max: 100): Maximum number of results
- `offset` (optional, default: 0): Number of results to skip

**Response:**
```json
{
  "coaches": [
    {
      "user_id": 123,
      "full_name": "John Doe",
      "bio": "Fitness coach with 10 years experience",
      "photo_url": "https://...",
      "price_per_month": 500,
      "rating": 4.8,
      "rating_count": 45,
      "specialties": ["Strength", "Cardio"],
      "instagram": "@johndoe",
      "is_active": true
    }
  ],
  "total": 50,
  "limit": 20,
  "offset": 0
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/client/coaches?q=fitness&limit=5&offset=0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### GET /client/coaches/{coach_user_id}
Get detailed coach profile including active packages.

**Path Parameters:**
- `coach_user_id` (required): The user ID of the coach

**Response:**
```json
{
  "coach": {
    "user_id": 123,
    "full_name": "John Doe",
    "bio": "Fitness coach...",
    "photo_url": "https://...",
    "price_per_month": 500,
    "rating": 4.8,
    "rating_count": 45,
    "specialties": ["Strength", "Cardio"],
    "instagram": "@johndoe",
    "is_active": true
  },
  "packages": [
    {
      "id": 456,
      "coach_user_id": 123,
      "name": "Monthly Plan",
      "description": "Full access for 30 days",
      "duration_days": 30,
      "price": 500,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ]
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/client/coaches/123" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### POST /client/checkout
Create a subscription from a coach package purchase.

**Request Body:**
```json
{
  "coach_package_id": 456
}
```

**Response:**
```json
{
  "ok": true,
  "subscription": {
    "id": 789,
    "client_user_id": 100,
    "coach_user_id": 123,
    "plan_name": "Monthly Plan",
    "status": "active",
    "started_at": "2024-01-15T10:00:00",
    "ends_at": "2024-02-14T10:00:00"
  },
  "coach_user_id": 123,
  "package": {
    "id": 456,
    "name": "Monthly Plan",
    "description": "Full access for 30 days",
    "duration_days": 30,
    "price": 500
  }
}
```

**Behavior:**
- Validates package exists and is active
- Creates subscription with `status='active'`
- Calculates `ends_at` from `started_at + duration_days`
- Updates `clients.assigned_coach_id` to assign the coach
- If client has existing active subscription with same coach: deactivates old one
- If client has existing active subscription with different coach: creates new subscription (reassigns coach)

**Example:**
```bash
curl -X POST "http://localhost:8000/client/checkout" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"coach_package_id": 456}'
```

**Error Responses:**
- `404`: Package not found or inactive
- `403`: User is not a client
- `500`: Internal server error

---

## Database Schema

### subscriptions table
- `id`: Primary key
- `client_user_id`: Foreign key to users.id
- `coach_user_id`: Foreign key to users.id
- `package_id`: Foreign key to coach_packages.id (optional, if column exists)
- `plan_name`: Name of the plan/package
- `status`: 'active', 'inactive', 'pending', 'expired', etc.
- `started_at`: Timestamp when subscription started
- `ends_at`: Timestamp when subscription ends
- `created_at`: Timestamp when subscription was created
- `subscription_ref`: External subscription reference (optional)

### clients table
- `user_id`: Primary key, foreign key to users.id
- `assigned_coach_id`: Foreign key to users.id (nullable)

### coach_packages table
- `id`: Primary key
- `coach_user_id`: Foreign key to users.id
- `name`: Package name
- `description`: Package description
- `duration_days`: Number of days the package lasts
- `price`: Price in TL (integer)
- `is_active`: Boolean flag

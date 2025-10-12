# API Specification v1.0

## Overview

This document defines the RESTful API endpoints for the Schedule Engine production system.

**Base URL:** `https://api.scheduleengine.com/api/v1`  
**Authentication:** Bearer JWT tokens  
**Content-Type:** `application/json`

---

## Authentication Endpoints

### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "organization_name": "University Name",
  "organization_domain": "university.edu"
}
```

**Response (201 Created):**
```json
{
  "user_id": 1,
  "email": "user@example.com",
  "organization_id": 1,
  "message": "Registration successful. Please verify your email."
}
```

### POST /auth/login
Login to get access token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "admin",
    "organization_id": 1
  }
}
```

### POST /auth/refresh
Refresh access token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### POST /auth/logout
Logout and invalidate tokens.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "message": "Logged out successfully"
}
```

---

## Course Endpoints

### GET /courses
Get list of courses.

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 50, max: 100)
- `department_id` (int, optional)
- `semester` (int, optional)
- `is_active` (bool, optional)
- `search` (string, optional) - search in code/title

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "course_code": "CS101",
      "course_title": "Introduction to Computer Science",
      "credits": 3,
      "lecture_hours": 3,
      "tutorial_hours": 1,
      "practical_hours": 2,
      "semester": 1,
      "department": {
        "id": 1,
        "code": "CS",
        "name": "Computer Science"
      },
      "required_room_features": ["projector", "computers"],
      "is_active": true
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 150,
    "pages": 3
  }
}
```

### POST /courses
Create a new course.

**Request Body:**
```json
{
  "course_code": "CS101",
  "course_title": "Introduction to Computer Science",
  "credits": 3,
  "lecture_hours": 3,
  "tutorial_hours": 1,
  "practical_hours": 2,
  "semester": 1,
  "department_id": 1,
  "required_room_features": ["projector", "computers"],
  "description": "Fundamentals of programming..."
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "course_code": "CS101",
  "course_title": "Introduction to Computer Science",
  "created_at": "2025-10-11T19:00:00Z"
}
```

### GET /courses/{id}
Get course details.

**Response (200 OK):**
```json
{
  "id": 1,
  "course_code": "CS101",
  "course_title": "Introduction to Computer Science",
  "credits": 3,
  "lecture_hours": 3,
  "tutorial_hours": 1,
  "practical_hours": 2,
  "semester": 1,
  "department": {
    "id": 1,
    "code": "CS",
    "name": "Computer Science"
  },
  "instructors": [
    {
      "id": 1,
      "instructor_code": "INST001",
      "name": "Dr. John Smith",
      "is_primary": true
    }
  ],
  "groups": [
    {
      "id": 1,
      "group_code": "CS-Y1-A",
      "group_name": "CS Year 1 Group A"
    }
  ],
  "required_room_features": ["projector", "computers"],
  "description": "Fundamentals of programming...",
  "is_active": true,
  "created_at": "2025-10-11T19:00:00Z",
  "updated_at": "2025-10-11T19:00:00Z"
}
```

### PUT /courses/{id}
Update a course.

**Request Body:** (same as POST, all fields optional)

**Response (200 OK):**
```json
{
  "id": 1,
  "message": "Course updated successfully"
}
```

### DELETE /courses/{id}
Delete a course.

**Response (200 OK):**
```json
{
  "message": "Course deleted successfully"
}
```

### POST /courses/import
Bulk import courses from CSV/JSON.

**Request (multipart/form-data):**
```
file: courses.csv
format: csv
```

**Response (200 OK):**
```json
{
  "imported": 50,
  "failed": 2,
  "errors": [
    {
      "row": 5,
      "error": "Invalid course code format"
    }
  ]
}
```

---

## Instructor Endpoints

### GET /instructors
Get list of instructors.

**Query Parameters:**
- `page`, `per_page`, `department_id`, `is_active`, `search`

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "instructor_code": "INST001",
      "name": "Dr. John Smith",
      "email": "john.smith@university.edu",
      "department": {
        "id": 1,
        "code": "CS",
        "name": "Computer Science"
      },
      "max_weekly_hours": 40,
      "is_active": true
    }
  ],
  "pagination": {...}
}
```

### POST /instructors
Create a new instructor.

**Request Body:**
```json
{
  "instructor_code": "INST001",
  "name": "Dr. John Smith",
  "email": "john.smith@university.edu",
  "phone": "+1-555-0100",
  "department_id": 1,
  "max_weekly_hours": 40,
  "availability": {
    "monday": ["08:00-18:00"],
    "tuesday": ["08:00-18:00"],
    "wednesday": ["08:00-18:00"],
    "thursday": ["08:00-18:00"],
    "friday": ["08:00-18:00"]
  },
  "preferences": {
    "preferred_rooms": ["LAB1", "LAB2"],
    "preferred_times": ["morning"]
  }
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "instructor_code": "INST001",
  "name": "Dr. John Smith"
}
```

### GET /instructors/{id}
Get instructor details with courses and availability.

### PUT /instructors/{id}
Update instructor.

### DELETE /instructors/{id}
Delete instructor.

---

## Room Endpoints

### GET /rooms
Get list of rooms.

**Query Parameters:**
- `page`, `per_page`, `building`, `room_type`, `min_capacity`, `is_active`

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "room_code": "LAB1",
      "room_name": "Computer Lab 1",
      "building": "Engineering Building",
      "floor": 3,
      "capacity": 30,
      "room_type": "lab",
      "features": ["computers", "projector", "whiteboard"],
      "is_active": true
    }
  ],
  "pagination": {...}
}
```

### POST /rooms
Create a new room.

**Request Body:**
```json
{
  "room_code": "LAB1",
  "room_name": "Computer Lab 1",
  "building": "Engineering Building",
  "floor": 3,
  "capacity": 30,
  "room_type": "lab",
  "features": ["computers", "projector", "whiteboard"],
  "availability": {
    "monday": ["08:00-18:00"],
    "tuesday": ["08:00-18:00"],
    "wednesday": ["08:00-18:00"],
    "thursday": ["08:00-18:00"],
    "friday": ["08:00-18:00"]
  }
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "room_code": "LAB1",
  "room_name": "Computer Lab 1"
}
```

### GET /rooms/{id}
Get room details.

### PUT /rooms/{id}
Update room.

### DELETE /rooms/{id}
Delete room.

### GET /rooms/availability
Check room availability for scheduling.

**Query Parameters:**
- `day` (string, required)
- `time_slot` (string, required)
- `min_capacity` (int, optional)
- `required_features` (array, optional)

**Response (200 OK):**
```json
{
  "available_rooms": [
    {
      "id": 1,
      "room_code": "LAB1",
      "room_name": "Computer Lab 1",
      "capacity": 30,
      "features": ["computers", "projector"]
    }
  ]
}
```

---

## Group Endpoints

### GET /groups
Get list of student groups.

**Query Parameters:**
- `page`, `per_page`, `program`, `semester`, `is_active`

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "group_code": "CS-Y1-A",
      "group_name": "CS Year 1 Group A",
      "program": "Computer Science",
      "semester": 1,
      "year": 2025,
      "student_count": 45,
      "is_active": true
    }
  ],
  "pagination": {...}
}
```

### POST /groups
Create a new group.

**Request Body:**
```json
{
  "group_code": "CS-Y1-A",
  "group_name": "CS Year 1 Group A",
  "program": "Computer Science",
  "semester": 1,
  "year": 2025,
  "student_count": 45
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "group_code": "CS-Y1-A"
}
```

### GET /groups/{id}
Get group details with enrolled courses.

### PUT /groups/{id}
Update group.

### DELETE /groups/{id}
Delete group.

---

## Schedule Endpoints

### POST /schedules/generate
Start a new schedule generation run.

**Request Body:**
```json
{
  "name": "Fall 2025 Schedule",
  "academic_year": "2025-2026",
  "semester": 1,
  "algorithm_config": {
    "population_size": 100,
    "generations": 100,
    "crossover_probability": 0.7,
    "mutation_probability": 0.15,
    "constraint_weights": {
      "hard_constraint_weight": 100,
      "soft_constraint_weight": 1
    }
  }
}
```

**Response (202 Accepted):**
```json
{
  "schedule_run_id": 1,
  "status": "queued",
  "message": "Schedule generation queued successfully",
  "estimated_time_minutes": 5
}
```

### GET /schedules/{run_id}
Get schedule run details and status.

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Fall 2025 Schedule",
  "academic_year": "2025-2026",
  "semester": 1,
  "status": "completed",
  "progress_percentage": 100,
  "fitness_score": 0.95,
  "hard_violations": 0,
  "soft_violations": 5,
  "runtime_seconds": 245,
  "is_published": false,
  "started_at": "2025-10-11T19:00:00Z",
  "completed_at": "2025-10-11T19:04:05Z",
  "created_by": {
    "id": 1,
    "name": "John Doe"
  }
}
```

### GET /schedules/{run_id}/progress
Get real-time progress of schedule generation (WebSocket or polling).

**Response (200 OK):**
```json
{
  "schedule_run_id": 1,
  "status": "running",
  "progress_percentage": 45,
  "current_generation": 45,
  "total_generations": 100,
  "best_fitness": 0.85,
  "hard_violations": 2,
  "soft_violations": 12,
  "estimated_time_remaining_seconds": 135
}
```

### GET /schedules/{run_id}/sessions
Get all scheduled sessions for a run.

**Query Parameters:**
- `day` (string, optional) - filter by day
- `instructor_id` (int, optional)
- `room_id` (int, optional)
- `group_id` (int, optional)
- `course_id` (int, optional)

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "course": {
        "id": 1,
        "course_code": "CS101",
        "course_title": "Introduction to Computer Science"
      },
      "instructor": {
        "id": 1,
        "name": "Dr. John Smith"
      },
      "room": {
        "id": 1,
        "room_code": "LAB1",
        "room_name": "Computer Lab 1"
      },
      "group": {
        "id": 1,
        "group_code": "CS-Y1-A"
      },
      "day_of_week": "monday",
      "time_slot": "08:00-09:30",
      "start_time": "08:00",
      "end_time": "09:30",
      "session_type": "lecture",
      "duration_minutes": 90
    }
  ],
  "total": 250
}
```

### PUT /schedules/{run_id}/publish
Publish a schedule to make it active.

**Response (200 OK):**
```json
{
  "message": "Schedule published successfully",
  "published_at": "2025-10-11T19:05:00Z"
}
```

### DELETE /schedules/{run_id}
Delete a schedule run.

**Response (200 OK):**
```json
{
  "message": "Schedule deleted successfully"
}
```

### GET /schedules
List all schedule runs.

**Query Parameters:**
- `page`, `per_page`, `status`, `academic_year`, `semester`

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "name": "Fall 2025 Schedule",
      "status": "completed",
      "fitness_score": 0.95,
      "created_at": "2025-10-11T19:00:00Z"
    }
  ],
  "pagination": {...}
}
```

---

## Report Endpoints

### GET /reports/utilization
Get room utilization report.

**Query Parameters:**
- `schedule_run_id` (int, required)
- `room_id` (int, optional)

**Response (200 OK):**
```json
{
  "schedule_run_id": 1,
  "overall_utilization": 75.5,
  "rooms": [
    {
      "room_code": "LAB1",
      "room_name": "Computer Lab 1",
      "total_slots": 25,
      "occupied_slots": 20,
      "utilization_percentage": 80.0,
      "sessions": 20
    }
  ]
}
```

### GET /reports/violations
Get constraint violations report.

**Query Parameters:**
- `schedule_run_id` (int, required)

**Response (200 OK):**
```json
{
  "schedule_run_id": 1,
  "total_hard_violations": 0,
  "total_soft_violations": 5,
  "violations": [
    {
      "type": "soft",
      "constraint": "instructor_preference",
      "description": "Instructor assigned to non-preferred time",
      "affected_sessions": [1, 5, 12],
      "count": 3
    }
  ]
}
```

### GET /reports/workload
Get instructor workload report.

**Query Parameters:**
- `schedule_run_id` (int, required)
- `instructor_id` (int, optional)

**Response (200 OK):**
```json
{
  "schedule_run_id": 1,
  "instructors": [
    {
      "id": 1,
      "name": "Dr. John Smith",
      "total_hours": 18,
      "max_hours": 40,
      "utilization_percentage": 45.0,
      "courses": [
        {
          "course_code": "CS101",
          "sessions": 6,
          "hours": 9
        }
      ]
    }
  ]
}
```

### POST /reports/export
Export schedule in various formats.

**Request Body:**
```json
{
  "schedule_run_id": 1,
  "format": "pdf",
  "view_by": "instructor",
  "include_details": true
}
```

**Response (200 OK):**
```json
{
  "download_url": "https://cdn.scheduleengine.com/exports/schedule_1_20251011.pdf",
  "expires_at": "2025-10-12T19:00:00Z"
}
```

---

## WebSocket Endpoints

### WS /ws/schedules/{run_id}/progress
Real-time schedule generation progress updates.

**Connection:**
```javascript
const ws = new WebSocket('wss://api.scheduleengine.com/ws/schedules/1/progress?token=jwt_token');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Progress:', data);
};
```

**Message Format:**
```json
{
  "type": "progress",
  "schedule_run_id": 1,
  "generation": 45,
  "fitness": 0.85,
  "hard_violations": 2,
  "soft_violations": 12,
  "progress_percentage": 45
}
```

### WS /ws/notifications
User notifications stream.

**Message Format:**
```json
{
  "type": "notification",
  "notification_id": 1,
  "title": "Schedule Generation Complete",
  "message": "Fall 2025 Schedule has been generated successfully",
  "data": {
    "schedule_run_id": 1
  },
  "timestamp": "2025-10-11T19:04:05Z"
}
```

---

## Error Responses

All errors follow this format:

**400 Bad Request:**
```json
{
  "error": "validation_error",
  "message": "Invalid input data",
  "details": {
    "course_code": "This field is required"
  }
}
```

**401 Unauthorized:**
```json
{
  "error": "unauthorized",
  "message": "Invalid or expired token"
}
```

**403 Forbidden:**
```json
{
  "error": "forbidden",
  "message": "You don't have permission to perform this action"
}
```

**404 Not Found:**
```json
{
  "error": "not_found",
  "message": "Resource not found"
}
```

**429 Too Many Requests:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later",
  "retry_after": 60
}
```

**500 Internal Server Error:**
```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred",
  "request_id": "req_abc123"
}
```

---

## Rate Limiting

- **Authentication endpoints:** 5 requests per minute per IP
- **Read endpoints:** 100 requests per minute per user
- **Write endpoints:** 20 requests per minute per user
- **Schedule generation:** 5 concurrent runs per organization

Headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1633974000
```

---

## Pagination

All list endpoints support pagination:

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 50, max: 100)

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 250,
    "pages": 5,
    "has_next": true,
    "has_prev": false,
    "next_page": 2,
    "prev_page": null
  }
}
```

---

## Authentication

All API requests (except /auth endpoints) require authentication:

**Header:**
```
Authorization: Bearer {access_token}
```

**Token Expiry:**
- Access token: 1 hour
- Refresh token: 7 days

---

**API Version:** 1.0  
**Last Updated:** October 2025  
**OpenAPI/Swagger:** https://api.scheduleengine.com/docs

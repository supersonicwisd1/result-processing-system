# Result Processor API Endpoints

This document provides a detailed overview of the backend API endpoints, including a description, example input, output, and any additional notes for each endpoint.

## Authentication Endpoints

### 1. **Register User**

- **Endpoint:** `POST /api/v1/auth/register`
- **Description:** Registers a new user in the system.
- **Role Access:** Open to all (no authentication required).
- **Request Body (JSON):**

| Field       | Type   | Required | Description                          |
|-------------|--------|----------|--------------------------------------|
| username    | string | Yes      | The username of the new user.        |
| email       | string | Yes      | The email address of the new user.   |
| department  | string | Yes      | The department of the new user.        |
| password    | string | Yes      | The password of the new user.        |
| role        | string | Yes      | Role of the user (admin, hod, lecturer, etc.). |

- **Example Input:**
```json
{
  "username": "john_doe",
  "email": "john.doe@example.com",
  "password": "securepassword123",
  "department": "Computer Science",
  "role": "lecturer"
}
```

- **Response:**

| Status Code | Message                        |
|-------------|--------------------------------|
| 201         | User registered successfully   |
| 400         | Validation error               |

- **Example Output:**
```json
{
  "message": "User registered successfully"
}
```

---

### 2. **Login User**

- **Endpoint:** `POST /api/v1/auth/login`
- **Description:** Authenticates a user and returns a JWT token.
- **Role Access:** Open to all (no authentication required).
- **Request Body (JSON):**

| Field       | Type   | Required                            | Description                         |
|-------------|--------|-------------------------------------|-------------------------------------|
| username    | string | Yes (Either email or username)      | The username of the user.           |
| email       | string | Yes (Either email or username)      | The email address of the user.       |
| password    | string | Yes                                 | The password of the user.           |

- **Example Input:**
```json
{
  "username": "john_doe",
  "password": "securepassword123"
}
```

## **OR**

```json
{
  "email": "john.doe@example.com",
  "password": "securepassword123"
}
```

- **Response:**

| Status Code | Message                        |
|-------------|--------------------------------|
| 200         | Login successful               |
| 401         | Invalid credentials            |

- **Example Output:**
```json
{
  "access_token": "jwt_token_here",
  "role": "lecturer"
}
```

---

### 3. **Forgot Password**

- **Endpoint:** `POST /api/v1/auth/forgot-password`
- **Description:** Sends a password reset email with an otp code.
- **Role Access:** Open to all (no authentication required).
- **Request Body (JSON):**

| Field    | Type   | Required | Description                            |
|----------|--------|----------|----------------------------------------|
| email    | string | Yes      | The email address of the user.         |

- **Example Input:**
```json
{
  "email": "john.doe@example.com"
}
```

- **Response:**

| Status Code | Message                         |
|-------------|---------------------------------|
| 200         | Password reset email sent       |
| 400         | Email is required               |
| 404         | User with email not found       |

- **Example Output:**
```json
{
  "message": "Password reset email sent"
}
```

---

### 4. **Reset Password**

- **Endpoint:** `POST /api/v1/auth/reset-password`
- **Description:** Resets the user password using a token.
- **Role Access:** Open to all (no authentication required).
- **Request Body (JSON):**

| Field        | Type   | Required | Description                           |
|--------------|--------|----------|---------------------------------------|
| email        | string | Yes      | The account email address.            |
| otp          | string | Yes      | The password reset token from email.  |
| new_password | string | Yes      | The new password.                    |

- **Example Input:**
```json
{
  "email": "john.doe@example.com",
  "otp": "123456",
  "new_password": "newpassword123"
}
```

- **Response:**

| Status Code | Message                     |
|-------------|-----------------------------|
| 200         | Password reset successful   |
| 400         | Invalid or expired code     |
| 400         | Code and new password required |

- **Example Output:**
```json
{
  "message": "Password reset successfully"
}
```

### 5. **Get Current User Information**

- **Endpoint:** `GET /api/v1/auth/me`
- **Description:** Retrieves the current user's information (e.g., username, email, role).
- **Role Access:** Any authenticated user.
- **Response:**

| Status Code | Message                           |
|-------------|-----------------------------------|
| 200         | User information retrieved        |
| 404         | User not found                    |

- **Example Output:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john.doe@example.com",
  "role": "lecturer",
  "department": "Computer Science"
}
```

---

### 6. **Update Username**

- **Endpoint:** `PATCH /api/v1/auth/update-username`
- **Description:** Updates the current user's username.
- **Role Access:** Any authenticated user.
- **Request Body (JSON):**

| Field         | Type   | Required | Description                           |
|---------------|--------|----------|---------------------------------------|
| new_username  | string | Yes      | The new username for the user.        |

- **Example Input:**
```json
{
  "new_username": "john_new_doe"
}
```

- **Response:**

| Status Code | Message                         |
|-------------|---------------------------------|
| 200         | Username updated successfully   |
| 400         | Username already taken          |

- **Example Output:**
```json
{
  "message": "Username updated successfully"
}
```

---

### 7. **Update Email**

- **Endpoint:** `PATCH /api/v1/auth/update-email`
- **Description:** Updates the current user's email.
- **Role Access:** Any authenticated user.
- **Request Body (JSON):**

| Field       | Type   | Required | Description                           |
|-------------|--------|----------|---------------------------------------|
| new_email   | string | Yes      | The new email for the user.           |

- **Example Input:**
```json
{
  "new_email": "john_new_doe@example.com"
}
```

- **Response:**

| Status Code | Message                         |
|-------------|---------------------------------|
| 200         | Email updated successfully      |
| 400         | Email already taken             |

- **Example Output:**
```json
{
  "message": "Email updated successfully"
}
```

---

### 8. **Change Password**

- **Endpoint:** `POST /api/v1/auth/change-password`
- **Description:** Changes the current user's password.
- **Role Access:** Any authenticated user.
- **Request Body (JSON):**

| Field         | Type   | Required | Description                           |
|---------------|--------|----------|---------------------------------------|
| old_password  | string | Yes      | The current password of the user.     |
| new_password  | string | Yes      | The new password for the user.        |

- **Example Input:**
```json
{
  "old_password": "old_password123",
  "new_password": "new_password123"
}
```

- **Response:**

| Status Code | Message                         |
|-------------|---------------------------------|
| 200         | Password changed successfully   |
| 400         | Incorrect old password          |
| 400         | Passwords do not match          |

- **Example Output:**
```json
{
  "message": "Password changed successfully"
}
```
---

## Results Endpoints

### 1. **Submit Results**

- **Endpoint:** `POST /api/v1/results/submit`
- **Description:** Submits results for a course, including scores for students.
- **Role Access:** Admin, HOD, Lecturer (the one who teaches the course).
- **Request Body (JSON):**

| Field            | Type   | Required | Description                         |
|------------------|--------|----------|-------------------------------------|
| course_code      | string | Yes      | The code for the course.            |
| course_title     | string | Yes      | The title of the course.            |
| course_unit      | int    | Yes      | The number of units for the course. |
| level            | string | Yes      | The academic level of the course.   |
| faculty          | string | Yes      | The faculty the course belongs to.  |
| department       | string | Yes      | The department offering the course. |
| semester_name    | string | Yes      | The name of the semester.           |
| session          | string | Yes      | The academic session.               |
| results          | array  | Yes      | List of student results with scores. |

- **Example Input:**
```json
{
  "course_code": "COS102",
  "course_title": "Computer Science 101",
  "course_unit": 3,
  "level": "100",
  "faculty": "Science",
  "department": "Computer Science",
  "semester_name": "First",
  "session": "2024/2025",
  "results": [
    {
      "registration_number": "2021-001",
      "student_name": "Alice Johnson",
      "ca_score": 30,
      "exam_score": 60,
      "total_score": 90,
      "grade": "A"
    },
    {
      "registration_number": "2021-002",
      "student_name": "Bob Smith",
      "ca_score": 25,
      "exam_score": 50,
      "total_score": 75,
      "grade": "B"
    }
  ]
}
```

- **Response:**

| Status Code | Message                        |
|-------------|--------------------------------|
| 200         | Results submitted successfully |
| 400         | Invalid data or missing fields |
| 409         | Results for this course and semester already exist |

- **Example Output:**
```json
{
  "message": "Results submitted successfully"
}
```

---

### 2. **Get All Results**

- **Endpoint:** `GET /api/v1/results/list`
- **Description:** Retrieves a list of all result metadata, with optional filters and pagination.
- **Role Access:** Admin, HOD, Lecturer (depends on affiliation).
- **Query Parameters:**

| Parameter       | Type    | Description                              |
|-----------------|---------|------------------------------------------|
| department      | string  | Filter by department (optional).         |
| course_code     | string  | Filter by course code (optional).        |
| semester        | string  | Filter by semester (optional).           |
| session         | string  | Filter by academic session (optional).   |
| page            | int     | Page number for pagination (default: 1). |
| per_page        | int     | Number of results per page (default: 10).|

- **Response:**

| Status Code | Message                           |
|-------------|-----------------------------------|
| 200         | Results retrieved successfully    |
| 400         | Invalid query parameters          |

- **Example Output:**
```json
{
  "results": [
    {
      "id": 1,
      "course_code": "COS102",
      "course_title": "Computer Science 101",
      "semester": "First",
      "uploaded_by": "john_doe",
      "upload_date": "2024-01-15T12:30:00",
      "department": "Computer Science",
      "faculty": "Science",
      "num_scores": 30
    }
  ],
  "total_results": 100,
  "current_page": 1,
  "total_pages": 10,
  "per_page": 10
}
```

---

### 3. **Get Results by Registration Number**

- **Endpoint:** `GET /api/v1/results/by-registration`
- **Description:** Retrieves the results for a specific student, filtered by registration number and optionally by session and semester.
- **Role Access:** Admin, HOD, Lecturer (depending on role and course taught).
- **Query Parameters:**

| Parameter          | Type    | Description                               |
|--------------------|---------|-------------------------------------------|
| registration_number | string  | The registration number of the student.   |
| session             | string  | Optional filter by academic session.      |

- **Response:**

| Status Code | Message                            |
|-------------|------------------------------------|
| 200         | Results retrieved successfully     |
| 404         | Student or results not found       |

- **Example Output:**
```json
{
  "student_name": "Alice Johnson",
  "registration_number": "2021-001",
  "session": "All Sessions",
  "total_credit_earned": 10,
  "total_grade_point": 35,
  "cgpa": 3.5,
  "results": [
    {
      "session": "2024/2025",
      "overall_credit_earned": 10,
      "overall_grade_point": 35,
      "results_by_semester": {
        "First": {
          "total_credit_earned": 5,
          "total_grade_point": 18,
          "courses": [
            {
              "course_code": "COS102",
              "course_title": "Computer Science 101",
              "grade": "A"
            }
          ]
        }
      }
    }
  ]
}
```

### 4. **Get Result by ID**

- **Endpoint:** `GET /api/v1/results/<int:result_id>`
- **Description:** Retrieves a result by its unique ID.
- **Role Access:** Admin, HOD, Lecturer (depending on course affiliation).
- **Response:**

| Status Code | Message                           |
|-------------|-----------------------------------|
| 200         | Result details retrieved         |
| 404         | Result not found                 |

- **Example Output:**
```json
{
  "id": 1,
  "course_code": "COS102",
  "course_title": "Computer Science 101",
  "semester": "First",
  "uploaded_by": "john_doe",
  "upload_date": "2024-01-15T12:30:00",
  "department": "Computer Science",
  "faculty": "Science",
  "scores": [
    {
      "student_name": "Alice Johnson",
      "registration_number": "2021-001",
      "ca_score": 30,
      "exam_score": 60,
      "total_score": 90,
      "grade": "A"
    }
  ]
}
```

---

### 5. **Update or Create Score for a Result**

- **Endpoint:** `PATCH /api/v1/results/<int:result_id>/update-score`
- **Description:** Updates or creates a score for a result, optionally adding a new student.
- **Role Access:** Admin, HOD, Lecturer (depending on course affiliation).
- **Request Body (JSON):**

| Field            | Type   | Required | Description                          |
|------------------|--------|----------|--------------------------------------|
| registration_number | string | Yes      | The student's registration number.   |
| ca_score         | float  | Yes      | Continuous assessment score.         |
| exam_score       | float  | Yes      | Exam score.                          |
| total_score      | float  | Yes      | Total score (calculated or entered). |
| grade            | string | Yes      | Grade (e.g., 'A', 'B', 'C').         |

- **Example Input:**
```json
{
  "registration_number": "2021-001",
  "ca_score": 30,
  "exam_score": 60,
  "total_score": 90,
  "grade": "A"
}
```

- **Response:**

| Status Code | Message                           |
|-------------|-----------------------------------|
| 200         | Score updated or created          |
| 404         | Result or student not found       |

- **Example Output:**
```json
{
  "message": "Score updated or created successfully"
}
```

---

### 6. **Update Result Metadata**

- **Endpoint:** `PATCH /api/v1/results/<int:result_id>/update-meta`
- **Description:** Updates the metadata for a specific result.
- **Role Access:** Admin, HOD, Lecturer (depending on course affiliation).
- **Request Body (JSON):**

| Field           | Type   | Required | Description                         |
|-----------------|--------|----------|-------------------------------------|
| course_code     | string | No       | The code of the course.             |
| course_title    | string | No       | The title of the course.            |
| course_unit     | int    | No       | The number of units for the course. |
| semester_name   | string | No       | The name of the semester.           |
| session         | string | No       | The academic session.               |

- **Example Input:**
```json
{
  "course_code": "COS202",
  "course_title": "Computer Science 202",
  "course_unit": 4,
  "semester_name": "Second",
  "session": "2025/2026"
}
```

- **Response:**

| Status Code | Message                           |
|-------------|-----------------------------------|
| 200         | Result metadata updated          |
| 404         | Result not found                 |

- **Example Output:**
```json
{
  "message": "Result metadata updated successfully"
}
```

---

### 7. **Search for Results**

- **Endpoint:** `GET /api/v1/results/search`
- **Description:** Searches for results based on various criteria such as course code, student name, and semester.
- **Role Access:** Admin, HOD, Lecturer.
- **Query Parameters:**

| Parameter        | Type   | Description                                |
|------------------|--------|--------------------------------------------|
| course_code      | string | Filter by course code.                    |
| student_name     | string | Filter by student name.                   |
| semester_name    | string | Filter by semester name.                  |
| session          | string | Filter by academic session.               |
| page             | int    | Page number for pagination.               |
| per_page         | int    | Number of results per page.               |

- **Response:**

| Status Code | Message                         |
|-------------|---------------------------------|
| 200         | Results retrieved successfully  |
| 400         | Invalid query parameters        |

- **Example Output:**
```json
{
  "search_results": [
    {
      "id": 1,
      "course_code": "COS102",
      "course_title": "COMPUTING PRACTICE",
      "semester": "2019/2020 SECOND",
      "department": "COMPUTER SCIENCE",
      "faculty": "PYSICAL SCIENCE",
      "upload_date": "2025-01-25T23:48:14.655142",
      "num_scores": 10
    }
  ],
  "total_results": 10,
  "current_page": 1,
  "total_pages": 1,
  "per_page": 10
}
```

---

### 12. **Delete Result**

- **Endpoint:** `DELETE /api/v1/results/delete/<int:result_id>`
- **Description:** Deletes a result by its ID, including associated scores.
- **Role Access:** Admin, HOD, Lecturer (if affiliated with the result).
- **Response:**

| Status Code | Message                        |
|-------------|--------------------------------|
| 200         | Result deleted successfully    |
| 404         | Result not found               |

- **Example Output:**
```json
{
  "message": "Result deleted successfully"
}
```

---

### 13. **Upload Results**

- **Endpoint:** `POST /api/v1/results/upload`
- **Description:** Uploads and processes a results file (e.g., CSV, XLSX, DOCX).
- **Role Access:** Admin, HOD, Lecturer.
- **Request Body (Form-data):**

| Parameter    | Type    | Required | Description                             |
|--------------|---------|----------|-----------------------------------------|
| file         | file    | Yes      | The file containing the results.        |

- **Response:**

| Status Code | Message                        |
|-------------|--------------------------------|
| 200         | Results uploaded successfully  |
| 400         | No file part or error          |
| 500         | Internal server error          |

- **Example Output:**
```json
{
  "message": "File processed and results saved successfully",
  "records": 20
}
```

---

### 14. **Get Action Logs**

- **Endpoint:** `GET /api/v1/security/action-logs`
- **Description:** Retrieves action logs (e.g., user actions) with pagination.
- **Role Access:** Admin, HOD.
- **Response:**

| Status Code | Message                         |
|-------------|---------------------------------|
| 200         | Action logs retrieved successfully |
| 403         | Forbidden                       |

- **Example Output:**
```json
{
  "action_logs": [
    {
      "id": 1,
      "user_id": 1,
      "username": "john_doe",
      "action": "submit_result",
      "resource": "Result",
      "resource_id": 1,
      "details": "{\"course_code\": \"COS102\"}",
      "timestamp": "2024-01-15T12:30:00",
      "ip_address": "127.0.0.1",
      "user_agent": "Mozilla/5.0"
    }
  ],
  "total_results": 10,
  "current_page": 1,
  "total_pages": 1,
  "per_page": 10
}
```
---
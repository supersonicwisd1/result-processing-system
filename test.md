Sure! Here's a detailed continuation for the other endpoints based on your request, formatted similarly to the previous ones.

---

### 4. **Get Current User Information**

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

### 5. **Update Username**

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

### 6. **Update Email**

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

### 7. **Change Password**

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

### 8. **Get Result by ID**

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

### 9. **Update or Create Score for a Result**

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

### 10. **Update Result Metadata**

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

### 11. **Search for Results**

- **Endpoint:** `GET /api/v1/results/search`
- **Description:** Searches for results based on various criteria such as course code, student name, and semester.
- **Role Access:** Admin, HOD, Lecturer.
- **Query Parameters:**

| Parameter        | Type   | Description                                |
|------------------|--------|--------------------------------------------|
| course_code      | string | Filter by course code.                    |
| student_name     | string | Filter by student name.                   |
| semester_name    | string | Filter by semester name.                  |
| registration_number | string | Filter by student registration number.  |

- **Response:**

| Status Code | Message                         |
|-------------|---------------------------------|
| 200         | Results retrieved successfully  |
| 400         | Invalid query parameters        |

- **Example Output:**
```json
{
  "results": [
    {
      "course_code": "COS102",
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
- **Description:** Uploads and processes a results file (e.g., CSV, XLSX).
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

This concludes the breakdown of all the endpoints with detailed examples and explanations. Feel free to expand or modify this structure as necessary for your project!
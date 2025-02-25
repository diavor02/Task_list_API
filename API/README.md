<h2>Table of contents:</h2>
<ul>
  <li><a href="#overview">Overview</a></li>
  <li><a href="#api-documentation">API Documentation</a></li>
  <li><a href="#features">Features</a></li>
  <li><a href="#api-endpoints">API Endpoints</a></li>
  <li><a href="#database-schema">Database Schema</a></li>
  <li><a href="#authentication">Authentication</a></li>
  <li><a href="#example-usage-with-python-scripts">Example Usage with Python Scripts</a></li>
  <li><a href="#request-and-response-examples">Request and Response Examples</a></li>
  <li><a href="#security-notes">Security Notes</a></li>
  <li><a href="#deployment">Deployment</a></li>
  <li><a href="#dependencies">Dependencies</a></li>
  <li><a href="#license">License</a></li>
</ul>

<br>
<h1>PART 1: THE API ARCHITECTURE</h1>
<h2>Overview</h2>
<p>A secure RESTful API for user authentication and task management, built with FastAPI and deployed on AWS Lambda using API Gateway.</p>
<br>

<h2>API Documentation</h2>

Interactive Swagger/OpenAPI documentation available at:  
[https://x1y5tdqmai.execute-api.us-east-1.amazonaws.com/docs](https://x1y5tdqmai.execute-api.us-east-1.amazonaws.com/docs)
<br>
<br>
<h2>Features</h2>

- 🔐 JWT-based authentication with token expiration
- 👤 User registration, login, profile management, and deletion
- 📝 Task creation, retrieval, updating, and deletion
- 🔍 Task filtering by keywords and date ranges
- 🔗 HATEOAS (Hypermedia) links in responses
- 🛡️ Secure password hashing and validation
- 📅 Date validation and formatting
- 🚀 Deployed on AWS with API Gateway + Lambda


<p align="center">
 <img src="architecture.png" height="500">
</p>

<br>
<h2>API Endpoints</h2>
<h3>User Management</h3>

| Method | Endpoint               | Description                            |
|--------|------------------------|----------------------------------------|
| POST   | `/users`               | Register a new user                    |
| POST   | `/auth/token`          | Authenticate and get JWT token         |
| GET    | `/users/me`            | Get user information                   |
| PATCH  | `/users/me`            | Update user information                |
| DELETE | `/users/me`            | Delete user account                    |
<br>
<h3>Task Management</h3>

| Method | Endpoint                     | Description                               |
|--------|------------------------------|-------------------------------------------|
| GET    | `/tasks/{id}`                | Get a task based on its id                |
| GET    | `/tasks`                     | Get tasks based on input query parameters |
| POST   | `/tasks`                     | Create a new task                         |
| PATCH  | `/tasks/{id}`                | Update task information                   |
| DELETE | `/tasks/{id}`                | Delete specific task                      |
<br>
<h2>Database Schema</h2>
<h3>Users Table</h3>

| Column         | Type      | Description                                 |
|----------------|-----------|---------------------------------------------|
| id (PK)        | Integer   | Auto-generated user ID                      |
| email          | String    | Unique email address                        |
| password       | String    | BCrypt-hashed password                      |
| notifications  | Integer   | Notification preference (0/1, default is 1) |
<br>
<h3>Tasks Table</h3>

| Column         | Type      | Description                                 |
|----------------|-----------|---------------------------------------------|
| id (PK)        | Integer   | Auto-generated task ID                      |
| user_id (FK)   | Integer   | Associated user ID                          |
| description    | String    | Task description (500 chars max)            |
| deadline       | Date      | Task deadline in YYYY-MM-DD format          |
<br>
<h2>Authentication</h2>
<p>All API endpoints except user registration and token acquisition require JWT authentication. Include the token in the Authorization header: <code>Authorization: Bearer [your_token]</code></p>
<br>
<h2>Example Usage with Python Scripts</h2>
<p>First, ensure the <code>requests</code> library is installed: <code>pip install requests</code>.</p>

<h3>User registration</h3>

```python
import requests

BASE_URL = "https://x1y5tdqmai.execute-api.us-east-1.amazonaws.com"

def register_user(email, password):
    url = f"{BASE_URL}/users"
    payload = {
        "email": email,
        "password": password
    }
    response = requests.post(url, json=payload)
    return response.json()

new_user = register_user("user@example.com", "SecurePass123!")
print(new_user)
```
<br>
<h3>Get Access Token</h3>

```python
def login_user(email, password):
    url = f"{BASE_URL}/auth/token"
    payload = {
        "email": email,
        "password": password
    }
    response = requests.post(url, json=payload)
    return response.json()

# Example usage
login_response = login_user("user@example.com", "SecurePass123!")
access_token = login_response["access_token"]
print("Access Token:", access_token)
```

<br>
<h3>Create Task</h3>

```python
def create_task(description, deadline, access_token):
    url = f"{BASE_URL}/tasks"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "description": description,
        "deadline": deadline
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# Example usage
task = create_task("Finish API project", "2023-12-31", access_token)
print(task)
```

<h3>Get a task based on query parameters</h3>

```python
def get_tasks(access_token, ):
    url = f"{BASE_URL}/tasks"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "keyword_pattern": "",
        "start_date": "",
        "end_date": ""
    }

    response = requests.get(url, json=payload, headers=headers)
    return response.json()

# Example usage
tasks = get_tasks(access_token)
print(tasks)
```

<br>
<h2>Request and Response Examples</h2>
<h3>User Registration Response</h3>

```python
{
  "id": 1,
  "email": "user@example.com",
  "notifications": 1,
  "links": {
    "self": {"href": "/users", "method": "POST"},
    "login_for_access_token": {"href": "/token", "method": "POST"}
  }
}
```
<br>
<h3>Get access token</h3>

```python
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "links": {
    "self": {"href": "/token", "method": "POST"},
    "update_user": {"href": "/users/me", "method": "PATCH"},
    "delete_user": {"href": "/users/me", "method": "DELETE"}
  }
}
```
<br>
<h3>Task Creation/Update Response</h3>

```python
{
  "task": {
    "id": 1,
    "description": "Complete API project",
    "deadline": "2023-12-31"
  },
  "links": {
    "self": {"href": "/tasks", "method": "POST"},
    "get_tasks": {"href": "/tasks", "method": "GET"},
    "update_task": {"href": "/tasks/1", "method": "PATCH"},
    "delete_task": {"href": "/tasks/1", "method": "DELETE"}
  }
}
```
<br>
<h3>Querying tasks</h3>

```python
{
        "links": {
            "delete_task": {
                "href": "/tasks/2",
                "method": "DELETE"
            },
            "new_task": {
                "href": "/tasks",
                "method": "POST"
            },
            "self": {
                "href": "/tasks",
                "method": "GET"
            },
            "update_task": {
                "href": "/tasks/2",
                "method": "PATCH"
            }
        },
        "task": {
            "deadline": "2025-01-03",
            "description": "Hold a presentation",
            "id": 2
        }
    },
    {
        "links": {
            "delete_task": {
                "href": "/tasks/7",
                "method": "DELETE"
            },
            "new_task": {
                "href": "/tasks",
                "method": "POST"
            },
            "self": {
                "href": "/tasks",
                "method": "GET"
            },
            "update_task": {
                "href": "/tasks/7",
                "method": "PATCH"
            }
        },
        "task": {
            "deadline": "2025-02-02",
            "description": "Set up the meeting",
            "id": 7
        }
    }
```


<h2>Security Notes</h2>
<ul>
  <li>
    Password requirements: 
    <ul>
      <li>Minimum 8 characters</li>
      <li>At least 1 uppercase letter</li>
      <li>At least 1 lowercase letter</li>
      <li>At least 1 digit</li>
      <li>At least 1 special character</li>
    </ul>
  </li>
  <li>All passwords are hashed with BCrypt</li>
  <li>JWT tokens expire after 30 minutes</li>
  <li>HTTPS enforced through API Gateway</li>
</ul>
<br>
<h2>Deployment</h2>
<p>The API is deployed using:</p>
<ul>
  <li>AWS Lambda for serverless execution</li>
  <li>API Gateway for HTTP routing</li>
  <li>PostgreSQL RDS for database storage</li>
  <li>Docker container packaging</li>
</ul>
<br>
<h2>Dependencies</h2>
<ul>
  <li>FastAPI</li>
  <li>SQLAlchemy</li>
  <li>Pydantic (for request/response models)</li>
  <li>Passlib (bcrypt)</li>
  <li>Python-JOSE (JWT)</li>
  <li>Mangum (AWS Lambda adapter)</li>
  <li>Psycopg2 (PostgreSQL adapter)</li>
</ul>
<br>
<h2>License</h2>
<p>This project is licensed under the MIT License - see the LICENSE file for details.</p>
<br>
<p>Note: for more information, access FastApi's automatically created documentation at "https://4mvvs3klti.execute-api.us-east-1.amazonaws.com/docs"</p>














from fastapi import Request, FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from functions import (
    check_password,
    check_email,
    create_access_token,
    get_token_from_header,
    hash_password,
    authenticate_user,
    get_user_id,
    verify_password,
    check_date,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from models import (
    CreateTask,
    TaskData,
    TaskUpdate,
    TaskResponseWithLinks,
    UserData,
    UserPassword,
    UserUpdateRequest,
    UserResponse,
    UserAccessToken,
    ErrorResponse
)
from models import User, Task
from typing import List
from mangum import Mangum
from datetime import datetime
import re

app = FastAPI()

ACCESS_TOKEN_EXPIRE_MINUTES = 30
ALGORITHM = "HS256"

EXISTING_USER = "EXISTING USER"
USER_NOT_FOUND = "USER NOT FOUND"
INVALID_EMAIL = "INVALID EMAIL"
INVALID_PASSWORD = "INVALID PASSWORD"
INVALID_CREDENTIALS = "INVALID CREDENTIALS"
TASK_NOT_FOUND = "TASK NOT FOUND"
INVALID_DATE = "INVALID DATE"

DATABASE_URL = (
    ""
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal() 
    try:
        yield db
    finally:
        db.close()


@app.post("/users", response_model=UserResponse, status_code=201)
async def new_user(user: UserData, db: Session = Depends(get_db)):
    """
    Register a new user account.

    Args:
        The user's registration data (email and password).

    Returns:
        Newly created user details with HATEOAS links.

    Raises:
        HTTPException: 
            - 409 (Conflict): If email already exists in system
            - 400 (Bad Request): For invalid email format or password 
            policy violations
    """
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail=ErrorResponse(
                code=EXISTING_USER,
                message="A user with this email already exists.",
                details={"email": user.email}
            ).model_dump()
        )

    if not check_password(user.password) or not check_email(user.email):
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                code=INVALID_PASSWORD,
                message=("Invalid email or password. Passwords must contain at least "
                    "one uppercase letter, one lowercase letter, one digit, "
                    "one special character, and be at least 8 characters long."),
                details={
                            "email": user.email,
                            "password": user.password
                        }
            ).model_dump()
        )

    db_user = User(
        email=user.email,
        password=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    links = {
            "self": {"href": "/users", "method": "POST"},
            "login_for_access_token": {"href": "/token", "method": "POST"}
            }

    return UserResponse(
        id = db_user.id,
        email = db_user.email,
        notifications = 1,
        links = links
    )


@app.post("/auth/token", response_model = UserAccessToken)
async def login_for_access_token(user: UserData, 
                                 db: Session = Depends(get_db)):
    """
    Authenticate user and generate JWT access token.

    Args:
        User credentials containing email and password.

    Returns:
        Access token with token type and navigation links.

    Raises:
        HTTPException: 
            - 401 (Unauthorized): For invalid authentication credentials
            - 400 if the user cannot be found
    """
    db_user = authenticate_user(user.email, user.password, db)
    access_token = create_access_token(data={"sub": str(db_user.id)})

    links = {
        "self": {"href": "/token", "method": "POST"},
        "update_user": {"href": "/users/me", "method": "PATCH"},
        "delete_user": {"href": "/users/me", "method": "DELETE"},
    }

    return UserAccessToken(
        access_token = access_token,
        token_type = "bearer",
        links = links
    )


@app.get("/users/me", response_model=UserResponse)
async def get_user(
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_header)
):
    """
    Retrieve authenticated user's profile information.

    Returns:
        Current user details with HATEOAS links.

    Raises:
        HTTPException: 
            - 401 (Unauthorized): Invalid or missing JWT token
            - 404 (Not Found): If user account no longer exists
    """
    user_id = get_user_id(db, token)
    db_user = db.query(User).filter(User.id == user_id).first()

    if db_user is None:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                code=USER_NOT_FOUND,
                message="User not found",
            ).model_dump()
        )
    
    links = {
        "self": {"href": "/users/me", "method": "GET"},
        "update_user": {"href": "/users/me", "method": "PATCH"},
        "delete_user": {"href": "/users/me", "method": "DELETE"}
    }

    return UserResponse(
        id=db_user.id,
        email=db_user.email,
        notifications=db_user.notifications,
        links=links
    )

@app.patch("/users/me", response_model=UserResponse)
async def update_user(
    update: UserUpdateRequest,
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_header)
):
    """
    Update authenticated user's account details.

    Args:
        Fields to update, requiring current password validation

    Returns:
        Updated user details with navigation links.

    Raises:
        HTTPException: 
            - 401 (Unauthorized): Invalid or missing JWT token
            - 404 (Not Found): If user account no longer exists
            - 400 (Bad Request): For validation errors in new credentials
    """
    user_id = get_user_id(db, token)
    db_user = db.query(User).filter(User.id == user_id).first()

    if db_user is None:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                code=USER_NOT_FOUND,
                message="User not found",
            ).model_dump()
        )

    if update.current_password: 
        if verify_password(update.current_password, db_user.password):

            if update.new_password:
                if not check_password(update.new_password):
                    raise HTTPException(
                        status_code=400,
                        detail=ErrorResponse(
                            code=INVALID_PASSWORD,
                            message=("Invalid email or password. Passwords must contain at least "
                                "one uppercase letter, one lowercase letter, one digit, "
                                "one special character, and be at least 8 characters long.")
                        ).model_dump()
                    )

            db_user.password = hash_password(update.new_password)

            if update.email:
                if not check_email(update.email):
                    raise HTTPException(
                        status_code=400,
                        detail=ErrorResponse(
                            code=INVALID_EMAIL,
                            message="Invalid email format",
                            details={"email": update.email}
                        ).model_dump()
                    )
                db_user.email = update.email


            if update.update_notification_status == "Yes":
                db_user.notifications = 0 if db_user.notifications else 1

        else:
            raise HTTPException(
                    status_code=400,
                    detail=ErrorResponse(
                        code=INVALID_PASSWORD,
                        message="Current password is incorrect",
                    ).model_dump()
                )
    else:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                code=INVALID_PASSWORD,
                message="Current password is required to update the user credentials",
            ).model_dump()
        )

    db.commit()
    db.refresh(db_user)

    links = {
        "self": {"href": "/users/me", "method": "PATCH"},
        "delete_user": {"href": "/users/me", "method": "DELETE"},
    }

    return UserResponse(
        id=db_user.id,
        email=db_user.email,
        notifications=db_user.notifications,
        links=links
    )


@app.delete("/users/me", status_code=204)
async def delete_user(
    credential: UserPassword,
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_header)
):
    """
    Permanently delete authenticated user's account.

    Args:
        Current password confirmation

    Raises:
        HTTPException: 
            - 401 (Unauthorized): Invalid or missing JWT token
            - 400 (Bad Request): Incorrect password confirmation
            - 404 (Not Found): If user account no longer exists
    """
    user_id = get_user_id(db, token)
    db_user = db.query(User).filter(User.id == user_id).first()

    if not verify_password(credential.password, db_user.password):
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                code=INVALID_PASSWORD,
                message="Current password is incorrect",
            ).model_dump()
        )

    if db_user is None:
        raise HTTPException(
            status_code=404, 
            detail=ErrorResponse(
                code=USER_NOT_FOUND,
                message="User not found"
            ).model_dump()
        )

    db.delete(db_user)
    db.commit()
    return


@app.get("/tasks/{id}", response_model=TaskResponseWithLinks)
async def get_task(id: int, db: Session = Depends(get_db), token: str = Depends(get_token_from_header)):
    """
    Retrieve specific task by ID for authenticated user.

    Args:
        Task identifier.

    Returns:
        Task details with associated links.

    Raises:
        HTTPException: 
            - 401 (Unauthorized): Invalid or missing JWT token
            - 404 (Not Found): Task not found or unauthorized access
    """
    user_id = get_user_id(db, token)
    db_task = db.query(Task).filter(Task.user_id == user_id, Task.id == id).first()

    if db_task is None:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                code=TASK_NOT_FOUND,
                message="Task not found",
                details={"task id": id}
            ).model_dump()
        )
    
    links = {"self": {"href": "/tasks", "method": "GET"},
             "new_task": {"href": f"/tasks/{id}", "method": "POST"},
             "update_task": {"href": f"/tasks/{id}", "method": "PATCH"},
             "delete_task": {"href": f"/tasks/{id}", "method": "DELETE"}}
    
    return TaskResponseWithLinks(
        task=db_task,
        links=links
    )


@app.get("/tasks", response_model=List[TaskResponseWithLinks])
async def get_tasks(
    query: TaskData = Depends(),
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_header)
):
    """
    Search tasks with optional filters for authenticated user.

    Query Parameters:
        - keyword_pattern (str): Filter tasks by description substring
        - start_date (date): Tasks due after this date (inclusive)
        - end_date (date): Tasks due before this date (inclusive)

    Returns:
        Matching tasks with navigation links

    Raises:
        HTTPException: 
            - 401 (Unauthorized): Invalid or missing JWT token
    """
    user_id = get_user_id(db, token)

    tasks_query = db.query(Task).filter(Task.user_id == user_id)


    if query.keyword_pattern:
        keyword_pattern = f"%{query.keyword_pattern}%"
        tasks_query = tasks_query.filter(Task.description.ilike(keyword_pattern))

    if query.start_date:
        tasks_query = tasks_query.filter(Task.deadline >= query.start_date)

    if query.end_date:
        tasks_query = tasks_query.filter(Task.deadline <= query.end_date)

    tasks = tasks_query.all()

    list_task_responses = []

    for task in tasks:
        links = {"self": {"href": "/tasks", "method": "GET"},
             "new_task": {"href": "/tasks", "method": "POST"},
             "update_task": {"href": f"/tasks/{task.id}", "method": "PATCH"},
             "delete_task": {"href": f"/tasks/{task.id}", "method": "DELETE"}}
        list_task_responses.append(TaskResponseWithLinks(task=task, links=links))

    return list_task_responses


@app.post("/tasks", response_model=TaskResponseWithLinks, status_code=201)
async def new_task(
    task: CreateTask,
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_header)
):
    """
    Create new task for authenticated user.

    Args:
        The description and deadline of the task.

    Returns:
        The task information as well as useful links.

    Raises:
        HTTPException: 
            - 401 (Unauthorized): Invalid or missing JWT token
            - 400 (Bad Request): Invalid date format
    """
    user_id = get_user_id(db, token)

    if not check_date(task.deadline):
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                code=INVALID_DATE,
                message="Invalid date format. Try YYYY-MM-DD",
                details={"deadline": task.deadline}
            ).model_dump()
        )

    # Convert the deadline string to a date object
    deadline_date = datetime.strptime(task.deadline, "%Y-%m-%d").date()
    db_task = Task(
        user_id=user_id,
        description=task.description,
        deadline=deadline_date
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    links = {"self": {"href": "/tasks", "method": "POST"},
            "get_tasks": {"href": "/tasks", "method": "GET"},
            "update_task": {"href": f"/tasks/{db_task.id}", "method": "PATCH"},
            "delete_task": {"href": f"/tasks/{db_task.id}", "method": "DELETE"}}

    return TaskResponseWithLinks(
        task=db_task,
        links=links
    )


@app.patch("/tasks/{id}", response_model=TaskResponseWithLinks)
async def update_task(
    id: int,
    update: TaskUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_header)
):
    """
    Update a task based on its id.

    Args:
        The task identifier, as well as the fields to update 
        (description and/or deadline)

    Returns:
        Updated task details with navigation links.

    Raises:
        HTTPException: 
            - 401 (Unauthorized): Invalid or missing JWT token
            - 404 (Not Found): Task not found or unauthorized access
            - 400 (Bad Request): Invalid date format
    """
    user_id = get_user_id(db, token)
    db_task = db.query(Task).filter(Task.user_id == user_id, Task.id == id).first()

    if db_task is None:
        raise HTTPException(
            status_code=404, 
            detail=ErrorResponse(
                code=TASK_NOT_FOUND,
                message="Task not found"
            ).model_dump()
        )
    
    if update.deadline:
        if not check_date(update.deadline):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    code=INVALID_DATE,
                    message="Invalid date format. Try YYYY-MM-DD",
                    details={"deadline": update.deadline}
                ).model_dump()
            )
        
        deadline_date = datetime.strptime(update.deadline, "%Y-%m-%d").date()
        db_task.deadline = deadline_date

    if update.description:
        db_task.description = update.description

    db.commit()
    db.refresh(db_task)


    links = {"self": {"href": f"/tasks/{id}", "method": "PATCH"},
             "new_task": {"href": "/tasks", "method": "POST"},
             "get_tasks": {"href": "/tasks", "method": "GET"},
             "delete_task": {"href": f"/tasks/{id}", "method": "DELETE"}}

    return TaskResponseWithLinks(
        task=db_task,
        links=links
    )


@app.delete("/tasks/{id}", status_code=204)
async def delete_task(
    id: int,
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_header)
):
    """
    Delete specific task for authenticated user.

    Args:
        The task identifier.

    Returns:
        Nothing (sattus code 204).

    Raises:
        HTTPException: 
            - 401 (Unauthorized): Invalid or missing JWT token
            - 404 (Not Found): Task not found or unauthorized access
    """
    user_id = get_user_id(db, token)
    db_task = db.query(Task).filter(Task.user_id == user_id, Task.id == id).first()
    
    if db_task is None:
        raise HTTPException(
            status_code=404, 
            detail=ErrorResponse(
                code=TASK_NOT_FOUND,
                message="Task not found"
            ).model_dump()
        )

    db.delete(db_task)
    db.commit()
    return



handler = Mangum(app)

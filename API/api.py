from fastapi import Request, FastAPI, HTTPException, Depends, status
from functions import (
    check_pass,
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
    TaskDescriptionUpdate,
    TaskDeadlineUpdate,
    TaskResponse,
    UserData,
    UserEmailUpdate,
    UserPasswordUpdate,
    UserResponse,
)
from models import User, Task
from typing import List
from mangum import Mangum
from datetime import datetime

app = FastAPI()

ACCESS_TOKEN_EXPIRE_MINUTES = 30
ALGORITHM = "HS256"

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



@app.post("/users", response_model=UserResponse)
def new_user(user: UserData, db: Session = Depends(get_db)):
    """
    Register a new user account.

    This endpoint creates a new user account using the provided email and 
    password. It checks if an account with the given email already exists, 
    validates the email and password (ensuring that the password contains at 
    least one uppercase letter, one digit, and one special character), hashes 
    the password, and then stores the new user in the database.

    Args:
        user (UserData): The user data containing email and password.
        db (Session, optional): A database session provided by dependency 
        injection.

    Returns:
        UserResponse: The created user details including id, email, and 
        notification status.

    Raises:
        HTTPException: If an account with the provided email already exists or 
        if the email/password is invalid.
    """
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists"
        )

    if not check_pass(user.password) or not check_email(user.email):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid email or password. The password must contain at least " 
                "one uppercase letter, "
                "one digit, and one special character."
            )
        )

    db_user = User(
        email=user.email,
        password=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@app.post("/token")
async def login_for_access_token(user: UserData, 
                                 db: Session = Depends(get_db)):
    """
    Authenticate a user and provide a JWT access token.

    This endpoint verifies the provided user credentials. If the credentials 
    are valid, a JWT access token is generated, which is then used to 
    authorize subsequent API requests.

    Args:
        user (UserData): The user data containing email and password.
        db (Session, optional): A database session provided by dependency 
        injection.

    Returns:
        dict: A dictionary containing the access token and token type 
        ("bearer").

    Raises:
        HTTPException: If authentication fails.
    """
    db_user = authenticate_user(user.email, user.password, db)
    access_token = create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@app.put("/users/email", response_model=UserResponse)
async def update_email(
    update: UserEmailUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_header)):
    """
    Update the authenticated user's email address.

    The endpoint validates the user's token, retrieves the corresponding user, 
    and then updates the email address in the database.

    Args:
        update (UserEmailUpdate): The payload containing the new email address.
        db (Session, optional): A database session provided by dependency 
                                injection.
        token (str, optional): JWT token extracted from the request header.

    Returns:
        UserResponse: The updated user details including id, email, and 
        notification status.

    Raises:
        HTTPException: If the user is not found.
    """
    user_id = get_user_id(db, token)
    db_user = db.query(User).filter(User.id == user_id).first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.email = update.email
    db.commit()
    db.refresh(db_user)

    return db_user


@app.put("/users/password", response_model=UserResponse)
async def update_password(
    update: UserPasswordUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_header)
):
    """
    Update the authenticated user's password.

    The endpoint verifies the current password before updating to a new 
    password. The new password is hashed before being saved to the database.

    Args:
        update (UserPasswordUpdate): The payload containing the current and new 
                                     passwords.
        db (Session, optional): A database session provided by dependency 
                                injection.
        token (str, optional): JWT token extracted from the request header.

    Returns:
        UserResponse: The updated user details including id, email, and 
        notification status.

    Raises:
        HTTPException: If the user is not found or if the current password is 
                        incorrect.
    """
    user_id = get_user_id(db, token)
    db_user = db.query(User).filter(User.id == user_id).first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify that the current password matches the stored password
    if not verify_password(update.current_password, db_user.password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    db_user.password = hash_password(update.new_password)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.put("/users/notifications", response_model=UserResponse)
async def update_notifications(
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_header)
):
    """
    Toggle the authenticated user's notification setting.

    This endpoint inverts the current notification status of the user 
    (enabled to disabled or vice versa).

    Args:
        db (Session, optional): A database session provided by dependency 
                                injection.
        token (str, optional): JWT token extracted from the request header.

    Returns:
        UserResponse: The updated user details including id, email, and 
                      notification status.

    Raises:
        HTTPException: If the user is not found.
    """
    user_id = get_user_id(db, token)
    db_user = db.query(User).filter(User.id == user_id).first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.notifications = 0 if db_user.notifications else 1
    db.commit()
    db.refresh(db_user)
    return db_user


@app.delete("/users", response_model=dict)
def delete_user(
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_header)
):
    """
    Delete the authenticated user's account.

    This endpoint removes the user's account from the database.

    Args:
        db (Session, optional): A database session provided by dependency 
                                injection.
        token (str, optional): JWT token extracted from the request header.

    Returns:
        dict: A dictionary confirming the successful deletion of the user.

    Raises:
        HTTPException: If the user is not found.
    """
    user_id = get_user_id(db, token)
    db_user = db.query(User).filter(User.id == user_id).first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(db_user)
    db.commit()
    return {"response": "User deleted successfully"}


@app.get("/tasks", response_model=List[TaskResponse])
def get_tasks(
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_header)
):
    """
    Retrieve all tasks for the authenticated user.

    Args:
        db (Session, optional): A database session provided by dependency 
                                injection.
        token (str, optional): JWT token extracted from the request header.

    Returns:
        List[TaskResponse]: A list of tasks belonging to the user.

    Raises:
        HTTPException: If no tasks are found for the user.
    """
    user_id = get_user_id(db, token)
    tasks = db.query(Task).filter(Task.user_id == user_id).all()
    if not tasks:
        raise HTTPException(status_code=404, 
                            detail="No tasks found for the user")
    return tasks


@app.post("/tasks", response_model=TaskResponse)
def new_task(
    task: CreateTask,
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_header)
):
    """
    Create a new task for the authenticated user.

    The provided deadline must be a string in the format YYYY-MM-DD. It is 
    validated using a regex check and then converted to a Date object before 
    being stored in the database.

    Args:
        task (CreateTask): The payload containing the task description and 
                           deadline.
        db (Session, optional): A database session provided by dependency 
                                injection.
        token (str, optional): JWT token extracted from the request header.

    Returns:
        TaskResponse: The newly created task details including id, 
                      description, and deadline.

    Raises:
        HTTPException: If the provided deadline format is invalid.
    """
    user_id = get_user_id(db, token)

    # The task deadline is passed as a string so as to check the correct format
    if not check_date(task.deadline):
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Try YYYY-MM-DD"
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
    return db_task


@app.put("/tasks/{id}/description", response_model=TaskResponse)
def update_description(
    id: int,
    update: TaskDescriptionUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_header)
):
    """
    Update the description of a specific task.

    This endpoint updates the description of the task identified by its ID,
    provided that the task belongs to the authenticated user.

    Args:
        id (int): The unique identifier of the task.
        update (TaskDescriptionUpdate): The payload containing the new 
                                        description.
        db (Session, optional): A database session provided by dependency 
                                injection.
        token (str, optional): JWT token extracted from the request header.

    Returns:
        TaskResponse: The updated task details including id, description, and 
                      deadline.

    Raises:
        HTTPException: If the task is not found.
    """
    user_id = get_user_id(db, token)
    db_task = db.query(Task).filter(Task.user_id == user_id, Task.id == id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db_task.description = update.description
    db.commit()
    db.refresh(db_task)
    return db_task


@app.put("/tasks/{id}/deadline", response_model=TaskResponse)
def update_deadline(
    id: int,
    update: TaskDeadlineUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_header)
):
    """
    Update the deadline of a specific task.

    This endpoint updates the deadline of the task identified by its ID,
    provided that the task belongs to the authenticated user.
    The new deadline must be in the format YYYY-MM-DD.

    Args:
        id (int): The unique identifier of the task.
        update (TaskDeadlineUpdate): The payload containing the new deadline.
        db (Session, optional): A database session provided by dependency 
                                injection.
        token (str, optional): JWT token extracted from the request header.

    Returns:
        TaskResponse: The updated task details including id, description, 
                      and deadline.

    Raises:
        HTTPException: If the task is not found.
    """
    user_id = get_user_id(db, token)
    db_task = db.query(Task).filter(Task.user_id == user_id, Task.id == id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    deadline_date = datetime.strptime(update.deadline, "%Y-%m-%d").date()
    db_task.deadline = deadline_date
    db.commit()
    db.refresh(db_task)
    return db_task


@app.delete("/tasks/{id}", response_model=dict)
def delete_task(
    id: int,
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_header)
):
    """
    Delete a specific task.

    This endpoint deletes the task identified by its unique ID,
    provided that the task belongs to the authenticated user.

    Args:
        id (int): The unique identifier of the task.
        db (Session, optional): A database session provided by dependency 
                                injection.
        token (str, optional): JWT token extracted from the request header.

    Returns:
        dict: A dictionary confirming the successful deletion of the task.

    Raises:
        HTTPException: If the task is not found.
    """
    user_id = get_user_id(db, token)
    db_task = db.query(Task).filter(Task.user_id == user_id, Task.id == id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(db_task)
    db.commit()
    return {"response": "Task deleted successfully"}


handler = Mangum(app)


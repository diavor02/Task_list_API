from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from pydantic import BaseModel, Field
from datetime import date
from typing import Dict, Optional, Any


Base = declarative_base()

# Defining the 2 SQL tables

# 1) The `users` table stores information about users, including their authentication details 
# and notification preferences. This table is linked to the `tasks` table via a one-to-many 
# relationship, where one user can have multiple tasks.
class User(Base):
    __tablename__ = "users"

    # A unique identifier for each user, automatically generated and acting as the primary key. 
    # This ID is used as a foreign key in the `tasks` table to associate tasks with their respective users.
    id = Column("id", Integer, primary_key=True)

    # The email address of the user, used for sending notifications. Each email must be unique 
    # across the table to ensure no two users share the same email address.
    email = Column("email", String(255), nullable=False, unique=True)

    # The user's password, stored in an encrypted format for secure authentication.
    password = Column("password", String(255), nullable=False)

    # A flag indicating whether the user wishes to receive notifications about their tasks. 
    # The value is stored as an integer, where `1` means notifications are enabled, and `0` 
    # means they are disabled. By default, notifications are enabled (`1`).
    notifications = Column("notifications", Integer, default=1, nullable=False)

    # A relationship to the `tasks` table, establishing a one-to-many connection between users 
    # and their tasks. The `cascade` option ensures that when a user is deleted, all associated 
    # tasks are also deleted.
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")


# 2) The `tasks` table stores information about tasks created by users. Each task is associated 
# with a specific user via the `user_id` foreign key, creating a one-to-many relationship 
# between users and tasks.
class Task(Base):
    __tablename__ = "tasks"

    # A unique identifier for each task, automatically generated and acting as the primary key.
    id = Column("id", Integer, primary_key=True)

    # The `user_id` column establishes a foreign key relationship with the `users` table, 
    # linking each task to a specific user. This ensures that every task is associated with 
    # the user who created it.
    user_id = Column("user_id", Integer, ForeignKey("users.id"), nullable=False)

    # A description of the task, provided by the user. This field is required and can store 
    # up to 500 characters.
    description = Column("description", String(500), nullable=False)

    # The deadline for the task, provided by the user. This field is used to determine when 
    # email notifications should be sent to the user regarding the task.
    deadline = Column("deadline", Date, nullable=False)

    # A relationship to the `users` table, establishing the many-to-one connection between 
    # tasks and their respective users.
    user = relationship("User", back_populates="tasks")


# Pydantic models for the API methods

class UserData(BaseModel):
    email: str
    password: str

class UserPassword(BaseModel):
    password: str

class UserUpdateRequest(BaseModel):
    current_password: str = Field(None, description="Current password for verification")
    email: Optional[str] = Field(None, description="New email address")
    new_password: Optional[str] = Field(None, description="New password to set")
    update_notification_status: Optional[str] = Field(None, description="'Yes' if you want to update "
                                                      "the notification status, empty otherwise")
    
class UserResponse(BaseModel):
    id: int
    email: str
    notifications: int
    links: Dict[str, Any]

    class Config:
        from_attributes = True

class UserAccessToken(BaseModel):
    access_token: str
    token_type: str
    links: Dict[str, Any]

class CreateTask(BaseModel):
    description: str
    deadline: str

class TaskUpdate(BaseModel):
    description: Optional[str] = Field(None, description="New task description")
    deadline: Optional[str] = Field(None, description="New task deadline")


class TaskData(BaseModel):
    keyword_pattern: Optional[str] = Field(None, description="Query based on keyword pattern from the task description")
    start_date: Optional[date] = Field(None, description="Query based on tasks due after the specified date")
    end_date: Optional[date] = Field(None, description="Query based on tasks due prior to the specified date")

class TaskResponse(BaseModel):
    id: int
    description: str
    deadline: date

    class Config:
        from_attributes = True

class TaskResponseWithLinks(BaseModel):
    task: TaskResponse
    links: Dict[str, Any]

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None

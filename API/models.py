from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from pydantic import BaseModel
from datetime import date

# Define the base
Base = declarative_base()

# Defining the 2 SQL tables

# 1) The users table, containing information about users
class User(Base):
    __tablename__ = "users"

    # An ID generated automatically, acting as the primary key. The user's ID 
    # acts as a foreign key for the tasks table.
    id = Column("id", Integer, primary_key=True) 

    # A column that stores emails for sending notifications to the users. 
    # Each entity in the table must be unique.
    email = Column("email", String(255), nullable=False, unique=True) 

    # A password used for authentication. All passwords are encrypted.
    password = Column("password", String(255), nullable=False)

    # An integer value acting as a boolean. 1 means the user expects 
    # notifications regarding their tasks, while 0 means the opposite. 
    # The default value is 1.
    notifications = Column("notifications", Integer, default=1, nullable=False)

    tasks = relationship("Task", back_populates="user", 
                         cascade="all, delete-orphan")

# 2) The tasks table, containing information about an individual user's stored 
#    tasks
class Task(Base):
    __tablename__ = "tasks"

    # An ID generated automatically, acting as the primary key.
    id = Column("id", Integer, primary_key=True)

    # The user_id column links each task to a specific user in the users table. 
    # The relationship is one-to-many.
    user_id = Column("user_id", Integer, ForeignKey("users.id"), nullable=False)

    # A task description inputted by the user
    description = Column("description", String(500), nullable=False)

    # A task deadline inputted by the user. The email notifications are sent 
    # based on the values in the deadline column.
    deadline = Column("deadline", Date, nullable=False)

    user = relationship("User", back_populates="tasks")


# Pydantic models are a core dependency of FastAPI. They are used to define 
# request and response models, to automatically generate OpenAPI documentation, 
# and to ensure API payload validation.

class UserData(BaseModel):
    email: str
    password: str

class UserEmailUpdate(BaseModel):
    email: str

class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str

class UserResponse(BaseModel):
    id: int
    email: str
    notifications: int

    class Config:
        from_attributes = True


class CreateTask(BaseModel):
    description: str
    deadline: str

class TaskDescriptionUpdate(BaseModel):
    description: str

class TaskDeadlineUpdate(BaseModel):
    deadline: str

class TaskResponse(BaseModel):
    id: int
    description: str
    deadline: date

    class Config:
        from_attributes = True

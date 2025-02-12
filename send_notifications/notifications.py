import smtplib
import ssl
from fastapi import Depends
from email.message import EmailMessage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
import psycopg2

Base = declarative_base()

# Defining the 2 SQL tables

# 1) The users table, containing information about users
class User(Base):
    __tablename__ = "users"

    # An id generated automatically, acting as the primary key. The user's id 
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

    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

# 2) The tasks table, containing information about an individual user's stored 
#    tasks
class Task(Base):
    __tablename__ = "tasks"

    # An id generated automatically, acting as the primary key.
    id = Column("id", Integer, primary_key=True)

    # The user_id column links each task to a specific user in the users table. 
    # The relationship is one-to-many.
    user_id = Column("user_id", Integer, ForeignKey("users.id"), nullable=False)

    # A task description inputted by the user
    description = Column("description", String(500), nullable=False)

    # A task deadline inputted by the user. The email notifications are sent 
    # based on the values in the deadline column
    deadline = Column("deadline", Date, nullable=False)

    user = relationship("User", back_populates="tasks")


DATABASE_URL = (
    "postgresql+psycopg2://postgres:Bag_pula123.@my-first-db.cbomes4a4cj7.us-east-1.rds.amazonaws.com:5432/postgres"
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Function name: sendUserNotif
# Arguments: a database session
# Purpose: Sends users reminders on their email regarding their tasks due 
#          tomorrow. 
def sendUserNotif(db):
    try:
        tomorrow = (datetime.now() + timedelta(days=1)).date()

        # Join the tasks and users tables
        tasks = (
            db.query(Task.user_id, Task.description, User.email)
            .join(User, User.id == Task.user_id)
            .filter(Task.deadline == tomorrow)
            .all()
        )

        # Create a dictionary of tasks. The keys represent the email addresses, 
        # while the values represent a list of task descriptions
        task_dict = {}
        for task in tasks:
            if task[2] not in task_dict:
                task_dict[task[2]] = []
            task_dict[task[2]].append(task[1])

        # Send to each user the appropriate notification
        for email, descriptions in task_dict.items():
            sendEmail(email, descriptions)
    except Exception as e:
        print(f"Error in sendUserNotif: {str(e)}")
        raise


# Function name: sendEmail
# Arguments: the user's email and the tasks due tomorrow descriptions
# Purpose: Creates the body content and sends the email 
def sendEmail(email, descriptions):
    email_sender = 'mylistnotifications@gmail.com' # The official email of the app
    email_password = 'zqqy gpac mqho knym'
    email_receiver = email # The email of the user

    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['Subject'] = "Tasks due tomorrow"

    paragraphs = "".join([f"<p>{d}</p>" for d in descriptions])

    body = f"""
    <html>
        <body>
            <p>The following tasks are due tomorrow:</p>
            {paragraphs}
            <p>Have a nice day!</p>
        </body>
    </html>
    """

    em.set_content(body, subtype='html')

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())


# The lambda entry point
def lambda_handler(event, context):
    db = SessionLocal()  # Manually create a session
    try:
        sendUserNotif(db)
        return {"statusCode": 200, "body": "Notifications sent successfully"}
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Error sending notifications: {str(e)}"
        }
    finally:
        db.close()

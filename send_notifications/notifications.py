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

# 1) The users table
class User(Base):
    __tablename__ = "users"

    id = Column("id", Integer, primary_key=True) 

    email = Column("email", String(255), nullable=False, unique=True) 

    password = Column("password", String(255), nullable=False)

    notifications = Column("notifications", Integer, default=1, nullable=False)

    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

# 2) The tasks table
class Task(Base):
    __tablename__ = "tasks"

    id = Column("id", Integer, primary_key=True)

    user_id = Column("user_id", Integer, ForeignKey("users.id"), nullable=False)

    description = Column("description", String(500), nullable=False)

    deadline = Column("deadline", Date, nullable=False)

    user = relationship("User", back_populates="tasks")


DATABASE_URL = (
    ""
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Function name: sendUserNotif
# Arguments: 
#   - db (Session): A database session instance.
# Returns:
#   - None
# Purpose: Sends reminder emails to users regarding their tasks due the next day.
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
            send_email(email, descriptions)
    except Exception as e:
        print(f"Error in sendUserNotif: {str(e)}")
        raise


# Function name: send_email
# Arguments: 
#   - email (str): The recipient's email address.
#   - descriptions (list[str]): A list of task descriptions due the next day.
# Returns:
#   - None
# Purpose: Composes an email with task reminders and sends it to the user.
def send_email(email, descriptions):
    email_sender = 'mylistnotifications@gmail.com' 
    email_password = ''
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
    db = SessionLocal()
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

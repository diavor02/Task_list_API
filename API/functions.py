from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from models import User, ErrorResponse
from datetime import datetime, timedelta, timezone, date
import re
from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext
from fastapi import Request, HTTPException
from typing import Union


SECRET_KEY = ""
ALGORITHM = "HS256"

INVALID_TOKEN = "INVALID TOKEN"
USER_NOT_FOUND = "USER NOT FOUND"
INVALID_CREDENTIALS = "INVALID CREDENTIALS"
AUTHORIZATION_HEADER_NOT_FOUND = "AUTHORIZATION_HEADER_NOT_FOUND"
INVALID_AUTHORIZATION_HEADER = "INVALID_AUTHORIZATION_HEADER"
INVALID_AUTHENTIFICATION_SCHEME = "INVALID_AUTHENTIFICATION_SCHEME"


DATABASE_URL = (
    ""
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


################################## Database ###################################

def get_db(SessionLocal=SessionLocal):
    """
    Provide a database session for a request and ensure it is closed after use.

    Yields:
        Session: A SQLAlchemy database session.

    Ensures:
        The session is properly closed to prevent connection leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


################################## Password ###################################

def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    Args:
        password (str): The plaintext password to hash.

    Returns:
        str: The hashed password.
    """
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against its hashed version using bcrypt.

    Args:
        plain_password (str): The plaintext password.
        hashed_password (str): The hashed password.

    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)


def check_password(password: str) -> bool:
    """
    Check if the provided password is secure.

    The password must:
      - Be at least 8 characters long.
      - Contain at least one uppercase letter.
      - Contain at least one lowercase letter.
      - Contain at least one digit.
      - Contain at least one special character (e.g., !@#$%^&*(),.?":{}|<>).

    Args:
        password (str): The plaintext password to check.

    Returns:
        bool: True if the password meets all criteria, False otherwise.
    """
    if len(password) < 8:
        return False
    return bool(
        re.search(r'[A-Z]', password) and       
        re.search(r'[a-z]', password) and 
        re.search(r'\d', password) and
        re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
    )


################################### Token #####################################

def create_access_token(data: dict) -> str:
    """
    Create a JWT access token for API authorization.

    The token payload includes the provided data along with an expiration time 
    set to 30 minutes from the time of creation.

    Args:
        data (dict): The payload data to encode (e.g., user identifier).

    Returns:
        str: The encoded JWT access token.

    Notes:
        The token must be included in the Authorization header for API requests.
        Uses the global SECRET_KEY and ALGORITHM for encoding.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_token_from_header(request: Request) -> str:
    """
    Extract the JWT token from the Authorization header of a request.

    Args:
        request (Request): The FastAPI request object containing the headers.

    Returns:
        str: The extracted JWT token.

    Raises:
        HTTPException: If the Authorization header is missing, improperly 
        formatted, or does not use the Bearer scheme.
    """
    auth_header: str = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
                status_code=401,
                detail=ErrorResponse(
                    code=AUTHORIZATION_HEADER_NOT_FOUND,
                    message="Missing Authorization header",
                ).model_dump()
            )
        
    try:
        scheme, token = auth_header.split()
    except ValueError:
        raise HTTPException(
                status_code=401,
                detail=ErrorResponse(
                    code=INVALID_AUTHORIZATION_HEADER,
                    message="Invalid Authorization header format",
                ).model_dump()
            )
    
    if scheme.lower() != "bearer":
        raise HTTPException(
                status_code=401,
                detail=ErrorResponse(
                    code=INVALID_AUTHENTIFICATION_SCHEME,
                    message="Invalid authentication scheme",
                    details=scheme
                ).model_dump()
            )
    
    return token


############################### Users #########################################

def authenticate_user(email: str, password: str, db: Session):
    """
    Authenticate a user by verifying their email and password.

    Args:
        email (str): The user's email address.
        password (str): The plaintext password.
        db (Session): The database session used to query user data.

    Returns:
        User: The authenticated user object.

    Raises:
        HTTPException: If the email or password does not meet security criteria,
                       the user is not found, or the password is incorrect.
    """
    if not check_email(email) or not check_password(password):
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(
                code=INVALID_CREDENTIALS,
                message=("Invalid email or password. Passwords must contain at least "
                    "one uppercase letter, one lowercase letter, one digit, "
                    "one special character, and be at least 8 characters long.")
            ).model_dump()
        )

    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                code=USER_NOT_FOUND,
                message="User not found",
                details={"email": email}
            ).model_dump()
        )


    if not verify_password(password, db_user.password):
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(
                code=INVALID_CREDENTIALS,
                message="Incorrect password",
                details={"password": password}
            ).model_dump()
        )

    return db_user


def get_user_id(db: Session, token: str) -> int:
    """
    Decode the JWT token to retrieve the associated user ID and verify token 
    validity.

    Args:
        db (Session): The database session used to query the user.
        token (str): The JWT access token.

    Returns:
        int: The authenticated user's ID.

    Raises:
        HTTPException: If the token is invalid, expired, or if the user does 
        not exist.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id: Union[str, None] = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail=ErrorResponse(
                    code=INVALID_TOKEN,
                    message="The decoded user ID does not exist"
                ).model_dump()
            )

        # Query user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=401,
                detail=ErrorResponse(
                    code=USER_NOT_FOUND,
                    message="User not found",
                    details={"user_id": user_id}
                ).model_dump()
            )

        return user.id

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(
                code=INVALID_TOKEN,
                message="Token has expired"
            ).model_dump()
        )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(
                code=INVALID_TOKEN,
                message="Problem decoding the JWT token"
            ).model_dump()
        )


################################## Date #####################################

def check_date(date_input, date_format: str = '%Y-%m-%d') -> bool:
    """
    Validate whether the provided date input conforms to the specified date 
    format.

    If the input is a date object, it is converted to a string using the given 
    format before validation.

    Args:
        date_input: The date input to validate.
        date_format (str): The expected date format (default is '%Y-%m-%d').

    Returns:
        bool: True if the date is valid according to the specified format, 
              False otherwise.
    """
    if isinstance(date_input, date):
        date_input = date_input.strftime(date_format)
    try:
        datetime.strptime(date_input, date_format)
        return True
    except ValueError:
        return False


################################ Notifications ################################

def check_email(email: str) -> bool:
    """
    Validate the format of an email address.

    The email must follow the pattern:
      - A local part containing letters, digits, and allowed special characters.
      - The '@' symbol.
      - A domain part containing letters, digits, hyphens, and dots.
      - A top-level domain with at least two letters.

    Args:
        email (str): The email address to validate.

    Returns:
        bool: True if the email matches the pattern, False otherwise.
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

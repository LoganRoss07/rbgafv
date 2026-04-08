"""
Authentication (verify the user) and authorisation (determines permissions of the users) logic for the backend API

-When accounts are created users passwords are hashed
-Verify passwords from user logins
-Generate JWT access tokens (user login successful)
-Client tokens validatation
-Protection for API routes through dependency functions

:User Registration:
 -> User input email address + password -> password is hashed -> store in database

:User Login: 
 -> User inputs email address + password -> verify password -> JWT token returned

:API Requests:
 Client will send request -> Authorisation: Bearer <token>

 API extracts the token -> verfiy token -> Retrieve stored user identity
 Access only allowed by a valid token

:Admin Routes: 
 Additional permisions e.g. admin role
 routes dictated by require_admin() function 
"""

#Standard Libraries
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from typing import Optional 
#Third Party Libraries
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from models import User
from database import get_db
from sqlalchemy.orm import Session

#Security Configuration
SECRET_KEY = "YOUR_SECRET_KEY"

#HS256 will be used for the crptographic algorithm for signing tokens
ALGORITHM = "HS256"

#Access token Expirey, limits how long a login token is valid
ACCESS_TOKEN_EXPIRE_MINUTES = 60

#Password hashing, argon2 will be used for hashing algorithm
password_hash = PasswordHash.recommended()

#Token Extraction, OAuth2PasswordBearer tells fast API the tokens origin, clients will send token
#FastAPI will extract the token and pass to functions with dependence from oauth2_scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#Pasword Utilities
def get_hash_password(password: str) -> str:
    #hashes the plain text password, when new user registers
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    #verifies if the login password matches the stored hash
    return pwd_context.verify(plain_password, hashed_password)

#token creation
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    #creates signed JWT access token (User identity, role info, expiration)
    
    #copy input data from original dictionary
    to_encode = data.copy()

    #Determine token expiration time
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

#Token Validation 
def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
#Current User Dependency
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    email:str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=401,
            detail="Token payload missing user identifier",
            headers={"WWW-Authenticate": "Bearer"}
        )
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user

#Admin authorisation check
def require_admin(current_user: User = Depends(get_current_user)):
    #Check if current user has admin perms
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    
    return current_user 

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

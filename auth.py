from datetime import datetime, timedelta, timezone

from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
import jwt
from jwt.exceptions import InvalidTokenError

from dotenv import load_dotenv, dotenv_values
import os

from sqlmodel import select

from .src.manuals.models import User, UserInDB, TokenData, UserCreateForm 
from .dependencies import SessionDep

load_dotenv()
AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")




fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc",
        "disabled": False,
    }
}


password_hash = PasswordHash.recommended()

DUMMY_HASH = password_hash.hash("dummypassword")


def hash_password(password: str):
    return "fakehashed" + password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password):
    return password_hash.hash(password)

async def get_user_by_username(username: str, session: SessionDep):
    find_user_stmt = select(UserInDB).where(UserInDB.username == username)
    results = session.exec(find_user_stmt)
    user = results.first()
    return user

async def get_user_by_email(data: UserCreateForm, session: SessionDep):
    find_user_stmt = select(UserInDB).where(UserInDB.email == data.email)
    results = session.exec(find_user_stmt)
    if not results:
        return None
    user = results.first()
    return user

async def get_user(session, username: str):
    user = await get_user_by_username(username, session)
    if user:
        return user
    
def decode_token(token):
    # This doesn't provide any security at all
    # Check the next version
    user = get_user(fake_users_db, token)
    return user


async def authenticate_user(session: SessionDep, username: str, password: str):
    user = await get_user_by_username(username, session)
    if not user:
        verify_password(password, DUMMY_HASH)
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, AUTH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], 
    session: SessionDep
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, AUTH_SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = await get_user(session, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)], 
    session: SessionDep
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user



async def create_user(
    data: UserCreateForm, 
    session: SessionDep,
    existing_user: Annotated[User, Depends(get_user_by_email)]
):
    """
    curl -F "username=uname" -F "first_name=FirstName" -F "last_name=LastName" -F "password=testing" -F "email=mymail" -F "disabled=False"  http://localhost:8000/users/create

    """
    if existing_user:
        raise HTTPException(status_code=409, detail="user exists")  
    
    hashed_password = get_password_hash(data.password)
    user = UserInDB(
        username=data.username,
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
        disabled=data.disabled,
        hashed_password=hashed_password
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    return user
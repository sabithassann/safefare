from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.schemas.user import User, UserCreate
from typing import List, Optional

router = APIRouter()

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    success: bool
    token: str
    username: str
    message: str

@router.post("/login", response_model=AdminLoginResponse)
def login_admin(credentials: AdminLoginRequest):
    """
    Authenticate admin user for SafeFare Studio access.
    """
    valid_users = {
        "admin": ["admin", "admin123", "safefare", "safefare123"],
        "safefare": ["safefare123", "admin"]
    }
    
    allowed_passwords = valid_users.get(credentials.username.strip().lower())
    if allowed_passwords and credentials.password.strip() in allowed_passwords:
        return AdminLoginResponse(
            success=True,
            token="safefare_session_token_admin",
            username=credentials.username,
            message="Login successful"
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password"
    )

@router.post("/", response_model=User)
def create_user(user_in: UserCreate):
    """
    Create new user.
    """
    # This is a dummy implementation
    return User(
        id=1,
        email=user_in.email,
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser,
        full_name=user_in.full_name
    )

@router.get("/", response_model=List[User])
def read_users(skip: int = 0, limit: int = 100):
    """
    Retrieve users.
    """
    # This is a dummy implementation
    return [
        User(id=1, email="user@example.com", is_active=True, is_superuser=False, full_name="Example User")
    ]


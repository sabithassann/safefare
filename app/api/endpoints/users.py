from fastapi import APIRouter
from app.schemas.user import User, UserCreate
from typing import List

router = APIRouter()

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

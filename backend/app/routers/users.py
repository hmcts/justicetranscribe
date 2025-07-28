from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..dependencies import get_current_user, get_current_db_user
from ..database import get_session
from ..models import UserRead, UserUpdate
from ..services import UserService
from ..auth_models import AuthUser

router = APIRouter()


@router.get("/users/me", tags=["users"], response_model=UserRead)
async def read_user_me(current_db_user = Depends(get_current_db_user)):
    """Get current user's database profile"""
    return current_db_user


@router.put("/users/me", tags=["users"], response_model=UserRead)
async def update_user_me(
    user_update: UserUpdate,
    session: Session = Depends(get_session),
    current_db_user = Depends(get_current_db_user)
):
    """Update current user's profile"""
    updated_user = UserService.update_user(session, current_db_user.id, user_update)
    return updated_user


@router.get("/users/auth-info", tags=["users"])
async def read_auth_info(current_user: AuthUser = Depends(get_current_user)):
    """Get authentication information from Azure AD"""
    return {
        "azure_user_id": current_user.user_id,
        "name": current_user.name,
        "email": current_user.email,
        "roles": current_user.roles
    }

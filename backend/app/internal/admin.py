from fastapi import APIRouter, Depends

from ..dependencies import get_current_user
from ..auth_models import AuthUser

router = APIRouter()


@router.post("/")
async def update_admin(current_user: AuthUser = Depends(get_current_user)):
    return {
        "message": "Admin getting schwifty",
        "admin_user": current_user.email
    }

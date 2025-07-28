from pydantic import BaseModel


class AuthUser(BaseModel):
    """User model for authenticated users from Easy Auth"""
    user_id: str
    name: str
    email: str
    roles: list[str] = []

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from pydantic import EmailStr


class UserBase(SQLModel):
    """Base user model with common fields"""
    name: str
    email: EmailStr
    is_active: bool = True


class User(UserBase, table=True):
    """User database model"""
    id: Optional[int] = Field(default=None, primary_key=True)
    azure_user_id: str = Field(unique=True, index=True)  # Azure AD user ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    items: List["Item"] = Relationship(back_populates="owner")


class UserCreate(UserBase):
    """User creation model"""
    azure_user_id: str


class UserRead(UserBase):
    """User read model"""
    id: int
    azure_user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserUpdate(SQLModel):
    """User update model"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class ItemBase(SQLModel):
    """Base item model with common fields"""
    title: str
    description: Optional[str] = None
    is_public: bool = False


class Item(ItemBase, table=True):
    """Item database model"""
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    owner: Optional[User] = Relationship(back_populates="items")


class ItemCreate(ItemBase):
    """Item creation model"""
    pass


class ItemRead(ItemBase):
    """Item read model"""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class ItemUpdate(SQLModel):
    """Item update model"""
    title: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
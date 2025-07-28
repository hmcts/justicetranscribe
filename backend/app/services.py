from sqlmodel import Session, select
from .models import User, UserCreate, UserUpdate, Item, ItemCreate, ItemUpdate
from typing import Optional, List
from datetime import datetime
from .auth_models import AuthUser

class UserService:
    """Service for user-related database operations"""
    
    @staticmethod
    def get_user_by_azure_id(session: Session, azure_user_id: str) -> Optional[User]:
        """Get user by Azure AD user ID"""
        statement = select(User).where(User.azure_user_id == azure_user_id)
        return session.exec(statement).first()
    
    @staticmethod
    def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
        """Get user by database ID"""
        return session.get(User, user_id)
    
    @staticmethod
    def create_user(session: Session, user_create: UserCreate) -> User:
        """Create a new user"""
        db_user = User.model_validate(user_create)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user
    
    @staticmethod
    def update_user(session: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """Update an existing user"""
        db_user = session.get(User, user_id)
        if not db_user:
            return None
        
        user_data = user_update.model_dump(exclude_unset=True)
        for field, value in user_data.items():
            setattr(db_user, field, value)
        
        db_user.updated_at = datetime.utcnow()
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user
    
    @staticmethod
    def get_or_create_user(session: Session, auth_user: AuthUser) -> User:
        """Get existing user or create new one from auth info"""
        # Try to find existing user
        db_user = UserService.get_user_by_azure_id(session, auth_user.user_id)
        
        if db_user:
            # Update user info in case it changed
            update_data = UserUpdate(
                name=auth_user.name,
                email=auth_user.email
            )
            return UserService.update_user(session, db_user.id, update_data)
        else:
            # Create new user
            user_create = UserCreate(
                name=auth_user.name,
                email=auth_user.email,
                azure_user_id=auth_user.user_id
            )
            return UserService.create_user(session, user_create)


class ItemService:
    """Service for item-related database operations"""
    
    @staticmethod
    def get_item(session: Session, item_id: int) -> Optional[Item]:
        """Get item by ID"""
        return session.get(Item, item_id)
    
    @staticmethod
    def get_items_by_user(session: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Item]:
        """Get items owned by a specific user"""
        statement = select(Item).where(Item.owner_id == user_id).offset(skip).limit(limit)
        return list(session.exec(statement))
    
    @staticmethod
    def get_public_items(session: Session, skip: int = 0, limit: int = 100) -> List[Item]:
        """Get public items"""
        statement = select(Item).where(Item.is_public == True).offset(skip).limit(limit)
        return list(session.exec(statement))
    
    @staticmethod
    def create_item(session: Session, item_create: ItemCreate, owner_id: int) -> Item:
        """Create a new item"""
        db_item = Item(**item_create.model_dump(), owner_id=owner_id)
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
        return db_item
    
    @staticmethod
    def update_item(session: Session, item_id: int, item_update: ItemUpdate, user_id: int) -> Optional[Item]:
        """Update an existing item (only if owned by user)"""
        db_item = session.get(Item, item_id)
        if not db_item or db_item.owner_id != user_id:
            return None
        
        item_data = item_update.model_dump(exclude_unset=True)
        for field, value in item_data.items():
            setattr(db_item, field, value)
        
        db_item.updated_at = datetime.utcnow()
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
        return db_item
    
    @staticmethod
    def delete_item(session: Session, item_id: int, user_id: int) -> bool:
        """Delete an item (only if owned by user)"""
        db_item = session.get(Item, item_id)
        if not db_item or db_item.owner_id != user_id:
            return False
        
        session.delete(db_item)
        session.commit()
        return True
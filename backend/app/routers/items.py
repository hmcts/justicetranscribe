from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List

from ..dependencies import get_current_user, get_current_db_user
from ..database import get_session
from ..models import ItemCreate, ItemRead, ItemUpdate
from ..services import ItemService, UserService
from ..auth_models import AuthUser

router = APIRouter(
    prefix="/items",
    tags=["items"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[ItemRead])
async def read_items(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_db_user = Depends(get_current_db_user)
):
    """Get items owned by the current user"""
    items = ItemService.get_items_by_user(session, current_db_user.id, skip=skip, limit=limit)
    return items


@router.get("/public", response_model=List[ItemRead])
async def read_public_items(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get public items"""
    items = ItemService.get_public_items(session, skip=skip, limit=limit)
    return items


@router.get("/{item_id}", response_model=ItemRead)
async def read_item(
    item_id: int,
    session: Session = Depends(get_session),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get a specific item by ID"""
    item = ItemService.get_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check if user can access this item (owner or public)
    current_db_user = UserService.get_user_by_azure_id(session, current_user.user_id)
    if not current_db_user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if item.owner_id != current_db_user.id and not item.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return item


@router.post("/", response_model=ItemRead)
async def create_item(
    item: ItemCreate,
    session: Session = Depends(get_session),
    current_db_user = Depends(get_current_db_user)
):
    """Create a new item"""
    return ItemService.create_item(session, item, current_db_user.id)


@router.put("/{item_id}", response_model=ItemRead)
async def update_item(
    item_id: int,
    item_update: ItemUpdate,
    session: Session = Depends(get_session),
    current_db_user = Depends(get_current_db_user)
):
    """Update an existing item"""
    updated_item = ItemService.update_item(session, item_id, item_update, current_db_user.id)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Item not found or access denied")
    return updated_item


@router.delete("/{item_id}")
async def delete_item(
    item_id: int,
    session: Session = Depends(get_session),
    current_db_user = Depends(get_current_db_user)
):
    """Delete an item"""
    success = ItemService.delete_item(session, item_id, current_db_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found or access denied")
    return {"message": "Item deleted successfully"}

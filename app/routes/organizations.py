from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import User, Organization, UserRole
from ..schemas import (
    OrganizationResponse, OrganizationUpdate, 
    UserResponse, UserCreate, UserUpdate
)
from ..auth import get_current_user, require_admin, get_password_hash

router = APIRouter(prefix="/api/organizations", tags=["Organizations"])

@router.get("/me", response_model=OrganizationResponse)
async def get_my_organization(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's organization"""
    org = db.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).first()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return OrganizationResponse.model_validate(org)

@router.put("/me", response_model=OrganizationResponse)
async def update_my_organization(
    updates: OrganizationUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update organization details (admin only)"""
    org = db.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).first()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(org, field, value)
    
    db.commit()
    db.refresh(org)
    
    return OrganizationResponse.model_validate(org)

@router.get("/users", response_model=List[UserResponse])
async def list_organization_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all users in the organization"""
    users = db.query(User).filter(
        User.organization_id == current_user.organization_id
    ).all()
    
    return [UserResponse.model_validate(u) for u in users]

@router.post("/users", response_model=UserResponse)
async def add_organization_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Add a new user to the organization (admin only)"""
    # Check if email exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        organization_id=current_user.organization_id,
        role=user_data.role.value,
        status="active"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse.model_validate(user)

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_organization_user(
    user_id: str,
    updates: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a user in the organization (admin only)"""
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == current_user.organization_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    for field, value in updates.model_dump(exclude_unset=True).items():
        if field == "role" and value:
            setattr(user, field, value.value)
        else:
            setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return UserResponse.model_validate(user)

@router.delete("/users/{user_id}")
async def remove_organization_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Remove a user from the organization (admin only)"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself"
        )
    
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == current_user.organization_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "User removed successfully"}

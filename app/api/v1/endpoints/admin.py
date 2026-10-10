from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.session import get_db
from app.authentication.dependencies import get_current_admin
from app.models.user import User
from app.core.config import settings

router = APIRouter(prefix="/admin", tags=["Admin"])

class RoleUpdate(BaseModel):
    role: str

@router.patch("/users/{user_id}/role", response_model=None)
def update_user_role(
    user_id: int,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Update a user's role. Only accessible by administrators.
    Enforces a limit on the total number of admins.
    """
    target_user = db.query(User).filter(User.id == user_id).first()

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    new_role = role_data.role

    if new_role == "admin":
        # Check current admin count
        admin_count = db.query(User).filter(User.role == "admin").count()

        if admin_count >= settings.MAX_ADMINS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum number of administrators ({settings.MAX_ADMINS}) reached."
            )

    target_user.role = new_role
    db.commit()
    db.refresh(target_user)

    return {"message": f"User {target_user.username} role updated to {new_role} successfully."}

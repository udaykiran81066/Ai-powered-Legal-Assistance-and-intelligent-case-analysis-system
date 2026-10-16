from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.schemas import UserOut
from app.db.models import User

router = APIRouter()


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user

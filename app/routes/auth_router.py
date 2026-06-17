from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user_schemas import UserCreate, UserResponse
from app.schemas.provider_schemas import ProviderCreate, ProviderResponse
from app.services.auth_service import AuthService
from app.services.provider_service import ProviderService

router = APIRouter(prefix="/auth", tags=["Authentication & Profiles"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_new_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Naujo vartotojo registracija."""
    try:
        new_user = AuthService.register_user(db, user_data=user_in)
        return new_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upgrade-to-provider", response_model=ProviderResponse)
def upgrade_user_to_provider(provider_in: ProviderCreate, db: Session = Depends(get_db)):
    """Esamo vartotojo pavertimas paslaugų teikėju (sukuriant jo profilį)."""
    try:
        new_provider = ProviderService.upgrade_to_provider(db, provider_data=provider_in)
        return new_provider
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
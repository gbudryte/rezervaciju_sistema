# app/services/provider_service.py
from sqlalchemy.orm import Session
from app.models.models import User, Provider, UserRole
from app.schemas.provider_schemas import ProviderCreate

class ProviderService:

    @staticmethod
    def upgrade_to_provider(db: Session, provider_data: ProviderCreate) -> Provider:
        """Paverčia esamą vartotoją paslaugų teikėju."""
        
        # 1. Surandame vartotoją pagal ID
        user = db.query(User).filter(User.id == provider_data.user_id).first()
        if not user:
            raise ValueError("Vartotojas nerastas.")

        if user.role == UserRole.PROVIDER:
            raise ValueError("Šis vartotojas jau yra paslaugų teikėjas.")
        user.role = UserRole.PROVIDER

        db_provider = Provider(
            user_id=user.id,
            location=provider_data.location
        )
        
        # Kadangi tai SQLAlchemy, db.add() ir db.commit() išsaugos abu pakeitimus:
        # Ir vartotojo rolės UPDATE, ir naujo teikėjo INSERT!
        db.add(db_provider)
        db.commit()
        db.refresh(db_provider)
        
        return db_provider
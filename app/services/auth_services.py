from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.models.models import User
from app.schemas.user_schemas import UserCreate

# Nustatome passlib naudoti bcrypt algoritmą slaptažodžių hash'avimui
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Užkoduoja atvirą slaptažodį į hash tekstą."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Patikrina, ar prisijungimo metu įvestas slaptažodis sutampa su esančiu DB."""
        return pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def register_user(cls, db: Session, user_data: UserCreate) -> User:
        """Verslo logika naujo vartotojo registracijai."""
        
        # 1. Patikriname, ar vartotojas su tokiu el. paštu jau egzistuoja
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValueError("Vartotojas su tokiu el. paštu jau egzistuoja.")

        # 2. Užkoduojame slaptažodį
        hashed_pwd = cls.hash_password(user_data.password)

        # 3. Sukuriame SQLAlchemy modelio objektą
        db_user = User(
            name=user_data.name,
            surname=user_data.surname,
            email=user_data.email,
            password_hash=hashed_pwd
            # 'role' bus priskiesta automatiškai kaip 'CLIENT' pagal default reikalavimą
        )

        # 4. Įrašome į duomenų bazę per SQLAlchemy sesiją
        db.add(db_user)
        db.commit()
        db.refresh(db_user) # kad gautume DB sugeneruotą ID
        
        return db_user
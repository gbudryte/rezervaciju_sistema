import os
from datetime import datetime, timedelta, timezone
import jwt
from dotenv import load_dotenv
from fastapi import HTTPException, status, Depends
from app.models.models import User
from app.database import get_db
from sqlalchemy.orm import Session
from passlib. context import CryptContext
from fastapi.security import OAuth2PasswordBearer
# Ši eilutė nurodo FastAPI, kur ieškoti žetono, jei jo prireiks
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

load_dotenv()

# Surenkame kintamuosius tiesiai per os.getenv()
SECRET_KEY = os.getenv("JWT_SECRET_KEY",)
ALGORITHM = os.getenv("JWT_ALGORITHM")
EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

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
    
    @staticmethod
    def create_access_token(data: dict) -> str:
        """Sugeneruoja JWT žetoną su galiojimo laiku."""
        to_encode = data.copy()
        
        # Nustatome, kada žetonas nustos galioti
        expire = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        
        # Užkoduojame duomenis naudodami paslaptį ir algoritmą
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @classmethod
    def authenticate_user(cls, db: Session, email: str, password: str) -> User:
        """Patikrina el. paštą ir slaptažodį. Jei viskas gerai - grąžina User objektą."""
        user = db.query(User).filter(User.email == email).first()
        
        # Jei vartotojas nerastas
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Neteisingas el. paštas arba slaptažodis"
            )
            
        # Jei slaptažodis netinka (naudojame verify_password iš ankstesnės pamokos)
        if not cls.verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Neteisingas el. paštas arba slaptažodis"
            )
            
        return user
    
    @staticmethod
    def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
        """
        Iškoduoja JWT žetoną ir grąžina duomenų bazės User objektą.
        Jei žetonas blogas ar pasibaigęs -> iškart išmeta HTTP 401 klaidą.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nepavyko patvirtinti tapatybės (Log-in expired or invalid)",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            # 1. Iškoduojame žetoną
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub") # Atsimeni, login metu ID įrašėme po raktu "sub"
            
            if user_id is None:
                raise credentials_exception
                
        except jwt.PyJWTError:
            # Jei žetonas suklastotas, sugadintas arba pasibaigęs jo laikas
            raise credentials_exception

        # 2. Surandame vartotoją duomenų bazėje, kad įsitikintume, jog jis vis dar egzistuoja
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise credentials_exception
            
        return user
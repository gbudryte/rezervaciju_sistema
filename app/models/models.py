# app/models.py
import enum
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime, TIMESTAMP, func
from sqlalchemy.orm import relationship
from app.database import Base  

class UserRole(str, enum.Enum):
    CLIENT = "CLIENT"
    PROVIDER = "PROVIDER"
    ADMIN = "ADMIN"


# 2. VARTOTOJO MODELIS (users lentelė)
class User(Base):
    __tablename__ = "users"  # Tikslus lentelės pavadinimas duomenų bazėje

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(55), nullable=False)
    surname = Column(String(55), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CLIENT)

    # RYŠIAI (Relationships): Jie neegzistuoja pačioje DB, jie skirti tik SQLAlchemy magijai kode.
    
    # uselist=False reiškia „One-to-One“ ryšį. Vartotojas gali turėti tik 1 teikėjo profilį.
    provider_profile = relationship("Provider", uselist=False, back_populates="user", cascade="all, delete-orphan")
    
    # Vartotojas (klientas) gali turėti daug rezervacijų (One-to-Many).
    reservations = relationship("Reservation", back_populates="client", cascade="all, delete-orphan")


# 3. PASLAUGŲ TEIKĖJO MODELIS (providers lentelė)
class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Uždedame ForeignKey ryšį su users lentelės id stulpeliu. 
    # ondelete="CASCADE" atitinka mūsų SQL taisyklę ON DELETE CASCADE.
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    location = Column(String(200), nullable=True)

    # Susiejame atgal su User modeliu
    user = relationship("User", back_populates="provider_profile")
    # Teikėjas gali turėti daug klientų rezervacijų
    reservations = relationship("Reservation", back_populates="provider", cascade="all, delete-orphan")


# 4. REZERVACIJOS MODELIS (reservations lentelė)
class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Ryšys su klientu (kuris yra User lentelėje)
    client_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Ryšys su teikėju (kuris yra Provider lentelėje)
    provider_id = Column(Integer, ForeignKey("providers.id", ondelete="CASCADE"), nullable=False)
    
    reservation_time = Column(DateTime, nullable=False)
    reservation_type = Column(String(150), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    
    # server_default=func.now() pasako MySQL pačiai įrašyti dabartinį laiką (DEFAULT CURRENT_TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # RYŠIAI: Štai kas sutaupys daugiausiai laiko!
    # Kai turėsi rezervacijos objektą `res`, galėsi rašyti: res.client.name arba res.provider.location
    client = relationship("User", back_populates="reservations")
    provider = relationship("Provider", back_populates="reservations")
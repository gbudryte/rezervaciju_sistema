# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models.models import User, Reservation

# 1. Paruošiame laikiną SQLite duomenų bazę atmintyje TIK testams
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Sukuriame funkciją, kuri pakeis tikrąjį get_db mūsų testų metu
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Pakeičiame FastAPI priklausomybę į mūsų testinę duomenų bazę
app.dependency_overrides[get_db] = override_get_db

# Sukuriame testinį klientą, per kurį siųsime užklausas
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    """Ši funkcija prieš kiekvieną testą sukuria tuščias lenteles, o po testo jas ištrina."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)



# --- PATYS TESTAI ---

def test_user_registration_and_login_success():
    """
    Testo scenarijus:
    1. Užregistruojame naują vartotoją.
    2. Tikriname, ar API grąžina teisingą statuso kodą (201) ir vartotojo el. paštą.
    3. Bandome prisijungti su ką tik sukurtais duomenimis.
    4. Tikriname, ar sėkmingai gauname JWT access_token.
    """
    
    # Kūnas registracijai
    user_data = {
        "email": "test@example.com",
        "password": "SaugusSlaptazodis123",
        "name": "Test",
        "surname": "Vartotojas"
    }

    # 1. Vykdome registraciją
    reg_response = client.post("/auth/register", json=user_data)
    
    # Tikriname, ar gavome 201 Created kodą
    assert reg_response.status_code == 201
    # Tikriname, ar atsake yra teisingas el. paštas
    assert reg_response.json()["email"] == "test@example.com"

    # 2. Vykdome prisijungimą (FastAPI OAuth2PasswordRequestForm reikalauja form-data formato)
    login_data = {
        "username": "test@example.com",
        "password": "SaugusSlaptazodis123"
    }
    login_response = client.post("/auth/login", data=login_data)

    # Tikriname, ar prisijungimas pavyko (200 OK)
    assert login_response.status_code == 200
    # Tikriname, ar gavome JWT žetoną ir jo tipas yra 'bearer'
    assert "access_token" in login_response.json()
    assert login_response.json()["token_type"] == "bearer"


def test_login_fails_with_wrong_password():
    """Testuojame neigiamą scenarijų: prisijungimas turi nepavykti su blogu slaptažodžiu."""
    # Pirmiausia užregistruojame vartotoją
    user_data = {
        "email": "fail@example.com",
        "password": "TeisingasSlaptazodis",
        "name": "Niekas",
        "surname": "Niekaitis"
    }
    client.post("/auth/register", json=user_data)

    # Bandome jungtis su BLOGU slaptažodžiu
    login_data = {
        "username": "fail@example.com",
        "password": "BlogasSlaptazodis"
    }
    login_response = client.post("/auth/login", data=login_data)

    # Sistema privalo grąžinti 401 Unauthorized klaidą
    assert login_response.status_code == 401
    assert login_response.json()["detail"] == "Neteisingas el. paštas arba slaptažodis"
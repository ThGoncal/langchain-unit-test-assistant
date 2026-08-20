"""
API d'authentification — src/api/authentification/

Fournit :
- POST /signup : inscription d'un nouvel utilisateur
- POST /login  : connexion, renvoie un JWT
- GET  /me     : renvoie l'identité de l'utilisateur courant à partir du JWT.
                  C'est cette route que l'API principale (main.py) appelle en
                  HTTP pour valider un token, plutôt que de décoder le JWT
                  elle-même.

La base de données est simulée par un dictionnaire en mémoire (fake_users_db).
Les mots de passe ne sont jamais stockés ni comparés en clair : hash bcrypt à
l'inscription, vérification via bcrypt.checkpw() à la connexion.
"""

import os
import time

import bcrypt
import jwt
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_SECONDS = 600  # 10 minutes

app = FastAPI(title="Authentification API")

# Base "simulée" : dictionnaire en mémoire, clé = username
fake_users_db: dict = {}


# --------------------------------------------------------------------------
# Schémas Pydantic
# --------------------------------------------------------------------------

class UserSignup(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class User(BaseModel):
    """Identité minimale exposée aux autres services (via /me)."""
    username: str


# --------------------------------------------------------------------------
# Sécurité : hash des mots de passe
# --------------------------------------------------------------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


# --------------------------------------------------------------------------
# JWT : émission et vérification
# --------------------------------------------------------------------------

def sign_jwt(username: str) -> TokenResponse:
    payload = {"sub": username, "exp": time.time() + JWT_EXPIRATION_SECONDS}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return TokenResponse(access_token=token)


def decode_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalide")
    return payload


class JWTBearer(HTTPBearer):
    """Garde d'accès réutilisable pour protéger une route via le JWT."""

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> str:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if credentials.scheme != "Bearer":
            raise HTTPException(status_code=403, detail="Schéma d'authentification invalide")
        payload = decode_jwt(credentials.credentials)
        return payload["sub"]  # username


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

@app.post("/signup")
def signup(user: UserSignup):
    """
    Inscrit un nouvel utilisateur.

    Raises:
    - HTTPException(400): si le nom d'utilisateur existe déjà.
    """
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce nom d'utilisateur existe déjà",
        )

    fake_users_db[user.username] = {
        "username": user.username,
        "hashed_password": hash_password(user.password),
    }
    return {"username": user.username}


@app.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin):
    """
    Vérifie les identifiants et renvoie un jeton d'accès.

    Raises:
    - HTTPException(401): identifiants invalides (même message dans les deux
      cas pour ne pas révéler si un username existe).
    """
    user = fake_users_db.get(credentials.username)
    if not user or not check_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
        )
    return sign_jwt(credentials.username)


@app.get("/me", response_model=User)
def get_current_user(username: str = Depends(JWTBearer())):
    """
    Renvoie l'identité de l'utilisateur courant à partir du JWT.
    Appelée en HTTP par l'API principale pour valider un token reçu.
    """
    user = fake_users_db.get(username)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return User(username=user["username"])
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import authenticate, create_access_token, get_current_user
from app.schemas import auth as auth_schemas

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=auth_schemas.LoginResponse)
def login(payload: auth_schemas.LoginRequest):
    user = authenticate(payload.username.strip(), payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"token": create_access_token(user["username"]), "user": user}


@router.get("/me", response_model=auth_schemas.UserResponse)
def me(user: dict = Depends(get_current_user)):
    return user

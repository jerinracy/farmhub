import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config import settings
from app.schemas import CurrentUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8000/api/auth/login/")


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("id") or payload.get("user_id")
        username = payload.get("username")
        role = payload.get("role")

        if user_id is None or username is None or role is None:
            raise credentials_exception

        return CurrentUser(
            id=int(user_id),
            username=str(username),
            role=str(role),
        )
    except Exception:
        raise credentials_exception

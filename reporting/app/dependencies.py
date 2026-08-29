from fastapi import Depends, HTTPException, status

from app.auth import CurrentUser, get_current_user


def require_role(*roles: str):
    def role_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted",
            )
        return current_user

    return role_checker


require_superadmin = require_role("SUPERADMIN")

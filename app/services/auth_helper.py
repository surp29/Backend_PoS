"""
Helper functions để lấy thông tin user từ JWT token
"""
from fastapi import Request
from typing import Optional
import jwt
from ..config import Config

SECRET_KEY = Config.JWT_SECRET_KEY
ALGORITHM = "HS256"


def get_username_from_request(request: Request) -> Optional[str]:
    """
    Lấy username từ Authorization header trong Request.
    Trả về None nếu không có token hoặc token không hợp lệ.
    """
    try:
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None
        
        # Lấy token từ "Bearer <token>"
        if authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
        else:
            token = authorization
        
        # Decode token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        return username
        
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, Exception):
        return None


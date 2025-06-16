from datetime import timedelta, datetime
from jose import jwt, JWTError

SECRET_KEY = "change-me-to-a-long-random-string"
ALGORITHM  = "HS256"
ACCESS_TTL = timedelta(hours=8)          # how long tokens stay valid


def create_access_token(data: dict, expires_delta: timedelta = ACCESS_TTL) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + expires_delta
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as e:
        raise ValueError("Invalid token") from e
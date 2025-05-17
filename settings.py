from datetime import timedelta
from pathlib import Path
from pydantic import BaseModel


BASE_DIR = Path(__file__).parent
USING_SQLITE_INSTEAD_OF_BIG_DB = True


class App(BaseModel):
    HOST: str = 'localhost'
    PORT: int = 8004


class AuthJWT(BaseModel):
    private_key_path: Path = BASE_DIR / 'auth' / 'private_key.pem'
    public_key_path: Path = BASE_DIR / 'auth' / 'public_key.pem'
    algorithm: str = 'RS256'
    ACCESS_JWT_COOKIE_NAME: str = 'ACCESS_JWT_cookie'
    REFRESH_JWT_COOKIE_NAME: str = 'REFRESH_JWT_cookie'
    REFRESH_JWT_HEADER_NAME: str = 'X-Refresh-Token'
    ACCESS_TOKEN_REFRESH: timedelta = timedelta(minutes=32)
    ACCESS_TOKEN_LIVE: timedelta = timedelta(minutes=33)
    REFRESH_TOKEN_LIVE: timedelta = timedelta(days=7)


app_settings = App()
auth_jwt = AuthJWT()


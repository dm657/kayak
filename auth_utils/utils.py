from datetime import datetime, UTC
from typing import Any

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

import jwt
from jwt import PyJWK

import bcrypt

from settings import auth_jwt, BASE_DIR
import os
from dotenv import load_dotenv


load_dotenv()
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
PUBLIC_KEY = os.getenv('PUBLIC_KEY')


def encode_jwt(
    payload: dict[str, Any],
    key: PyJWK | str | bytes | None = None,  # default value set here, when func declared
    algorithm: str | None = auth_jwt.algorithm,
):
    if key is None:  # reading file only when func called. no FileNotExist err
        # key = auth_jwt.private_key_path.read_text()
        key = PRIVATE_KEY
    encoded = jwt.encode(payload=payload, key=key, algorithm=algorithm)
    return encoded


def decode_jwt(
        token: str | bytes,
        key: str | None = None,
        algorithm: str = auth_jwt.algorithm,
):
    if key is None:
        # key = auth_jwt.public_key_path.read_text()
        key = PUBLIC_KEY
    decoded = jwt.decode(token, key, algorithm)
    return decoded


def hash_password(password: str) -> bytes:
    salt = bcrypt.gensalt()
    pwd_bytes: bytes = password.encode()
    return bcrypt.hashpw(pwd_bytes, salt)


def validate_password(
        password: str,
        hashed_password: bytes
) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password)


def convert_datetimes_to_timestamps(payload: dict) -> dict:
    return {k: int(v.timestamp()) if isinstance(v, datetime) else v for k, v in payload.items()}


def create_access_or_refresh_token(token_type: str):
    def create_token(payload: dict):
        payload['sub'] = str(payload['user_id'])
        payload['exp'] = datetime.now(UTC) + auth_jwt.__getattribute__(f'{token_type}_TOKEN_LIVE')
        payload['type'] = token_type
        if token_type == 'ACCESS':
            payload['refresh_after'] = datetime.now(UTC) + auth_jwt.__getattribute__(f'{token_type}_TOKEN_REFRESH')

        return encode_jwt(convert_datetimes_to_timestamps(payload))
    return create_token


if __name__ == '__main__':
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with open(f"{BASE_DIR}/auth/private_key.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    public_key = private_key.public_key()

    print(public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ))

    with open(f"{BASE_DIR}/auth/public_key.pem", "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

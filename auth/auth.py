from typing import Annotated

from fastapi import FastAPI, APIRouter, Request, Response, Depends, HTTPException, status, Form, Header

import settings
from schemas import CreateUser, JWTToken, User, HandleAnswer

from starlette.responses import HTMLResponse, RedirectResponse
from fastapi.security import (HTTPBasic, HTTPBasicCredentials,
                              HTTPBearer, HTTPAuthorizationCredentials,
                              OAuth2PasswordBearer)
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from cruds import get_user_by_login, create_user as async_create_user
from auth_utils import (decode_jwt,
                        validate_password,
                        create_access_or_refresh_token)

from templ import templates

from fastapi.staticfiles import StaticFiles

http_bearer = HTTPBearer(auto_error=True)  # take token from header, 400 if no token
oauth_schema = OAuth2PasswordBearer(tokenUrl='/auth/login/')

app = FastAPI(title='auth_app')
router = APIRouter(prefix='/auth', tags=['basic auth'])

app.mount("/static", StaticFiles(directory=f"{settings.BASE_DIR}/static"), name="static")

security = HTTPBasic()


def validate_auth_user(
        username: str = Form(),
        password: str = Form(),
):
    return HTTPBasicCredentials(username=username, password=password)


async def get_user_data_from_db_by_username(
        username: Annotated[str, Depends()], exclude_password=False) -> dict | None:
    user: User = await get_user_by_login(username)
    if not user:
        return None
    user_dict = user.model_dump(exclude={(None, 'password')[exclude_password]})
    return user_dict


async def get_user_payload_from_db(
        credentials: Annotated[HTTPBasicCredentials, Depends(validate_auth_user)]) -> dict:
    user_dict = await get_user_data_from_db_by_username(credentials.username)
    if not (user_dict and validate_password(credentials.password, user_dict['password'])):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    if user_dict.get('status') == 'blocked':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='user inactive')
    print(f'{user_dict=}')
    del user_dict['password']
    return user_dict


async def make_access_by_refresh(refresh: str) -> str:
    try:
        payload = decode_jwt(refresh)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='invalid token')
    if payload['type'] != 'REFRESH':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='invalid token')

    payload_from_db = await get_user_data_from_db_by_username(payload['username'], exclude_password=True)
    access_token = create_access_or_refresh_token('ACCESS')(payload_from_db)
    return access_token


class TokenVerifier:
    def __init__(self, check_status: list[str] = None, show_user_id: bool = False):
        self.check_status_list = check_status
        self.show_user_id = show_user_id

    async def __call__(self,
                       authorization_creds: HTTPAuthorizationCredentials = Depends(http_bearer),
                       request: Request = None,
                       ) -> JWTToken:
        result = JWTToken()
        try:
            token = authorization_creds.credentials
            payload = decode_jwt(token)

        except ExpiredSignatureError as e:
            print('token expired    ===>>>   ', e)
            refresh_token = request.headers.get(settings.auth_jwt.REFRESH_JWT_HEADER_NAME)
            if not refresh_token:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
            new_access = await make_access_by_refresh(refresh_token)
            payload = decode_jwt(new_access)
            result.access_token = new_access

        if self.check_status_list and payload.get('status') not in self.check_status_list:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='you have no access here')
        if self.show_user_id:
            result.user_id = payload.get('user_id')

        return result


@router.post('/login')
def auth_with_making_jwt_tokens(response: Response,
                                payload: Annotated[dict, Depends(get_user_payload_from_db)]):
    access_token = create_access_or_refresh_token('ACCESS')(payload)
    refresh_token = create_access_or_refresh_token('REFRESH')(payload)

    return JWTToken(
        access_token=access_token,
        refresh_token=refresh_token,
    )
    # response.set_cookie(
    #     key=settings.auth_jwt.ACCESS_JWT_COOKIE_NAME,
    #     value=access_token,
    #     httponly=True,  # Защита от XSS
    #     secure=True,  # Только HTTPS
    #     samesite="strict"  # Защита от CSRF
    # )
    # response.set_cookie(
    #     key=settings.auth_jwt.REFRESH_JWT_COOKIE_NAME,
    #     value=refresh_token,
    #     httponly=True,
    #     secure=True,
    #     samesite="strict"
    # )


@router.post('/refresh')
async def refresh_token(refresh: Annotated[str | None, Header(alias="X-Refresh-Token")]) -> JWTToken:
    access_token = await make_access_by_refresh(refresh)
    return JWTToken(access_token=access_token)


@router.get('/logout')  # ToDo: rework
def logout_by_del_cookie(response: Response):
    response.delete_cookie(key=settings.auth_jwt.REFRESH_JWT_COOKIE_NAME)
    response.delete_cookie(key=settings.auth_jwt.ACCESS_JWT_COOKIE_NAME)
    return RedirectResponse(url="/auth/login", headers=response.headers)


# def get_token_payload_from_cookie(token_cookie_name: str, request: Request) -> dict:
#     token = request.cookies.get(token_cookie_name)
#     if token:
#         return decode_jwt(token)
#     else:
#         raise InvalidTokenError
#
#
# async def check_or_refresh_the_access_token(response: Response, request: Request):
#     try:
#         payload = get_token_payload_from_cookie(token_cookie_name=settings.auth_jwt.ACCESS_JWT_COOKIE_NAME,
#                                                 request=request)
#         print(f' try_1: {payload=}')
#     except InvalidTokenError:
#         try:
#             payload = get_token_payload_from_cookie(token_cookie_name=settings.auth_jwt.REFRESH_JWT_COOKIE_NAME,
#                                                     request=request)
#             user = await get_user_by_login(payload['username'])
#             payload = await get_user_payload_from_db()
#
#             access_token = create_access_or_refresh_token('ACCESS')(user.model_dump(exclude={'password'}))
#
#             response.set_cookie(
#                 key=settings.auth_jwt.ACCESS_JWT_COOKIE_NAME,
#                 value=access_token,
#                 httponly=True,  # Защита от XSS
#                 secure=True,  # Только HTTPS
#                 samesite="strict"  # Защита от CSRF
#             )
#             return payload
#
#         except InvalidTokenError:
#             return None
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='invalid token')
#         access_token = create_access_or_refresh_token('ACCESS')(payload)
#
#         print(f'\nСоздание access')
#         response.set_cookie(
#             key=settings.auth_jwt.ACCESS_JWT_COOKIE_NAME,
#             value=access_token,
#             httponly=True,  # Защита от XSS
#             secure=True,  # Только HTTPS
#             samesite="strict"  # Защита от CSRF
#         )
#     print(f'{payload=}')
#     return payload
#
#
# def check_token_if_admin(token_payload=Depends(check_or_refresh_the_access_token)):
#     if token_payload and token_payload.get('status') == 'admin':
#         return token_payload
#     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


@router.get('/login', response_class=HTMLResponse)
def show_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get('/create-user', status_code=status.HTTP_200_OK)
def show_create_user(request: Request):
    return templates.TemplateResponse("create-user.html", {"request": request})


@router.post('/create-user', status_code=status.HTTP_201_CREATED, response_model=HandleAnswer)
async def create_user(user: CreateUser, ):
    try:
        await async_create_user(user=user)
    except ValueError as err:
        return {'result': 'fail', 'message': f'{err}'}
    else:
        return {'result': 'ok', 'message': f'user with {user.username=}created'}


@router.get('/me')
def get_payload(request: Request, jwt_token=Depends(TokenVerifier())):
    print(f'{jwt_token=}')
    return templates.TemplateResponse("base.html", {"request": request, "jwt_token": jwt_token})


app.include_router(router)

if __name__ == '__main__':
    pass
    # token_dep = TokenVerifier()

    # uvicorn.run(app='auth:app', port=8002, reload=True)

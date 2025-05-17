from typing import Annotated

from fastapi import APIRouter, Request, Depends, status

import cruds
from auth import TokenVerifier
from schemas import BaseUserData, JWTToken, Option
from templ import templates

router = APIRouter(prefix='/administrate', tags=['Administrating tool'])


@router.get('/')
def show_admin_page(request: Request):
    return templates.TemplateResponse('administrate.html', {'request': request})


@router.get('/get-users-list')
async def get_users_list(jwt_token: Annotated[JWTToken, Depends(TokenVerifier(check_status=['admin']))]):
    result = await cruds.get_users_list()
    return {'jwt_token': jwt_token.model_dump(exclude_none=True), 'result': result}


@router.post('/edit_users_statuses', status_code=status.HTTP_200_OK)
async def edit_user_status(statuses: list[BaseUserData],
                           jwt_token: Annotated[JWTToken, Depends(TokenVerifier(check_status=['admin']))]):
    result = await cruds.edit_user_status(statuses)
    return {'jwt_token': jwt_token.model_dump(exclude_none=True), 'result': result}


@router.get('/get-options-list')
async def get_users_list(jwt_token: Annotated[JWTToken, Depends(TokenVerifier(check_status=['admin']))]):
    result = await cruds.get_all_options()
    print(result)
    return {'jwt_token': jwt_token.model_dump(exclude_none=True), 'result': result}


@router.post('/edit-option')
async def edit_option(option: Option,
                      jwt_token: Annotated[JWTToken, Depends(TokenVerifier(check_status=['admin']))]):
    await cruds.rename_option(option)
    return {'jwt_token': jwt_token.model_dump(exclude_none=True), 'result': 'Ok'}


@router.delete('/delete-option')
async def delete_option(option_id: int,
                        jwt_token: Annotated[JWTToken, Depends(TokenVerifier(check_status=['admin']))]):
    await cruds.delete_option(option_id)
    return {'jwt_token': jwt_token.model_dump(exclude_none=True), 'result': 'Ok'}

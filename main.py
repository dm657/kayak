from typing import Annotated

import uvicorn
from fastapi import FastAPI, Request, status, Depends, HTTPException
from fastapi.staticfiles import StaticFiles

import cruds
from admining import router as admin_router
from auth import router as auth_router, TokenVerifier
from graph import graph_builder, compute_pagerank
from schemas import JWTToken, AddOption, Option, OptionsList
from settings import app_settings
from templ import templates

app = FastAPI(summary='Lite kayak')
app.mount('/static', StaticFiles(directory='static'), name='static')
app.include_router(auth_router)
app.include_router(admin_router)


@app.get('/add-option', status_code=status.HTTP_200_OK)
def show_add_option(request: Request, ):
    return templates.TemplateResponse('add-option.html', {'request': request})


@app.post('/add-option', status_code=status.HTTP_201_CREATED)
async def add_option(option: AddOption,
                     jwt_token: Annotated[JWTToken, Depends(TokenVerifier())]):
    res = await cruds.add_option(option)
    return {'jwt_token': jwt_token.model_dump(exclude_none=True)} | res


@app.get('/approve-options', status_code=status.HTTP_200_OK)
def show_add_option(request: Request, ):
    return templates.TemplateResponse('approve-options.html', {'request': request})


@app.get('/get-options-to-approve', status_code=status.HTTP_200_OK)
async def get_options_to_approve(jwt_token: Annotated[JWTToken,
                                 Depends(TokenVerifier(check_status=['superuser', 'admin']))]):
    options = await cruds.get_options_to_approve()
    return {'jwt_token': jwt_token.model_dump(exclude_none=True), 'options': options}


@app.post('/approve-options', status_code=status.HTTP_201_CREATED)
async def approve_options(options_to_add: OptionsList, options_to_del: OptionsList,
                          jwt_token: Annotated[JWTToken,
                          Depends(TokenVerifier(check_status=['superuser', 'admin']))]):
    res = await cruds.approve_options(options_to_add.options, options_to_del.options)
    return {'jwt_token': jwt_token.model_dump(exclude_none=True)} | res


@app.get('/rank-variants', status_code=status.HTTP_200_OK)
def show_rank_variants(request: Request):
    return templates.TemplateResponse('rank-variants.html', {'request': request})


@app.get('/get-options-to-rank', status_code=status.HTTP_200_OK)
async def add_option(jwt_token:
Annotated[JWTToken, Depends(TokenVerifier())]):
    res = await cruds.get_options_to_rank()
    options = [Option(option_id=1, text='плавать на байдарке'), ]
    options.extend((Option.model_validate(o, from_attributes=True) for o in res))
    return {'jwt_token': jwt_token.model_dump(exclude_none=True), 'options': options}


@app.post('/rank-variants', status_code=status.HTTP_201_CREATED, )
async def rank_variants(options: list[int], jwt_token:
Annotated[JWTToken, Depends(TokenVerifier(show_user_id=True))]):
    await cruds.submit_answer(user_id=jwt_token.user_id, options=options)
    return {'jwt_token': jwt_token.model_dump(exclude={'user_id'}, exclude_none=True)}


@app.get('/ranked-data', status_code=status.HTTP_200_OK)
def show_ranked_data(request: Request):
    return templates.TemplateResponse('ranked-data.html', {'request': request})


@app.get('/calc-ranks', status_code=status.HTTP_200_OK)
async def calc_ranks(jwt_token: Annotated[JWTToken, Depends(TokenVerifier(show_user_id=True))],
                     user_id: int = None):
    if user_id is not None and user_id != jwt_token.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    data = await cruds.get_ranks(user_id)
    ranks = compute_pagerank(graph_builder(user_id)(data[0]))
    print(ranks)
    # return ranks
    result = {k: (v, data[1].get(k)) for k, v in ranks.items()}
    return {'jwt_token': jwt_token.model_dump(exclude={'user_id'}, exclude_none=True),
            'result': result}


if __name__ == '__main__':
    uvicorn.run(app='main:app',
                host=app_settings.HOST,
                port=app_settings.PORT,
                reload=True)

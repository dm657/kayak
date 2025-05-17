from sqlalchemy import select, insert, update, delete, func, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased
import models
from models import session_maker
from auth_utils import utils

from schemas import CreateUser, User, BaseUserData, UserData, AddOption, Option

import asyncio


async def create_user(user: CreateUser, status='blocked'):
    user.password = utils.hash_password(user.password)
    async with session_maker() as session:
        query = select(models.User).where(models.User.username == user.username)
        res = await session.execute(query)
        if res.scalar_one_or_none():
            raise ValueError('username already exist')
        elif user.email:
            query = select(models.User).where(models.User.email == user.email)
            res = await session.execute(query)
            if res.scalar_one_or_none():
                raise ValueError('email already exist')

        session.add(models.User(**user.model_dump(), status=status))
        await session.commit()
        print('user created')


async def get_user_by_login(username) -> User:
    async with session_maker() as session:
        query = select(models.User).where(models.User.username == username)
        res = await session.execute(query)
    result = res.scalar_one_or_none()
    if result:
        return User.model_validate(result, from_attributes=True)


async def get_users_list():
    async with session_maker() as session:
        res = await session.execute(select(models.User))
    result = [UserData.model_validate(r, from_attributes=True) for r in res.scalars().all()]
    return result


async def edit_user_status(statuses: list[BaseUserData]):
    async with session_maker() as session:
        for status in statuses:
            stmt = update(models.User).where(
                models.User.user_id == status.user_id).values(
                status=status.status)
            await session.execute(stmt)
        await session.commit()
    return {'message': 'Ok'}


async def add_option(option: AddOption):
    try:
        async with session_maker() as session:
            session.add(models.OptionToApprove(text=option.text))
            await session.commit()
        print(f'=======\ncrud.add_option({option.text=})')
        return {'message': 'OK'}
    except IntegrityError:
        return {'message': 'Error'}


async def get_options_to_approve():
    async with session_maker() as session:
        query = select(models.OptionToApprove)  # .option_id, models.OptionToApprove.text)
        res = await session.execute(query)
        result = res.scalars().all()
    return result


async def approve_options(options_to_add: list[int], options_to_del: list[int]):
    select_stmt = select(models.OptionToApprove.text).where(
        models.OptionToApprove.option_id.in_(options_to_add))
    insert_stmt = insert(models.Option).from_select(['text'], select_stmt)
    del_stmt = delete(models.OptionToApprove).where(models.OptionToApprove.option_id.in_(
        options_to_add + options_to_del))
    try:
        async with session_maker() as session:
            await session.execute(insert_stmt)
            await session.execute(del_stmt)
            await session.commit()
    except IntegrityError:
        return {'message': 'Error', 'detail': 'some DB error. probably not unique value'}
    return {'message': 'OK', 'detail': ''}


async def get_options_to_rank():
    """Getting 2 random options"""
    query = select(models.Option).where(models.Option.option_id > 1).order_by(func.random()).limit(2)
    async with session_maker() as session:
        res = await session.execute(query)
        result = res.scalars().all()
    return result


async def get_all_options():
    sa1 = aliased(models.SubmittedAnswer)
    sa2 = aliased(models.SubmittedAnswer)
    stmt = (
        select(
            models.Option.option_id,
            models.Option.text,
            (
                    select(func.count())
                    .where(sa1.op1 == models.Option.option_id)
                    .scalar_subquery()
                    +
                    select(func.count())
                    .where(sa2.op2 == models.Option.option_id)
                    .scalar_subquery()
            )  # .label("count_total")
        )
    )

    async with session_maker() as session:
        res = await session.execute(stmt)
    return {r[0]: [r[1], r[2]] for r in res.all()}


async def rename_option(option: Option):
    stmt = update(models.Option).where(models.Option.option_id == option.option_id).values(
        text=option.text)
    async with session_maker() as session:
        await session.execute(stmt)
        await session.commit()
    return {'message': 'Ok'}


async def delete_option(option_id: int):
    stmt = delete(models.Option).filter_by(option_id=option_id)
    async with session_maker(cascade_actions=True) as session:
        await session.execute(stmt)
        await session.commit()


async def submit_answer(user_id: int, options: list[int]):
    del_stmt = delete(models.SubmittedAnswer
                      ).where(and_(models.SubmittedAnswer.user_id == user_id,
                                   models.SubmittedAnswer.op1.in_(options),
                                   models.SubmittedAnswer.op2.in_(options))
                              )
    async with session_maker() as session:
        await session.execute(del_stmt)
        session.add(models.SubmittedAnswer(op1=options[0], op2=options[1], user_id=user_id, ))
        session.add(models.SubmittedAnswer(op1=options[0], op2=options[2], user_id=user_id, ))
        session.add(models.SubmittedAnswer(op1=options[1], op2=options[2], user_id=user_id, ))
        await session.commit()


async def get_ranks(user_id=None):
    texts_query = select(models.Option)
    if user_id is None:
        query = select(models.SubmittedAnswer.op1, models.SubmittedAnswer.op2,
                       func.count()).group_by(models.SubmittedAnswer.op1, models.SubmittedAnswer.op2)
    else:
        query = select(models.SubmittedAnswer.op1, models.SubmittedAnswer.op2).filter(
            models.SubmittedAnswer.user_id == user_id)

    async with session_maker() as session:
        res = await session.execute(query)
        result = res.all()
        res = await session.execute(texts_query)
        texts = {o.option_id: o.text for o in res.scalars().all()}

    print(result, texts)
    return result, texts


if __name__ == '__main__':
    # asyncio.run(create_user(CreateUser(username='asd4', password=b'123123'), status='admin'))
    # u = asyncio.run(get_user_by_login('asd3'))
    ranks = asyncio.run(get_ranks())
    print(ranks)
    # print(compute_pagerank(graph_builder()(ranks)))

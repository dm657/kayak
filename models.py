import os
from dotenv import load_dotenv
from settings import BASE_DIR, USING_SQLITE_INSTEAD_OF_BIG_DB

from typing import Annotated

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy import (create_engine, update, Table, Column, Integer, DECIMAL, String, LargeBinary, TIMESTAMP,
                        ForeignKey, func, text, PrimaryKeyConstraint, event)
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession, async_session, AsyncEngine
import sqlite3

from contextlib import asynccontextmanager
from fastapi import Depends


if USING_SQLITE_INSTEAD_OF_BIG_DB:
    DB_CONNECTION_PARAM = f'sqlite+aiosqlite:///{BASE_DIR}/kayak.db'
    DB_SYNC_CONNECTION_PARAM = f'sqlite:///{BASE_DIR}/kayak.db'
else:
    load_dotenv()
    DB_CONNECTION_PARAM = (os.getenv('DB_CONNECTION_PARAM'))
    DB_SYNC_CONNECTION_PARAM = os.getenv('DB_SYNC_CONNECTION_PARAM')

engine = create_async_engine(DB_CONNECTION_PARAM)
sync_engine = create_engine(DB_SYNC_CONNECTION_PARAM)


new_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
new_sync_session = sessionmaker(bind=sync_engine, expire_on_commit=False)


@asynccontextmanager
async def session_maker(cascade_actions=False) -> AsyncSession:
    async with new_session() as session:
        if USING_SQLITE_INSTEAD_OF_BIG_DB and cascade_actions:
            await session.execute(text("PRAGMA foreign_keys=ON"))
        yield session


SessionDep = Annotated[async_session, Depends(session_maker)]


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    user_id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    password: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=True, default='user')

    answer: Mapped['SubmittedAnswer'] = relationship(back_populates='user')


class OptionToApprove(Base):
    __tablename__ = "options_to_approve"
    option_id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    text: Mapped[str] = mapped_column(String, unique=True)


class Option(Base):
    __tablename__ = "options"
    option_id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    text: Mapped[str] = mapped_column(String, unique=True)

    # Указываем только таблицу, а не конкретные поля
    ref1 = relationship("SubmittedAnswer", back_populates="opt1", foreign_keys="[SubmittedAnswer.op1]")
    ref2 = relationship("SubmittedAnswer", back_populates="opt2", foreign_keys="[SubmittedAnswer.op2]")


class SubmittedAnswer(Base):
    __tablename__ = "submitted_answers"

    op1: Mapped[int] = mapped_column(Integer, ForeignKey("options.option_id", ondelete="CASCADE", onupdate="CASCADE"))
    op2: Mapped[int] = mapped_column(Integer, ForeignKey("options.option_id", ondelete="CASCADE", onupdate="CASCADE"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"))

    opt1 = relationship("Option", back_populates="ref1", foreign_keys=[op1])
    opt2 = relationship("Option", back_populates="ref2", foreign_keys=[op2])
    user: Mapped['User'] = relationship("User", back_populates="answer", foreign_keys=[user_id])

    __table_args__ = (
        PrimaryKeyConstraint("op1", "op2", "user_id", name='sa2_pk'),
    )


def setup_db():
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)
    return None


if __name__ == '__main__':
    pass
    setup_db()
    with new_sync_session() as session_:
        session_.add(Option(option_id=1, text='Плавать на байдарке'))
        session_.commit()

from abc import ABC, abstractmethod

from sqlalchemy import insert, select

from db.db import async_session_maker
from model.model import Blueprint, Citadel, MediumRig, NonProductable, Setup, User


class AbstractRepository(ABC):
    model = None

    @abstractmethod
    async def find_all(self):
        ...

    @abstractmethod
    async def add_one(self):
        ...


class SQLAlchemyRepository(AbstractRepository):
    async def add_one(self, data: dict) -> int:
        async with async_session_maker() as session:
            stmt = insert(self.model).values(**data).returning(self.model.id)
            res = await session.execute(stmt)
            await session.commit()
            return res.scalar_one()

    async def find_all(self, setup_id=None):
        async with async_session_maker() as session:
            if setup_id is None:
                stmt = select(self.model)
            else:
                stmt = select(self.model).where(self.model.setup_id == setup_id)
            res = await session.execute(stmt)
            res = [row[0].to_read_model() for row in res.all()]
            return res


class UserRepository(SQLAlchemyRepository):
    model = User

    async def find_all(self, user_id=None):
        async with async_session_maker() as session:
            if setup_id is None:
                stmt = select(self.model)
            else:
                stmt = select(self.model).where(self.model.user_id == user_id)
            res = await session.execute(stmt)
            res = [row[0].to_read_model() for row in res.all()]
            return res


class SetupRepository(SQLAlchemyRepository):
    model = Setup


class MediumRigRepository(SQLAlchemyRepository):
    model = MediumRig

    async def find_all(self, citadel_id=None):
        async with async_session_maker() as session:
            if citadel_id is None:
                stmt = select(self.model)
            else:
                stmt = select(self.model).where(self.model.citadel_id == citadel_id)
            res = await session.execute(stmt)
            res = [row[0].to_read_model() for row in res.all()]
            return res


class NonProductableRepository(SQLAlchemyRepository):
    model = NonProductable


class CitadelRepository(SQLAlchemyRepository):
    model = Citadel


class BlueprintRepository(SQLAlchemyRepository):
    model = Blueprint

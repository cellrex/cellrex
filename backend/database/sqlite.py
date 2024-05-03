"""SQLite database interface for the CellRexMetadata database"""

import os
import contextlib
import json
from typing import Any, AsyncIterator, Dict, List

from database.base import DatabaseInterface
from model.biofile import Biofile
from model.search import SearchModel
from sqlalchemy import create_engine, select, text
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

Base = declarative_base()


class SqlBiofile(Base):
    """SQL Alchemy ORM class for the biofiles table"""

    __tablename__ = "biofiles"

    _id: Mapped[int] = mapped_column(primary_key=True)
    filecontext: Mapped[str] = mapped_column()
    filepath: Mapped[str] = mapped_column(index=True, unique=True)
    filesize: Mapped[int] = mapped_column()
    filehash: Mapped[str] = mapped_column(index=True)
    filetype: Mapped[str] = mapped_column()

    def __repr__(self):
        return (
            f"<SqlBioFile(_id={self._id!r}, filecontext={self.filecontext}, "
            f"filepath={self.filepath}, filesize={self.filesize}, "
            f"filehash={self.filehash}, filetype={self.filetype})>"
        )


# Heavily inspired by
# https://praciano.com.br/fastapi-and-async-sqlalchemy-20-with-pytest-done-right.html


class InitializationError(Exception):
    pass


class DatabaseSessionManager:
    """
    DatabaseSessionManager orchestrates the creation and disposal
    of an async database engine and sessionmaker.
    """

    def __init__(self, host: str, engine_kwargs: dict[str, Any]):
        if not engine_kwargs:
            engine_kwargs = {"echo": True}
        self._engine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(autocommit=False, bind=self._engine)

    async def close(self):
        if self._engine is None:
            raise InitializationError("DatabaseSessionManager is not initialized")
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise InitializationError("DatabaseSessionManager is not initialized")
        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise InitializationError("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


sqlite_file = os.getenv(
    "DATABASE_BACKEND_SQLITE_FILE", default="data/sqlite/CellRexMetadata.sqlite"
)

sessionmanager = DatabaseSessionManager(
    f"sqlite+aiosqlite:///{sqlite_file}", {"echo": False}
)


def sqlite_orm_to_dict(orm_object):
    """Convert a SQL Alchemy ORM object to a dictionary"""
    orm_dict = orm_object.__dict__
    orm_dict.pop("_sa_instance_state")
    orm_dict["filecontext"] = json.loads(orm_dict["filecontext"])
    return orm_dict


class SQLiteDatabase(DatabaseInterface):
    """
    SQLite database interface based on the DatabaseInterface class.
    This class is used to interact with the SQLite database.
    """

    def __init__(self):
        self.engine = create_engine(f"sqlite:///{sqlite_file}")

        Base.metadata.create_all(self.engine)

        self.biofile_table = Base.metadata.tables["biofiles"]

    async def add_biofile(self, data: Biofile) -> str | None:
        """Add a new biofile into to the database"""
        data: Dict = data.model_dump(exclude_none=True)
        async with sessionmanager.session() as session:
            async with session.begin():
                # upsert if filepath already exists
                stmt = (
                    sqlite_upsert(self.biofile_table)
                    .values(
                        filecontext=json.dumps(data["filecontext"]),
                        filepath=data["filepath"],
                        filesize=data["filesize"],
                        filehash=data["filehash"],
                        filetype=data["filetype"],
                    )
                    .on_conflict_do_update(
                        index_elements=["filepath"],
                        set_=dict(
                            filecontext=json.dumps(data["filecontext"]),
                            filesize=data["filesize"],
                            filehash=data["filehash"],
                            filetype=data["filetype"],
                        ),
                    )
                    .returning(self.biofile_table.c._id)
                )
                result = await session.execute(stmt)
                biofile_id = result.scalar_one()
                if biofile_id:
                    return biofile_id

                return

    async def retrieve_biofiles(self) -> List[Dict] | None:
        """Retrieve all biofiles present in the database"""
        async with sessionmanager.session() as session:
            # for streaming ORM results, AsyncSession.stream() may be used.
            stmt = select(SqlBiofile)
            result = await session.stream(stmt)

            # result is a streaming AsyncResult object.
            biofiles = []
            async for biofile in result.scalars():
                biofiles.append(sqlite_orm_to_dict(biofile))

            return biofiles

    async def retrieve_biofile_by_id(self, biofile_id: str) -> Dict | None:
        """Retrieve a biofile with a matching ID"""
        async with sessionmanager.session() as session:
            # stmt = select(SqlBiofile, biofile_id)
            biofile = await session.get(SqlBiofile, biofile_id)

            if biofile:
                return sqlite_orm_to_dict(biofile)

    async def update_biofile_by_id(self, biofile_id: str, data: Biofile) -> Dict | None:
        """Update a biofile with a matching ID"""
        data = data.model_dump(exclude_none=True)
        if len(data) < 1:
            return

        async with sessionmanager.session() as session:
            async with session.begin():
                biofile = await session.get(SqlBiofile, biofile_id)

                if biofile:
                    biofile.filecontext = json.dumps(data["filecontext"])
                    biofile.filesize = data["filesize"]
                    biofile.filehash = data["filehash"]
                    biofile.filetype = data["filetype"]

            updated_biofile = await session.get(SqlBiofile, biofile_id)

            if updated_biofile:
                return sqlite_orm_to_dict(updated_biofile)
        return

    async def delete_biofile_by_id(self, biofile_id: str) -> bool | None:
        """Delete a biofile with a matching ID"""
        async with sessionmanager.session() as session:
            async with session.begin():
                biofile = await session.get(SqlBiofile, biofile_id)

                if biofile:
                    await session.delete(biofile)
                    return True

    async def retrieve_biofiles_by_key(self, key: str, val: str) -> List[dict] | None:
        """Retrieve biofiles with a matching path or hash"""
        async with sessionmanager.session() as session:
            try:
                stmt = select(SqlBiofile).where(getattr(SqlBiofile, key) == val)
                result = await session.stream(stmt)

            except AttributeError as e:
                raise e
            else:
                # result is a streaming AsyncResult object.
                biofiles = []
                async for biofile in result.scalars():
                    biofiles.append(sqlite_orm_to_dict(biofile))

                return biofiles

    def get_key_category(self, key):
        cat_universal = [
            "species",
            "origin",
            "organType",
            "cellType",
            "brainRegion",
            "protocolName",
            "keywords",
            "experimenter",
            "lab",
        ]
        cat_influence = [
            "control",
            "sham",
            "pharmacology",
            "radiation",
            "stimulus",
            "disease",
        ]
        cat_device = [
            "deviceMEA",
            "chipTypeMEA",
            "deviceMicroscope",
            "taskMicroscope",
        ]

        if key in cat_universal:
            return "cat_universal"
        elif key in cat_influence:
            return "cat_influence"
        elif key in cat_device:
            return key
        elif key == "date_from":
            return key
        elif key == "date_to":
            return key
        elif key == "experimentName":
            return key
        elif key is None:
            return "none"
        else:
            return "unknown"

    async def retrieve_biofiles_by_search(
        self, search: SearchModel
    ) -> List[Dict] | None:
        # pylint: disable=line-too-long
        """Retrieve biofiles with a matching search query"""
        stmt = "SELECT * FROM biofiles WHERE "

        search_dict = dict(search)

        conditions = []
        for key, values in search_dict.items():
            category = self.get_key_category(key)
            if not values:
                continue
            elif isinstance(values, str):
                values_str = f"{values}"
            else:
                values_str = ", ".join(f"'{value}'" for value in values)

            match category:
                case "cat_universal":
                    # """
                    # SELECT * FROM experiments WHERE
                    # WHERE EXISTS (
                    #     SELECT 1 FROM json_each(data, '$.keywords')
                    #     WHERE json_each.value IN ('neuron', 'lsd')
                    # )
                    # """
                    conditions.append(
                        (
                            "EXISTS ("
                            f"SELECT 1 FROM json_each(filecontext, '$.{key}') "
                            f"WHERE json_each.value IN ({values_str})"
                            ")"
                        )
                    )

                case "cat_influence":
                    # """
                    # SELECT * FROM experiments
                    # WHERE EXISTS(
                    #     SELECT 1 FROM json_each(experiments.data, '$.influenceGroups')
                    #     WHERE json_extract(json_each.value, '$.s_keys.name') IN (s_vals)
                    # )
                    # """
                    conditions.append(
                        (
                            "EXISTS ( "
                            "SELECT 1 FROM json_each(biofiles.filecontext, '$.influenceGroups') "
                            f"WHERE json_extract(json_each.value, '$.{key}.name') IN ({values_str})"
                            ")"
                        )
                    )
                case "deviceMEA":
                    # """SELECT * FROM experiments WHERE json_extract(data, '$.labDevice.MEA.name') IN (s_vals)"""
                    conditions.append(
                        f"json_extract(filecontext, '$.labDevice.mea.name') IN ({values_str})"
                    )
                case "chipTypeMEA":
                    # """SELECT * FROM experiments WHERE json_extract(data, '$.labDevice.MEA.chipType') IN (s_vals)"""
                    conditions.append(
                        f"json_extract(filecontext, '$.labDevice.mea.chipType') IN ({values_str})"
                    )
                case "deviceMicroscope":
                    # """SELECT * FROM experiments WHERE json_extract(data, '$.labDevice.Microscope.name') IN (s_vals)"""
                    conditions.append(
                        f"json_extract(filecontext, '$.labDevice.microscope.name') IN ({values_str})"
                    )
                case "taskMicroscope":
                    # """SELECT * FROM experiments WHERE json_extract(data, '$.labDevice.Microscope.task') IN (s_vals)"""
                    conditions.append(
                        f"json_extract(filecontext, '$.labDevice.microscope.task') IN ({values_str})"
                    )
                case "date_from":
                    # """SELECT * FROM experiments WHERE json_extract(data, '$.date') >= s_vals"""
                    conditions.append(
                        f"json_extract(filecontext, '$.date') >= '{values_str}'"
                    )
                case "date_to":
                    # """SELECT * FROM experiments WHERE json_extract(data, '$.date') <= s_vals"""
                    conditions.append(
                        f"json_extract(filecontext, '$.date') <= '{values_str}'"
                    )
                case "experimentName":
                    # """SELECT * FROM experiments WHERE json_extract(data, '$.experimentName') = s_vals"""
                    conditions.append(
                        f"json_extract(filecontext, '$.experimentName') LIKE '%{values_str}%'"
                    )
                case "none":
                    pass
                case "unknown":
                    conditions.append(
                        f"json_extract(filecontext, '$.{key}') IN ({values_str})"
                    )

        if conditions:
            stmt += " AND ".join(conditions)
        else:
            # If there are no conditions, remove the WHERE clause
            stmt = "SELECT * FROM biofiles"

        async with sessionmanager.session() as session:
            result = await session.stream(text(stmt))

            biofiles = []
            async for biofile in result.mappings():
                biofile_dict = dict(biofile)
                biofile_dict["filecontext"] = json.loads(biofile_dict["filecontext"])
                biofiles.append(biofile_dict)
            return biofiles

    async def check_database(self) -> bool | None:
        """Check if the database is available"""
        # check if the table from above exists
        async with sessionmanager.session() as session:
            result = await session.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='biofiles'"
                )
            )
            return bool(result.scalar_one_or_none())

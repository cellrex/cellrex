from abc import ABC, abstractmethod
from inspect import signature
from typing import Dict, List, Tuple

from model.biofile import Biofile
from model.search import SearchModel


class DatabaseInterface(ABC):
    """
    DatabaseInterface base class.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for name, method in cls.__dict__.items():
            if name in ["__init__"]:
                continue
            if callable(method) and hasattr(super(cls, cls), name):
                super_params = signature(getattr(super(cls, cls), name)).parameters
                sub_params = signature(method).parameters
                if super_params != sub_params:
                    raise TypeError(
                        f"Parameters of {name} in {cls.__name__} don't match superclass"
                    )

    @abstractmethod
    async def add_biofile(self, data: Biofile) -> str | None:
        """Add a new biofile into to the database"""
        pass

    @abstractmethod
    async def retrieve_biofiles(
        self, offset: int, limit: int
    ) -> Tuple[List[Dict], int] | None:
        """Retrieve all biofiles present in the database"""
        pass

    @abstractmethod
    async def retrieve_biofile_by_id(self, biofile_id: str) -> Dict | None:
        """Retrieve a biofile with a matching ID"""
        pass

    @abstractmethod
    async def update_biofile_by_id(self, biofile_id: str, data: Biofile) -> str | None:
        """Update a biofile with a matching ID"""
        pass

    @abstractmethod
    async def delete_biofile_by_id(self, biofile_id: str) -> bool | None:
        """Delete a biofile with a matching ID"""
        pass

    @abstractmethod
    async def retrieve_biofiles_by_key(self, key: str, val: str) -> List[dict] | None:
        """Retrieve biofiles with a matching path or hash"""
        pass

    @abstractmethod
    async def retrieve_biofiles_by_search(
        self, search: SearchModel
    ) -> List[Dict] | None:
        """Retrieve biofiles with a matching search query"""
        pass

    @abstractmethod
    async def check_database(self) -> bool | None:
        """Check if the database is available"""
        pass

    @classmethod
    def delete_none(cls, _dict):
        """Delete None values and empty dictionaries recursively from all of the dictionaries"""
        for key, value in list(_dict.items()):
            if isinstance(value, dict):
                cls.delete_none(value)
                if not value:  # if the dictionary is empty after removing None values
                    del _dict[key]  # delete the key from the parent dictionary
            elif value is None:
                del _dict[key]
            elif isinstance(value, list):
                for v_i in value:
                    if isinstance(v_i, dict):
                        cls.delete_none(v_i)
                        if (
                            not v_i
                        ):  # if the dictionary is empty after removing None values
                            value.remove(
                                v_i
                            )  # remove the empty dictionary from the list

        return _dict

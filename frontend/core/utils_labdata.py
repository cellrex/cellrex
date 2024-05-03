from typing import Any, Dict, List


class PrefillList(list):
    """Custom list implementing default values for missing keys

    Custom list implementing default index and list values for missing keys.
    The default values are set to 0 and [] respectively. The lookup is done
    on between the keys of the experiment_data dictionary and the list itself.

    amended from: https://stackoverflow.com/questions/2132718
    """

    def getindexdefault(
        self, elem: str, experiment_data: Dict[str, Any], default: int = 0
    ) -> int:
        try:
            return (
                self.index(experiment_data[elem])
                if elem in experiment_data.keys()
                else 0
            )
        except ValueError:
            return default

    def getlistdefault(
        self, elem: str, experiment_data: Dict[str, Any], default: List[str] = None
    ) -> List[str]:
        try:
            if isinstance(experiment_data[elem], list):
                return experiment_data[elem]
            elif isinstance(experiment_data[elem], dict):
                return list(experiment_data[elem].keys())
        except KeyError:
            return default if default is not None else []


class PrefillDict(dict):
    """Custom dict implementing default index values for missing keys

    Custom dict implementing default index values for missing keys. The
    default value is set to 0. The lookup is done between the keys of the
    experiment_data dictionary and the dict itself.
    """

    def getindexdefault(
        self, elem: str, experiment_data: Dict[str, Any], default: int = 0
    ) -> int:
        try:
            return (
                list(self.keys()).index(experiment_data[elem])
                if elem in experiment_data.keys()
                else 0
            )
        except ValueError:
            return default

    def getlistdefault(
        self, elems: str, experiment_data: Dict[str, Any], default: List = None
    ) -> List:
        try:
            return [elem for elem in experiment_data[elems] if elem in self.keys()]
        except KeyError:
            print("KeyError")
            return default if default is not None else []

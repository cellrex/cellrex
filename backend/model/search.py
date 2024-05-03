# pylint: disable=invalid-name
from typing import List, Optional

from pydantic import BaseModel


class SearchModel(BaseModel, extra="ignore"):
    species: Optional[List[str]] = None
    origin: Optional[List[str]] = None
    organType: Optional[List[str]] = None
    cellType: Optional[List[str]] = None
    brainRegion: Optional[List[str]] = None
    protocolNames: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    experimenter: Optional[List[str]] = None
    lab: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    experimentName: Optional[str] = None
    control: Optional[List[str]] = None
    sham: Optional[List[str]] = None
    pharmacology: Optional[List[str]] = None
    radiation: Optional[List[str]] = None
    stimulus: Optional[List[str]] = None
    disease: Optional[List[str]] = None
    deviceMEA: Optional[List[str]] = None
    chipTypeMEA: Optional[List[str]] = None
    deviceMicroscope: Optional[List[str]] = None
    taskMicroscope: Optional[List[str]] = None

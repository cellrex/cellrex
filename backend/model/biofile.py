# pylint: disable=invalid-name
# pylint: disable=missing-class-docstring
"""
This module contains the data models used in the CellRex backend.

The data models define the structure and validation rules for various
entities used in the application. Each data model is defined as a Pydantic
BaseModel subclass, with optional fields and validation logic.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class Control(BaseModel):
    name: str = ...
    wells: Optional[List[str]] = None


class Sham(BaseModel):
    name: str = ...
    wells: Optional[List[str]] = None
    notes: Optional[str] = None


class Pharmacology(BaseModel):
    name: str = ...
    concentration: Optional[float] = None
    concentrationUnit: Optional[str] = None
    exposure: Optional[float] = None
    exposureUnit: Optional[str] = None
    wells: Optional[List[str]] = None
    notes: Optional[str] = None


class Radiation(BaseModel):
    name: str = ...
    dosage: Optional[float] = None
    dosageUnit: Optional[str] = None
    exposure: Optional[float] = None
    exposureUnit: Optional[str] = None
    irradiationDevice: Optional[str] = None
    wells: Optional[List[str]] = None
    notes: Optional[str] = None


class Stimulus(BaseModel):
    name: str = ...


class Disease(BaseModel):
    name: str = ...
    wells: Optional[List[str]] = None
    notes: Optional[str] = None


class InfluenceGroup(BaseModel):
    control: Optional[Control] = None
    sham: Optional[Sham] = None
    pharmacology: Optional[Pharmacology] = None
    radiation: Optional[Radiation] = None
    stimulus: Optional[Stimulus] = None
    disease: Optional[Disease] = None


class IFStaining(BaseModel):
    numAntibodies: Optional[int] = None
    abPrim1: Optional[str] = None
    abSec1: Optional[str] = None
    abPrim2: Optional[str] = None
    abSec2: Optional[str] = None
    abPrim3: Optional[str] = None
    abSec3: Optional[str] = None
    abPrim4: Optional[str] = None
    abSec4: Optional[str] = None
    abPrim5: Optional[str] = None
    abSec5: Optional[str] = None
    abCon: Optional[str] = None
    dyeOth: Optional[str] = None


class Ca2Imaging(BaseModel):
    dye: Optional[str] = None


class Microscope(BaseModel):
    type: str = ...
    name: str = ...
    magnification: Optional[list] = None
    task: str = ...
    ifStaining: Optional[IFStaining] = None
    ca2Imaging: Optional[Ca2Imaging] = None
    brightfield: Optional[Dict] = None

    @model_validator(mode="after")
    def check_exactly_one(self):
        if [self.ifStaining, self.ca2Imaging, self.brightfield].count(None) != 2:
            raise ValueError(
                "Exactly one of ifStaining, ca2Imaging, or brightfield must be provided"
            )
        return self


class MEA(BaseModel):
    name: str = None
    chipType: str = None
    chipId: Optional[int] = None
    recDur: Optional[int] = None
    rate: Optional[int] = None


class LabDevice(BaseModel):
    microscope: Optional[Microscope] = None
    mea: Optional[MEA] = None

    @model_validator(mode="after")
    def check_microscope_or_mea(self):
        microscope, mea = self.microscope, self.mea
        if (microscope is None and mea is None) or (
            microscope is not None and mea is not None
        ):
            raise ValueError("Exactly one of microscope or mea must be provided")
        return self


class Protocol(BaseModel):
    name: str = ...
    path: str = ...
    notes: Optional[str] = None
    text: str = ...


class Filecontext(BaseModel, extra="forbid"):
    species: str = ...
    origin: str = ...
    organType: str = ...
    cellType: str = ...
    brainRegion: List[str] = None
    protocolNames: Optional[List[str]] = None
    cellID: Optional[str] = None
    protocols: Optional[Dict[str, Protocol]] = None
    keywords: List[str] = Field(..., min_items=1)
    experimenter: List[str] = Field(..., min_items=1)
    lab: List[str] = Field(..., min_items=1)
    date: str = ...
    time: Optional[str] = None
    experimentName: str = ...
    precursorExperimentNames: Optional[List[str]] = None
    sampleID: int = ...
    ageDIV: Optional[int] = None
    ageDAP: Optional[int] = None
    numInfluenceGroups: int = Field(..., gt=0)
    influenceGroups: Dict[str, InfluenceGroup] = ...
    labDeviceType: str = ...
    labDevice: LabDevice = ...
    notes: Optional[str] = None
    smiley: Optional[int] = None
    creationDate: str = ...
    filepath: str = ...

    @field_validator("influenceGroups")
    @classmethod
    def must_contain_at_least_one_item(cls, v):
        if not v:
            raise ValueError("influenceGroups must contain at least one item")
        return v

    @model_validator(mode="after")
    def check_age(self):
        ageDIV = self.ageDIV
        ageDAP = self.ageDAP
        if ageDIV is None and ageDAP is None:
            raise ValueError("Either ageDIV or ageDAP must be provided")
        return self


class Biofile(BaseModel, extra="forbid"):
    filecontext: Filecontext = None
    filepath: str = None
    filesize: int = None
    filehash: str = None
    filetype: str = None


class FilecontextOptional(BaseModel):
    species: Optional[str] = None
    origin: Optional[str] = None
    organType: Optional[str] = None
    cellType: Optional[str] = None
    brainRegion: Optional[List[str]] = None
    experimentName: Optional[str] = None
    sampleID: Optional[int] = None
    ageDIV: Optional[int] = None
    ageDAP: Optional[int] = None
    influenceGroups: Optional[Dict[str, InfluenceGroup]] = None
    labDevice: Optional[LabDevice] = None

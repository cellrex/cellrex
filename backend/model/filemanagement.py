from pathlib import Path

from model.biofile import Filecontext
from pydantic import BaseModel


class FileMove(BaseModel):
    filename: Path
    srcpath: Path
    dstpath: Path
    filecontext: Filecontext = None

    @property
    def jsonfilename(self) -> Path:
        return self.filename.with_suffix(self.filename.suffix + ".json")

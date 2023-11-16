
from pathlib import Path
from typing import List, Dict

from pydantic import BaseModel, Field

from modules.shared import
.

class MessageRecorder(BaseModel):
    class Config:
        validate_assignment = True

    data_dir: str | Path
    data: Dict[int, List[str]] = Field(default_factory=dict, const=True, allow_mutation=False)


    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        if save
    def add_data(self,key):
        pass

    def save(self):
        pass


    def load(self):
        pass

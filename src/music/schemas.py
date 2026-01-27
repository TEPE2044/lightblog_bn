from typing import Optional

from pydantic import BaseModel


class Radio(BaseModel):
    radio_name: str
    author: Optional[str]

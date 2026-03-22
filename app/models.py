from pydantic import BaseModel
from typing import List

class BatchWakeRequest(BaseModel):
    mac_addresses: List[str]
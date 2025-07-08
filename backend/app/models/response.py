from typing import List
from pydantic import BaseModel

class ExperienceTag(BaseModel):
    tag: str
    evidence: str


class InferenceResult(BaseModel):
    tags: List[ExperienceTag]

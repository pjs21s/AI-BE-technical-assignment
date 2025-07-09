from typing import List
from pydantic import BaseModel, Field

class ExperienceTag(BaseModel):
    tag: str = Field(..., example="리더쉽", description="데이터 기반으로 추출한 경험 태그")
    evidence: str = Field(..., example="CTO, Tech Lead 등 직책 기반 추론", description="데이터 기반으로 추출한 경험 태그의 근거")


class InferenceResult(BaseModel):
    tags: List[ExperienceTag]

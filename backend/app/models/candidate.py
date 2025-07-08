from typing import List, Optional
from pydantic import BaseModel, Field

class Position(BaseModel):
    title: str
    companyName: str
    description: str
    startEndDate: dict
    companyLocation: str


class Education(BaseModel):
    schoolName: str
    degreeName: Optional[str]
    fieldOfStudy: Optional[str]
    startEndDate: Optional[str]
    description: Optional[str]


class Candidate(BaseModel):
    firstName: str
    lastName: str

    headline: Optional[str] = Field(None, description="LInkedIn 헤드라인")
    summary: Optional[str] = Field(None, description="자기소개/요약 문구")
    skills: List[str] = Field(default_factory=list, description="보유 스킬 목록")
    website: List[str] = Field(default_factory=list, description="개인 웹사이트나 블로그 URL 목록")

    educations: List[Education] = Field(default_factory=list)
    positions: List[Position] = Field(default_factory=list)

from typing import List, Optional
from pydantic import BaseModel, Field

class Position(BaseModel):
    title: str = Field(..., example="CTO", description="직책")
    companyName: str = Field(..., example="비바리퍼블리카", description="회사 이름")
    description: str = Field(..., example="토스쇼핑 검색 서비스 백엔드 아키텍처 설계 및 개발", description="수행한 업무")
    startEndDate: dict = Field(..., description="근무 기간")
    companyLocation: str = Field(..., example="대한민국 서울 강남구",description="회사 대략적인 주소")


class Education(BaseModel):
    schoolName: str = Field(..., example="연세대학교", description="대학교 이름")
    degreeName: Optional[str] = Field(..., example="학사", description="학/석/박사 표기")
    fieldOfStudy: Optional[str] = Field(..., example="컴퓨터 공학", description="공부한 분야")
    startEndDate: Optional[str] = Field(..., description="재학 기간")
    description: Optional[str] = Field(..., description="기타 설명")


class Candidate(BaseModel):
    firstName: str = Field(..., example="Junho", description="이름")
    lastName: str = Field(..., example="Kim", description="성")

    headline: Optional[str] = Field(None, description="LInkedIn 헤드라인")
    summary: Optional[str] = Field(None, description="자기소개/요약 문구")
    skills: List[str] = Field(default_factory=list, description="보유 스킬 목록")
    website: List[str] = Field(default_factory=list, description="개인 웹사이트나 블로그 URL 목록")

    educations: List[Education] = Field(default_factory=list)
    positions: List[Position] = Field(default_factory=list)

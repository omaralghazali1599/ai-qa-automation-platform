from pydantic import BaseModel, validator
from typing import List

class TestCase(BaseModel):
    id: str
    title: str
    steps: List[str]
    expected_result: str

    @validator("steps")
    def steps_not_empty(cls, v):
        if not v:
            raise ValueError("steps list cannot be empty")
        return v

class TestSuite(BaseModel):
    positive: List[TestCase] = []
    negative: List[TestCase] = []
    edge: List[TestCase] = []
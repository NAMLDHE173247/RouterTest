from pydantic import BaseModel, validator, Field
from typing import List, Optional

class DatasetSample(BaseModel):
    id: str
    question: str
    history: List[str]
    primary_subject: str
    secondary_subjects: List[str]
    intent: str
    target_slm: str
    need_clarification: bool
    case_type: str

    @validator('primary_subject')
    def validate_primary_subject(cls, v):
        allowed = {"math", "physics", "chemistry", "unknown"}
        if v not in allowed:
            raise ValueError(f"Invalid primary_subject: {v}")
        return v

    @validator('secondary_subjects', each_item=True)
    def validate_secondary_subjects(cls, v):
        allowed = {"math", "physics", "chemistry"}
        if v not in allowed:
            raise ValueError(f"Invalid secondary_subject: {v}")
        return v

    @validator('intent')
    def validate_intent(cls, v):
        allowed = {
            "solve_problem", "explain_concept", "give_hint", "check_answer", 
            "diagnose_error", "ask_follow_up", "unknown"
        }
        if v not in allowed:
            raise ValueError(f"Invalid intent: {v}")
        return v

    @validator('target_slm')
    def validate_target_slm(cls, v):
        allowed = {"math_slm", "physics_slm", "chemistry_slm", "general_tutor", "ask_clarification"}
        if v not in allowed:
            raise ValueError(f"Invalid target_slm: {v}")
        return v

    @validator('case_type')
    def validate_case_type(cls, v):
        allowed = {"single_turn", "multi_turn", "interdisciplinary", "ambiguous", "out_of_scope"}
        if v not in allowed:
            raise ValueError(f"Invalid case_type: {v}")
        return v

class DatasetMetadata(BaseModel):
    dataset_id: str
    original_filename: str
    stored_filename: str
    format: str
    total_samples: int
    valid_samples: int
    invalid_samples: int
    uploaded_at: str
    status: str
    source: str = "uploaded"

class DatasetErrorDetail(BaseModel):
    line: int
    id: Optional[str] = None
    field: Optional[str] = None
    message: str

class DatasetUploadResponse(BaseModel):
    dataset_id: Optional[str] = None
    filename: str
    format: str
    total_samples: int
    valid_samples: int
    invalid_samples: int
    status: str
    message: Optional[str] = None
    errors: Optional[List[DatasetErrorDetail]] = None

class DatasetListItem(BaseModel):
    dataset_id: str
    name: str
    format: str
    total_samples: int
    source: str

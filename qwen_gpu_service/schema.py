from typing import Literal, List
from pydantic import BaseModel, Field, model_validator, ConfigDict

Subject = Literal["math", "physics", "chemistry", "unknown"]
Intent = Literal[
    "solve_problem",
    "explain_concept",
    "give_hint",
    "check_answer",
    "diagnose_error",
    "ask_follow_up",
    "unknown"
]
TargetSLM = Literal[
    "math_slm",
    "physics_slm",
    "chemistry_slm",
    "general_tutor",
    "ask_clarification"
]

class RouterDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    primary_subject: Subject
    secondary_subjects: List[Subject] = Field(default_factory=list)
    intent: Intent
    target_slm: TargetSLM
    confidence: float = Field(ge=0.0, le=1.0)
    need_clarification: bool
    reason: str
    
    @model_validator(mode='after')
    def validate_fields(self):
        if not self.reason.strip():
            raise ValueError("reason cannot be empty.")
            
        seen = set()
        deduped = []
        for s in self.secondary_subjects:
            if s not in seen:
                seen.add(s)
                deduped.append(s)
                
        filtered_secondary = []
        for s in deduped:
            if s != "unknown" and s != self.primary_subject:
                filtered_secondary.append(s)
                
        self.secondary_subjects = filtered_secondary
        
        return self

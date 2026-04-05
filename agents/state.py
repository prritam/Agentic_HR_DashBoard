from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    resume_text: str
    job_description: str
    form_data: dict
    job_id: str
    relevant_policies: List[str]
    candidate_history: List[dict] # Memory storage
    score: Optional[int]
    reason: Optional[str]
    decision: Optional[str] 
    errors: List[str]
    attempts: int
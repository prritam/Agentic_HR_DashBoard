from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    # Input data
    resume_text: str
    job_description: str
    form_data: dict
    job_id: str
    
    # RAG Data
    relevant_policies: List[str]
    
    # Internal working data
    score: Optional[int]
    reason: Optional[str]
    decision: Optional[str] 
    
    # Tracking
    errors: List[str]
    attempts: int
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import PyPDF2
import io
import core.database as db
from agents.state import AgentState
from agents.evaluator import GraphNodes
from langgraph.graph import StateGraph, END

app = FastAPI()
nodes = GraphNodes()
db.init_db()

# --- LANGGRAPH DEFINITION ---
workflow = StateGraph(AgentState)

workflow.add_node("retrieve", nodes.retrieval_node)
workflow.add_node("memory", nodes.memory_node)
workflow.add_node("evaluate", nodes.scorer_node)
workflow.add_node("judge", nodes.judge_node)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "memory")
workflow.add_edge("memory", "evaluate")
workflow.add_edge("evaluate", "judge")

# The Router: Decides if we loop back to 'evaluate' or finish
def router(state):
    # Check if the Judge requested a retry and we haven't hit the limit
    if state.get("decision") == "retry" and state.get("attempts", 0) < 1:
        print(f"--- LOOPING BACK: Attempt {state['attempts']} failed compliance ---")
        return "evaluate"
    return "end"

workflow.add_conditional_edges(
    "judge", 
    router, 
    {
        "evaluate": "evaluate", 
        "end": END
    }
)

hr_graph = workflow.compile()

@app.post("/submit_application/{job_id}")
async def submit_application(
    job_id: str,
    name: str = Form(...),
    email: str = Form(...),
    mobile: str = Form(...),
    current_employer: str = Form(...),
    current_ctc: float = Form(...),
    expected_ctc: float = Form(...),
    notice_period: str = Form(...),
    last_working_day: str = Form(...),
    resume: UploadFile = File(...)
):
    # Extract resume text
    try:
        content = await resume.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        resume_text = "".join([page.extract_text() for page in pdf_reader.pages])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")
    
    # Get job description
    job_data = db.get_job(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    job_description = job_data[1]
    
    # Initial state
    initial_state = {
        "resume_text": resume_text,
        "job_description": job_description,
        "form_data": {
            "name": name,
            "email": email,
            "mobile": mobile,
            "current_employer": current_employer,
            "current_ctc": current_ctc,
            "expected_ctc": expected_ctc,
            "notice_period": notice_period,
            "last_working_day": last_working_day
        },
        "job_id": job_id,
        "relevant_policies": [],
        "candidate_history": [],
        "score": None,
        "reason": None,
        "decision": None,
        "errors": [],
        "attempts": 0
    }
    
    # Run graph
    final_state = hr_graph.invoke(initial_state)
    
    # Save to DB
    db.save_candidate(final_state["form_data"], final_state["score"], final_state["reason"], job_id)
    
    return {"status": "success", "message": "Application submitted successfully"}
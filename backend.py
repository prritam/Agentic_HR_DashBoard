from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import PyPDF2
import io
from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.evaluator import GraphNodes
from core.tools import execute_tool
import core.database as db

app = FastAPI()
nodes = GraphNodes()

# Define the Graph Structure
workflow = StateGraph(AgentState)

# 1. Add All Nodes
workflow.add_node("retrieve", nodes.retrieval_node)
workflow.add_node("evaluate", nodes.scorer_node)
workflow.add_node("validate", nodes.validator_node)

# 2. Set the Path
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "evaluate")
workflow.add_edge("evaluate", "validate")

# 3. Define the Router Logic
def router(state):
    if state["decision"] == "retry" and state["attempts"] < 3:
        return "evaluate"
    return "end"

workflow.add_conditional_edges("validate", router, {"evaluate": "evaluate", "end": END})

# 4. Compile the Brain
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
    # PDF and Job Info setup
    content = await resume.read()
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
    text = "".join([p.extract_text() for p in pdf_reader.pages])
    job_info = db.get_job(job_id)
    
    form_data = {
        "name": name, "email": email, "mobile": mobile, 
        "current_employer": current_employer, "current_ctc": current_ctc, 
        "expected_ctc": expected_ctc, "notice_period": notice_period, 
        "last_working_day": last_working_day
    }

    # Initialize Graph State
    initial_state = {
        "resume_text": text,
        "job_description": job_info[1] if job_info else "General Role",
        "form_data": form_data,
        "job_id": job_id,
        "relevant_policies": [],
        "attempts": 0,
        "errors": [],
        "score": 0,
        "reason": "",
        "decision": ""
    }
    
    # RUN THE AGENTIC GRAPH
    final_state = hr_graph.invoke(initial_state)

    if final_state["decision"] == "save":
        execute_tool("save_candidate", {
            "data": form_data,
            "score": final_state["score"],
            "reason": final_state["reason"],
            "job_id": job_id
        })
        return {"status": "Success", "ai_score": final_state["score"]}
    
    raise HTTPException(status_code=500, detail="AI Graph failed to process candidate.")
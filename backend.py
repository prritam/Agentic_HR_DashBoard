from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import PyPDF2
import io
import core.database as db
from agents.evaluator import EvaluatorAgent
from core.tools import execute_tool

app = FastAPI()
evaluator = EvaluatorAgent()

@app.on_event("startup")
def startup():
    db.init_db()

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
    # 1. Validate Job
    job_info = db.get_job(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="Job not found")

    # 2. Extract PDF Text
    try:
        content = await resume.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        resume_text = "".join([page.extract_text() for page in pdf_reader.pages])
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read PDF file")

    # 3. Prepare Input Data
    form_data = {
        "name": name, "email": email, "mobile": mobile,
        "current_employer": current_employer, "current_ctc": current_ctc,
        "expected_ctc": expected_ctc, "notice_period": notice_period,
        "last_working_day": last_working_day
    }

    # 4. Reflection Loop (Point 2: State & Reflection)
    max_retries = 3
    attempts = 0
    last_error = ""

    while attempts < max_retries:
        try:
            # Ask agent for a decision, passing previous error if it exists
            decision = evaluator.decide_action(resume_text, job_id, form_data, last_error)
            
            # Attempt to execute the tool
            tool_result = execute_tool(decision['tool'], decision['parameters'])
            
            # If the tool itself returns an error string, trigger a retry
            if "Error" in tool_result:
                last_error = tool_result
                attempts += 1
                continue
            
            # Success state
            return {
                "status": "Success",
                "attempts_required": attempts + 1,
                "agent_decision": decision['tool'],
                "log": tool_result
            }

        except Exception as e:
            # Catch JSON parsing errors or logic errors
            last_error = str(e)
            attempts += 1

    # Final Failure state if all retries exhausted
    raise HTTPException(
        status_code=500, 
        detail=f"Agent failed to provide a valid action after {max_retries} attempts. Last error: {last_error}"
    )
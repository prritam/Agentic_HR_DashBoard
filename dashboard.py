import streamlit as st
import requests
import core.database as db

db.init_db()
from core.database import create_job

# --- GET JOB ID FROM URL ---
query_params = st.query_params
job_id = query_params.get("job")

if not job_id:
    # HR Dashboard
    st.title("HR Dashboard - Create Job")
    
    title = st.text_input("Job Title")
    description = st.text_area("Job Description")
    experience = st.number_input("Required Experience (years)", min_value=0)
    
    if st.button("Create Job"):
        if title and description:
            job_id_new = create_job(title, description, experience)
            link = f"http://localhost:8501/?job={job_id_new}"
            st.success("Job created!")
            st.write("Share this link with candidates:")
            st.code(link, language="text")
        else:
            st.error("Please fill all fields.")
    
    # View Candidates
    if st.button("View Candidates"):
        candidates = db.get_leaderboard()
        if candidates:
            st.subheader("Candidate Leaderboard")
            for i, (name, score, reason, email, lwd, job_title) in enumerate(candidates, 1):
                st.write(f"{i}. {name} ({job_title}) - Score: {score}/100 - {reason}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Send Assessment Invite to {name}", key=f"assess_{i}"):
                        from agents.communicator import CommunicatorAgent
                        comm = CommunicatorAgent()
                        email_body = comm.draft_assessment(name, job_title)
                        from core.mailer import send_real_email
                        result = send_real_email(email, "Technical Assessment Invite", email_body)
                        if "Email sent" in result:
                            st.success(f"Invite sent to {email}")
                        else:
                            st.error(f"Failed to send: {result}")
                with col2:
                    if st.button(f"Send Interview Invite to {name}", key=f"interview_{i}"):
                        comm = CommunicatorAgent()
                        email_body = comm.draft_interview(name, "Tomorrow at 10 AM")
                        result = send_real_email(email, "Interview Invite", email_body)
                        if "Email sent" in result:
                            st.success(f"Interview invite sent to {email}")
                        else:
                            st.error(f"Failed to send: {result}")
        else:
            st.write("No candidates yet.")
else:
    # Application Form
    st.title(f"Application Form (Job ID: {job_id})")
    
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    mobile = st.text_input("Mobile Number")
    current_employer = st.text_input("Current Employer")
    current_ctc = st.number_input("Current CTC (in LPA)", min_value=0.0)
    expected_ctc = st.number_input("Expected CTC (in LPA)", min_value=0.0)
    notice_period = st.text_input("Notice Period")
    if notice_period and ("serving" in notice_period.lower() or "days" in notice_period.lower()):
        last_working_day = st.text_input("Last Working Day (YYYY-MM-DD)")
    else:
        last_working_day = "N/A"
    resume_file = st.file_uploader("Upload Resume (PDF)", type="pdf")
    
    if st.button("Submit Application"):
        if not all([name, email, mobile, current_employer, resume_file]):
            st.error("Please fill all required fields.")
        else:
            # Prepare Data
            data = {
                "name": name,
                "email": email,
                "mobile": mobile,
                "current_employer": current_employer,
                "current_ctc": current_ctc,
                "expected_ctc": expected_ctc,
                "notice_period": notice_period,
                "last_working_day": last_working_day
            }
            
            files = {"resume": (resume_file.name, resume_file.getvalue(), "application/pdf")}
            
            # Submit to API
            with st.spinner("Submitting application..."):
                try:
                    response = requests.post(
                        f"http://127.0.0.1:8000/submit_application/{job_id}", 
                        data=data, 
                        files=files
                    )
                    if response.status_code == 200:
                        st.success("Application submitted successfully! HR will review and contact you if shortlisted.")
                    else:
                        st.error(f"Submission failed: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
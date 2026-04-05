import streamlit as st
import requests
import core.database as db
from agents.communicator import CommunicatorAgent
from core.mailer import send_real_email

# --- Page Config ---
st.set_page_config(page_title="Agentic HR Portal", layout="wide", page_icon="🤖")

# Initialize DB and Agents
db.init_db()
comm_agent = CommunicatorAgent()

# --- Check URL for Job Link (Candidate Mode) ---
query_params = st.query_params
job_id_url = query_params.get("job")

if job_id_url:
    # ---------------------------------------------------------
    # CANDIDATE VIEW: The Shared LinkedIn Form
    # ---------------------------------------------------------
    job_info = db.get_job(job_id_url)
    
    if job_info:
        st.title(f"Apply for: {job_info[0]}")
        st.info(f"**Requirements:** {job_info[1]} | **Min Experience:** {job_info[2]} Years")
        
        with st.form("candidate_apply"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name*")
                email = st.text_input("Email*")
                mobile = st.text_input("Mobile Number*")
                employer = st.text_input("Current Employer")
            with col2:
                c_ctc = st.number_input("Current CTC (LPA)", min_value=0.0)
                e_ctc = st.number_input("Expected CTC (LPA)", min_value=0.0)
                notice = st.selectbox("Notice Period", ["Immediate", "30 Days", "60 Days", "90 Days"])
                lwd = st.text_input("Last Working Day (if serving)", value="N/A")
            
            uploaded_file = st.file_uploader("Upload Resume (PDF only)*", type="pdf")
            
            submit_btn = st.form_submit_button("Submit Application")
            
            if submit_btn:
                if not uploaded_file or not name or not email:
                    st.error("Please fill in all required fields and upload your resume.")
                else:
                    with st.spinner("AI Agent is analyzing your application via Backend..."):
                        # Prepare data for FastAPI
                        files = {"resume": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                        payload = {
                            "name": name,
                            "email": email,
                            "mobile": mobile,
                            "current_employer": employer,
                            "current_ctc": c_ctc,
                            "expected_ctc": e_ctc,
                            "notice_period": notice,
                            "last_working_day": lwd
                        }
                        
                        try:
                            # CALLING THE FASTAPI BACKEND
                            response = requests.post(
                                f"http://localhost:8000/submit_application/{job_id_url}", 
                                data=payload, 
                                files=files
                            )
                            
                            if response.status_code == 200:
                                st.success(f"✅ Success! AI Scored your profile: {response.json().get('score')}/100")
                                st.balloons()
                            else:
                                st.error(f"Backend Error: {response.text}")
                        except Exception as e:
                            st.error(f"Could not connect to FastAPI Backend. Is it running? Error: {e}")
    else:
        st.error("Invalid Job Link. Please check the URL.")

else:
    # ---------------------------------------------------------
    # HR VIEW: The Management Dashboard
    # ---------------------------------------------------------
    st.title("🤖 HR Agentic Control Center")
    
    tab1, tab2 = st.tabs(["🏗️ Create Job Posting", "📊 Leaderboard & Actions"])

    with tab1:
        st.header("Post a New Job to LinkedIn")
        with st.container(border=True):
            j_title = st.text_input("Job Title", placeholder="e.g. Senior Python Developer")
            j_exp = st.number_input("Required Experience (Years)", min_value=0, max_value=40)
            j_desc = st.text_area("Detailed Job Description")
            
            if st.button("Generate Shared Form Link"):
                if j_title and j_desc:
                    new_id = db.create_job(j_title, j_desc, j_exp)
                    # This link uses the Streamlit URL + the Job ID
                    share_link = f"http://localhost:8501/?job={new_id}"
                    st.success("Job Created Successfully!")
                    st.code(share_link, language="text")
                else:
                    st.warning("Please provide a Title and Description.")

    with tab2:
        st.header("Candidate Leaderboard")
        candidates = db.get_leaderboard()
        
        if not candidates:
            st.write("No applications found in the database.")
        else:
            for rank, c in enumerate(candidates, 1):
                # c = (name, score, reason, email, lwd)
                name, score, justification, email, lwd = c
                
                with st.expander(f"Rank #{rank}: {name} (Score: {score}/100)"):
                    st.write(f"**Last Working Day:** {lwd}")
                    st.write(f"**AI Evaluation:** {justification}")
                    st.write(f"**Email:** {email}")
                    
                    st.divider()
                    
                    # HR Actions (Human-in-the-loop)
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button(f"📧 Send Assessment to {name}", key=f"as_{rank}"):
                            with st.spinner("Agent drafting email..."):
                                body = comm_agent.draft_assessment(name, "Python Developer")
                                status = send_real_email(email, "Technical Assessment Invitation", body)
                                st.toast(status)
                                st.info(body)
                    
                    with col_b:
                        if st.button(f"📅 Invite {name} to Interview", key=f"int_{rank}"):
                            with st.spinner("Agent drafting invite..."):
                                body = comm_agent.draft_interview(name, "Next Monday at 2 PM")
                                status = send_real_email(email, "Interview Invitation", body)
                                st.toast(status)
                                st.info(body)
import json
import re
from core.ollama_client import ask_llama
from datetime import datetime

class ParserAgent:
    def __init__(self):
        self.role = "You are a Recruitment Data Extraction Agent. You output strict JSON."

    def extract_info(self, resume_text):
        today = datetime.now().strftime("%Y-%m-%d")
        prompt = f"""
        Today's date is {today}.
        Extract the following from the resume: name, email, mobile, current_employer, job_role, current_ctc, expected_ctc, notice_period.
        
        SPECIAL LOGIC: If the candidate mentions they are "serving notice" or gives a "last working day", 
        calculate or extract the 'last_working_day' in YYYY-MM-DD format. If not mentioned, use "N/A".

        Resume Text: {resume_text}
        Return ONLY valid JSON.
        """
        raw = ask_llama(prompt, system_role=self.role)
        try:
            # Regex to find JSON block
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            return json.loads(match.group(0)) if match else {}
        except:
            return {{"name": "Error", "last_working_day": "N/A"}}
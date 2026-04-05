from core.ollama_client import ask_llama
import json
import re

class EvaluatorAgent:
    def __init__(self):
        self.role = """
        You are an Autonomous Recruitment Dispatcher.
        Your job is to analyze resumes and decide on the next action.
        
        AVAILABLE TOOLS:
        1. save_candidate: Use this to store the applicant's data and score.
        2. send_email: Use this to send a rejection email if the score is below 40.
        """

    def decide_action(self, resume_text, job_id, form_data):
        prompt = f"""
        Analyze this resume against the requirements.
        Resume Text: {resume_text}
        
        If the candidate is decent (Score > 40), call 'save_candidate'.
        Return ONLY a JSON object in this format:
        {{
            "tool": "save_candidate",
            "parameters": {{
                "data": {form_data},
                "score": 85,
                "reason": "Strong Python skills...",
                "job_id": "{job_id}"
            }}
        }}
        """
        response = ask_llama(prompt, system_role=self.role)
        # Regex to ensure we only get the JSON block
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise Exception("Agent failed to provide structured JSON.")
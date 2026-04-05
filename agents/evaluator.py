import json
import re
from core.ollama_client import ask_llama

class GraphNodes:
    def __init__(self):
        self.system_role = "You are an AI Recruitment Specialist."

    def scorer_node(self, state: dict):
        # Node to evaluate and score the resume
        print("--- EXECUTING SCORER NODE ---")
        
        error_context = f"\nPrevious Error to fix: {state['errors'][-1]}" if state['errors'] else ""
        
        prompt = f"""
        Score this resume against the requirements.
        Requirements: {state['job_description']}
        Resume: {state['resume_text']}
        {error_context}
        
        Return ONLY valid JSON: {{"score": 85, "reason": "Text..."}}
        """
        
        response = ask_llama(prompt, system_role=self.system_role)
        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            data = json.loads(match.group(0))
            return {
                "score": data.get("score", 50),
                "reason": data.get("reason", "No reason provided"),
                "attempts": state["attempts"] + 1
            }
        except Exception as e:
            return {"errors": [f"JSON Parse Error: {str(e)}"], "attempts": state["attempts"] + 1}

    def validator_node(self, state: dict):
        # Node to check if the evaluation was successful and logical
        print("--- EXECUTING VALIDATOR NODE ---")
        
        # Check for errors from the scorer
        if state.get("errors") and len(state["errors"]) > state["attempts"] - 1:
            return {"decision": "retry"}
            
        # Logic check: If score is very high but reason is too short
        if state["score"] > 90 and len(state["reason"]) < 20:
            return {
                "decision": "retry", 
                "errors": state["errors"] + ["Reason is too short for a high score."]
            }
            
        return {"decision": "save"}
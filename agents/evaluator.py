import json
import re
import chromadb
import ollama
import core.database as db
from core.ollama_client import ask_llama

class EvaluatorAgent:
    def __init__(self):
        self.system_role = "You are a Recruitment Agent."
    
    def score_candidate(self, candidate_data, job_requirement):
        prompt = f"""
        Evaluate candidate: {candidate_data['name']}
        Job: {job_requirement}
        Resume: {candidate_data}
        Return format: Score | Reason
        """
        response = ask_llama(prompt, system_role=self.system_role)
        return response.strip()

class JsonParserAgent:
    def __init__(self):
        self.system_role = "You are a JSON parsing expert. Extract and return only valid JSON from text."
    
    def parse_json_response(self, text):
        prompt = f"""
        Extract the JSON object from this text and return ONLY the valid JSON:
        {text}
        
        If no valid JSON is found, return {{"score": 50, "reason": "Unable to parse"}}
        """
        response = ask_llama(prompt, system_role=self.system_role)
        try:
            return json.loads(response.strip())
        except:
            return {"score": 50, "reason": "JSON parsing failed"}

class GraphNodes:
    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path="./company_knowledge")
        self.collection = self.chroma_client.get_collection(name="hiring_policies")

    def retrieval_node(self, state: dict):
        # Step 1: Get Company Knowledge (RAG)
        query_emb = ollama.embeddings(model="llama2", prompt=state['job_description'])["embedding"]
        results = self.collection.query(query_embeddings=[query_emb], n_results=3)
        return {"relevant_policies": results.get("documents", [[]])[0]}

    def memory_node(self, state: dict):
        # Step 2: Check Past Behavior (Memory)
        print("--- DEBUG: Entering Memory Node ---")
        history = db.get_candidate_history(state['form_data']['email'])
        formatted_history = [{"job": h[0], "score": h[1], "reason": h[2]} for h in history]
        print(f"--- DEBUG: Memory Node Found {len(history)} past apps ---")
        return {"candidate_history": formatted_history}

    def scorer_node(self, state: dict):
        print("--- EXECUTING SCORER NODE ---")
        
        # 1. Define the Contexts
        policy_context = "\n".join([f"- {p}" for p in state.get('relevant_policies', [])])
        history_context = "New Applicant"
        if state.get('candidate_history'):
            history_context = "\n".join([f"- Previous Job: {h['job']} (Score: {h['score']})" for h in state['candidate_history']])
        
        critique_context = ""
        if state.get('errors'):
            critique_context = f"\nJUDGE FEEDBACK: {state['errors'][-1]}"

        # 2. Define the Prompt (Fixes the 'not defined' error)
        prompt = f"""
        Evaluate candidate: {state['form_data']['name']}
        
        POLICIES: {policy_context}
        HISTORY: {history_context}
        {critique_context}
        
        RESUME: {state['resume_text']}
        
        TASK: Return ONLY a JSON object in this exact format: {{"score": 85, "reason": "Good fit for the role"}}
        Do not include any other text, explanations, or formatting.
        """

        # 3. Call the Model
        try:
            response = ask_llama(prompt, system_role="You are a Recruitment Agent.")
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return {
                    "score": int(data.get('score', 50)), 
                    "reason": data.get('reason', 'N/A'), 
                    "attempts": state["attempts"] + 1
                }
            else:
                # If regex fails, use JsonParserAgent
                parser = JsonParserAgent()
                data = parser.parse_json_response(response)
                return {
                    "score": int(data.get('score', 50)), 
                    "reason": data.get('reason', 'Parsed by agent'), 
                    "attempts": state["attempts"] + 1
                }
        except Exception as e:
            print(f"Scorer Error: {e}")
            return {"errors": [str(e)], "attempts": state["attempts"] + 1}
        
    def judge_node(self, state: dict):
        # Step 4: Compliance Check (LLM-as-a-Judge)
        policies = "\n".join(state['relevant_policies'])
        prompt = f"""
        Does this evaluation violate company policy?
        SCORE: {state['score']} | POLICIES: {policies}
        Return ONLY JSON: {{"is_compliant": true/false, "critique": "..."}}
        """
        res = ask_llama(prompt, system_role="You are a Compliance Judge.")
        # Safer parsing inside judge_node
        try:
            data = json.loads(re.search(r'\{.*\}', res, re.DOTALL).group(0))
            # Using .get() prevents crashes if the key is missing
            if not data.get('is_compliant', True): 
                return {"decision": "retry", "errors": state.get('errors', []) + [data.get('critique', 'Policy violation')]}
            return {"decision": "save"}
        except:
            return {"decision": "save"} # Fallback so the server doesn't crash
    
    
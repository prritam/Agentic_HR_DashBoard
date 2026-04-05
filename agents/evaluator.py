import json
import re
import chromadb
import ollama
from core.ollama_client import ask_llama

class GraphNodes:
    def __init__(self):
        self.system_role = "You are an AI Recruitment Specialist following strict company policies."
        # Connect to the database created by your indexer script
        self.chroma_client = chromadb.PersistentClient(path="./company_knowledge")
        self.collection = self.chroma_client.get_collection(name="hiring_policies")

    def retrieval_node(self, state: dict):
        """Step 1: Search the knowledge base for relevant rules."""
        print("--- EXECUTING RETRIEVAL NODE (RAG) ---")
        
        # Search using the job description to find matching rules
        query_text = f"{state['job_description']}"
        query_emb = ollama.embeddings(model="llama2", prompt=query_text)["embedding"]
        
        results = self.collection.query(
            query_embeddings=[query_emb], 
            n_results=3
        )
        
        policies = results.get("documents", [[]])[0]
        # Return the found policies to the shared state
        return {"relevant_policies": policies}

    def scorer_node(self, state: dict):
        """Step 2: Evaluate resume using retrieved policies."""
        print("--- EXECUTING SCORER NODE ---")
        
        policy_context = "\n".join([f"- {p}" for p in state['relevant_policies']])
        
        prompt = f"""
        Evaluate the candidate based on the Resume AND the Mandatory Company Policies.
        
        MANDATORY POLICIES:
        {policy_context}
        
        JOB DESCRIPTION:
        {state['job_description']}
        
        RESUME TEXT:
        {state['resume_text']}
        
        TASK:
        1. Score 0-100.
        2. If a Mandatory Policy is violated, the score MUST be below 50.
        3. Return ONLY valid JSON: {{"score": 85, "reason": "Text..."}}
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
        """Step 3: Business logic validation."""
        print("--- EXECUTING VALIDATOR NODE ---")
        if state.get("errors") and len(state["errors"]) > state["attempts"] - 1:
            return {"decision": "retry"}
            
        return {"decision": "save"}
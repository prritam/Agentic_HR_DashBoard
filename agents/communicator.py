from core.ollama_client import ask_llama

class CommunicatorAgent:
    def __init__(self):
        self.system_role = "You are a professional HR Coordinator. Write clear, friendly emails."

    def draft_assessment(self, name, role):
        prompt = f"""
        Write a professional email to {name}. 
        They are shortlisted for the {role} position.
        Invite them to a technical assessment at this link: [https://assessment-link.com/test-101]
        Keep it concise (under 80 words). No subject line.
        """
        return ask_llama(prompt, system_role=self.system_role)

    def draft_interview(self, name, time_slot):
        prompt = f"""
        Write an interview invite for {name}. 
        Scheduled time: {time_slot}. 
        Format: Google Meet.
        Be professional and welcoming. No subject line.
        """
        return ask_llama(prompt, system_role=self.system_role)
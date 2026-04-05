import ollama

def ask_llama(prompt, system_role="You are a helpful HR assistant."):
    """Standardized way to call Llama2 via Ollama."""
    response = ollama.generate(
        model='llama2',
        system=system_role,
        prompt=prompt,
        options={"temperature": 0.2} # Low temperature for factual extraction
    )
    return response['response']
import core.database as db
from core.mailer import send_real_email

TOOL_REGISTRY = {
    "save_candidate": db.save_candidate,
    "send_email": send_real_email
}

def execute_tool(tool_name, arguments):
    if tool_name not in TOOL_REGISTRY:
        return f"Error: Tool '{tool_name}' is not available in the registry."

    try:
        # Execute the function with unpacked arguments
        result = TOOL_REGISTRY[tool_name](**arguments)
        return "Success"
    except Exception as e:
        return f"Error during execution: {str(e)}"
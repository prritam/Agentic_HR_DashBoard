import sys
import os

# This ensures Python looks at the directory containing main.py
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from core.database import init_db, save_candidate, get_leaderboard, create_job
    from agents.parser import ParserAgent
    from agents.evaluator import EvaluatorAgent
except ImportError as e:
    print(f"Import Error: {e}")
    print("\nDEBUG INFO:")
    print(f"Current Directory: {os.getcwd()}")
    print(f"Python Path: {sys.path}")
    sys.exit(1)

def process_new_application(resume_text, job_requirement, job_id):
    # Initialize agents
    parser = ParserAgent()
    evaluator = EvaluatorAgent()
    
    # Step 1 & 2: Parse Resume
    print("Agent 1 is extracting data...")
    candidate_data = parser.extract_info(resume_text)
    
    # Step 3: Evaluate against Job Requirement
    print(f"Agent 2 is scoring {candidate_data['name']}...")
    eval_result = evaluator.score_candidate(candidate_data, job_requirement)
    
    # Split the "Score | Reason" format from the Evaluator
    try:
        score_part, reason = eval_result.split('|')
        score = int(''.join(filter(str.isdigit, score_part)))
    except:
        score, reason = 0, "Evaluation format error"

    # Step 4: Save to DB (Binding the candidate)
    save_candidate(candidate_data, score, reason.strip(), job_id)
    print("Candidate successfully added to Leaderboard.")

if __name__ == "__main__":
    init_db()
    
    # HR Input
    jd = "Python developer with 2+ years exp and knowledge of SQL."
    job_id = create_job("Python Developer", jd, 2)
    
    # Simulated LinkedIn Form Submission
    resume_input = """
    Pritam Mane. Email: p.mane@email.com. Exp: 3 years Python, FastAPI. 
    Current CTC: 8L. Expected: 12L. Notice: 30 days.
    """
    
    process_new_application(resume_input, jd, job_id)
    
    # Show Leaderboard
    print("\n--- HR DASHBOARD: CANDIDATE LEADERBOARD ---")
    for rank, (name, score, reason) in enumerate(get_leaderboard(), 1):
        print(f"{rank}. {name} | Score: {score}/100 | {reason}")
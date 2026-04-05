import sqlite3
import uuid

DB_NAME = "hr_agentic.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS jobs 
            (job_id TEXT PRIMARY KEY, title TEXT, description TEXT, required_experience INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS candidates 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT, name TEXT, email TEXT, mobile TEXT,
             current_employer TEXT, current_ctc REAL, expected_ctc REAL, notice_period TEXT, 
             last_working_day TEXT, ai_score INTEGER, ai_justification TEXT)''')
        conn.commit()

def create_job(title, description, experience):
    job_id = str(uuid.uuid4())[:8]
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO jobs VALUES (?, ?, ?, ?)", (job_id, title, description, experience))
        conn.commit()
    return job_id

def get_job(job_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT title, description, required_experience FROM jobs WHERE job_id = ?", (job_id,))
        return cursor.fetchone()

def get_candidate_history(email):
    # Retrieve past applications to check for consistency
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT job_id, ai_score, ai_justification FROM candidates WHERE email = ?", (email,))
        return cursor.fetchall()

def save_candidate(data, score, reason, job_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO candidates (job_id, name, email, mobile, current_employer, 
            current_ctc, expected_ctc, notice_period, last_working_day, ai_score, ai_justification)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
            (job_id, data['name'], data['email'], data['mobile'], data['current_employer'],
             data['current_ctc'], data['expected_ctc'], data['notice_period'], 
             data['last_working_day'], score, reason))
        conn.commit()

def get_leaderboard():
    """
    Retrieves all candidates from the database, ordered by their AI score.
    Used by dashboard.py to display the HR table.
    """
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Ensure the column names match exactly what your dashboard.py expects
        cursor.execute("""
            SELECT c.name, c.ai_score, c.ai_justification, c.email, c.last_working_day, j.title
            FROM candidates c
            JOIN jobs j ON c.job_id = j.job_id
            ORDER BY c.ai_score DESC
        """)
        return cursor.fetchall()
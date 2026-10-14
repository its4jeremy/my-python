import sqlite3
import json

def create_database():
    conn = sqlite3.connect("pastpapers.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_code TEXT,
            year TEXT,
            season TEXT,
            paper_number TEXT,
            syllabus_section TEXT,
            question_number TEXT,
            topic TEXT,
            subtopic TEXT,
            question_text TEXT,
            mark_scheme TEXT,
            key_phrases TEXT,
            common_mistakes TEXT,
            marks INTEGER
        )
    """)

    conn.commit()
    conn.close()
    print("Database created successfully.")

def insert_questions(data, paper_code, year, season, paper_number):
    conn = sqlite3.connect("pastpapers.db")
    cursor = conn.cursor()

    for q in data:
        cursor.execute("""
            INSERT INTO questions (
                paper_code, year, season, paper_number, 
                syllabus_section, question_number, topic, subtopic, question_text,
                mark_scheme, key_phrases, common_mistakes, marks
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            paper_code,
            year,
            season,
            paper_number,
            q.get("syllabus_section"),
            q.get("question_number"),
            q.get("topic"),
            q.get("subtopic"),
            q.get("question_text"),
            q.get("mark_scheme"),
            json.dumps(q.get("key_phrases", [])),
            json.dumps(q.get("common_mistakes", [])),
            q.get("marks")
        ))

    conn.commit()
    conn.close()
    print(f"Inserted {len(data)} questions into the database.")

# Run it
create_database()

with open("output.json", "r", encoding="utf-8") as f:
    data = json.load(f)

insert_questions(data, 
    paper_code="9618",
    year="2025",
    season="October/November",
    paper_number="31"
)

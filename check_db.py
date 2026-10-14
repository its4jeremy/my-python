import sqlite3
import json

conn = sqlite3.connect("pastpapers.db")
cursor = conn.cursor()

# Count total questions
cursor.execute("SELECT COUNT(*) FROM questions")
print(f"Total questions: {cursor.fetchone()[0]}")

# Show all unique topics
print("\nTopics in database:")
cursor.execute("SELECT DISTINCT topic FROM questions")
for row in cursor.fetchall():
    print(f"  - {row[0]}")

# Show one full question
print("\nSample question:")
cursor.execute("SELECT * FROM questions WHERE id = 1")
row = cursor.fetchone()
columns = [desc[0] for desc in cursor.description]
for col, val in zip(columns, row):
    if col in ("key_phrases", "common_mistakes"):
        print(f"  {col}: {json.loads(val)}")
    else:
        print(f"  {col}: {val}")

conn.close()

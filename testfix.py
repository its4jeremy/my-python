import json

with open("output.json", "r") as f:
    response_text = f.read()

clean_text = response_text.strip()
if clean_text.startswith("```"):
    clean_text = clean_text.split("\n", 1)[1]
if clean_text.endswith("```"):
    clean_text = clean_text.rsplit("```", 1)[0]

questions = json.loads(clean_text)
print(f"Extracted {len(questions)} questions.")
print(json.dumps(questions[0], indent=2))

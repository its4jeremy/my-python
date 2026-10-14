import pdfplumber
import anthropic
import json

def extract_text(filepath):
    text = ""
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def analyse_paper(qp_path, ms_path):
    print("Extracting text from PDFs...")
    qp_text = extract_text(qp_path)
    ms_text = extract_text(ms_path)

    client = anthropic.Anthropic()

    prompt = f"""You are processing a Cambridge A Level Computer Science (9618) past paper.

Below is the full question paper and mark scheme for one paper.

Your job is to:
1. Identify each question and sub-question
2. Match it with its mark scheme answer
3. Return a JSON array where each item represents one sub-question

For each sub-question return:
- question_number: e.g. "1(a)(i)"
- syllabus_section: the section number e.g. "13.1"
- topic: the EXACT Cambridge 9618 syllabus topic name e.g. "Data Representation"
- subtopic: the EXACT syllabus subtopic e.g. "User-defined data types"
- question_text: the full question text
- mark_scheme: the full mark scheme answer including all mark points
- key_phrases: list of exact words/phrases a student MUST include to score marks
- common_mistakes: what students typically write that won't score marks
- marks: the number of marks available

Use ONLY these official syllabus sections and topics for Paper 3:
13.1 - Data Representation - User-defined data types
13.2 - Data Representation - File organisation and access
13.3 - Data Representation - Floating-point numbers, representation and manipulation
14.1 - Communication and internet technologies - Protocols
14.2 - Communication and internet technologies - Circuit switching, packet switching
15.1 - Hardware and Virtual Machines - Processors, Parallel Processing and Virtual Machines
15.2 - Hardware and Virtual Machines - Boolean Algebra and Logic Circuits
16.1 - System Software - Purposes of an Operating System
16.2 - System Software - Translation Software
17.1 - Security - Encryption, Encryption Protocols and Digital Certificates
18.1 - Artificial Intelligence - Artificial Intelligence
19.1 - Computational thinking and Problem-solving - Algorithms
19.2 - Computational thinking and Problem-solving - Recursion
20.1 - Further Programming - Programming Paradigms
20.2 - Further Programming - File Processing and Exception Handling
- question_text: the full question text
- mark_scheme: the full mark scheme answer including all mark points
- key_phrases: list of exact words/phrases a student MUST include to score marks
- common_mistakes: what students typically write that won't score marks
- marks: the number of marks available

Return ONLY a valid JSON array, no other text.

QUESTION PAPER:
{qp_text}

MARK SCHEME:
{ms_text}
"""

    print("Sending to Claude for analysis...")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text

    print("Saving results...")
    # Strip markdown code fences if present
    clean_text = response_text.strip()
    if clean_text.startswith("```"):
        clean_text = clean_text.split("\n", 1)[1]  # remove first line
    if clean_text.endswith("```"):
        clean_text = clean_text.rsplit("```", 1)[0]  # remove last fence

    with open("output.json", "w", encoding="utf-8") as f:
        f.write(clean_text)

    questions = json.loads(clean_text)
    print(f"\nDone! Extracted {len(questions)} questions.")
    print("\nFirst question preview:")
    print(json.dumps(questions[0], indent=2))

# Run it
analyse_paper(
    "papers/9618/paper_3/9618_w25_qp_31.pdf",
    "papers/9618/paper_3/9618_w25_ms_31.pdf"
)

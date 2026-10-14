import anthropic

# Sample mark scheme question (Biology IGCSE style)
question = """
Question: Explain why the rate of photosynthesis increases as light intensity increases, 
up to a certain point.

Mark Scheme:
- more light energy available for the light-dependent reactions (1)
- more ATP / reduced NADP produced (1)
- rate limited by another factor e.g. CO2 concentration / temperature (1)
"""

client = anthropic.Anthropic()  # automatically picks up your API key

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": f"""You are an expert IGCSE/A-level exam coach.

Analyse this past paper question and mark scheme, then return:
1. TOPIC: The specific syllabus topic this question tests
2. KEY PHRASES: The exact words/phrases a student MUST include to score marks
3. COMMON MISTAKES: What students typically write that doesn't score marks
4. STUDENT TIP: One sentence advice on how to phrase answers for this type of question

Here is the question and mark scheme:
{question}"""
        }
    ]
)

print(message.content[0].text)

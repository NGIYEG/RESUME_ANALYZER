from transformers import pipeline

print("Loading NLP model...")
resume_nlp = pipeline(
    "text2text-generation",
    model="google/flan-t5-base"
)

def extract_insights(text):
    prompt = f"""
    Extract this resume into structured JSON with fields:
    - skills (list)
    - work_experience (list)
    - projects (list)
    - education (list)

    Resume text:
    {text}
    """

    result = resume_nlp(prompt, max_length=512)[0]["generated_text"]

    # Ensure JSON output
    import json
    try:
        data = json.loads(result)
    except:
        data = {"error": "Invalid JSON", "raw": result}

    return data

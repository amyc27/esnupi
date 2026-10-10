
import os
import json
from google import genai
from google.genai import types


PASSING_SCORE = 70
MODEL_NAME = "gemini-3.6-flash"


def evaluate_explanation(topic, student_answer):
    """Evaluate a student's explanation using Gemini."""

    # Handle empty answers without calling the AI.
    if not student_answer or not student_answer.strip():
        return {
            "topic": topic,
            "score": 0,
            "feedback": (
                "Please try explaining the topic in your own words. "
                "Start with one thing you remember."
            ),
            "strengths": [],
            "missing_concepts": [],
            "passed": False
        }

    # Read the API key from the environment.
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. "
            "Please configure your API key first."
        )

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an educational evaluator for onTrack.

Evaluate the student's understanding of the topic fairly.
Accept correct explanations in the student's own words.
Do not reward length alone, and do not invent mistakes.

TOPIC: {topic}

STUDENT EXPLANATION:
{student_answer}

Use this scoring rubric:
- Accuracy: 0 to 40 points
- Understanding of key concepts: 0 to 30 points
- Completeness: 0 to 20 points
- Clarity: 0 to 10 points

Award points only for knowledge demonstrated in the answer.
A short but accurate explanation can earn a good score.

Return only valid JSON with these fields:
{{
  "score": integer from 0 to 100,
  "feedback": "specific, encouraging feedback",
  "strengths": ["concepts explained correctly"],
  "missing_concepts": ["important concepts not explained"]
}}

Do not include the passed field. Python will calculate pass status.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    # Parse and validate the AI's response.
    if not response.text:
        raise RuntimeError("The AI returned an empty response.")

    result = json.loads(response.text)

    score = int(result.get("score", 0))
    score = max(0, min(100, score))

    # Python, not the AI, decides whether the student passes.
    result["score"] = score
    result["passed"] = score >= PASSING_SCORE
    result["topic"] = topic

    # Ensure expected fields exist.
    result.setdefault("feedback", "Review the topic and try again.")
    result.setdefault("strengths", [])
    result.setdefault("missing_concepts", [])

    return result


if __name__ == "__main__":
    topic = "Photosynthesis"
    answer = "Photosynthesis is when plants breathe."

    try:
        result = evaluate_explanation(topic, answer)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as error:
        print("Evaluation failed:", error)

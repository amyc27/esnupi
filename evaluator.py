
import os
import json
from google import genai
from google.genai import types

PASSING_SCORE = 70
MODEL_NAME = "gemini-3.6-flash"


def evaluate_explanation(topic, student_answer):
    """Evaluate a student's explanation using Gemini."""

    if not isinstance(student_answer, str) or not student_answer.strip():
        return {
            "topic": topic,
            "score": 0,
            "feedback": "Please explain the topic in your own words.",
            "strengths": [],
            "missing_concepts": [],
            "passed": False
        }

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an educational evaluator for onTrack.
Evaluate the student's understanding fairly.
Accept correct explanations in their own words.
Do not reward length alone or invent mistakes.

TOPIC: {topic}
STUDENT EXPLANATION: {student_answer}

Scoring rubric:
- Accuracy: 0 to 40 points
- Understanding of key concepts: 0 to 30 points
- Completeness: 0 to 20 points
- Clarity: 0 to 10 points

Return only valid JSON:
{{
  "score": integer from 0 to 100,
  "feedback": "specific, encouraging feedback",
  "strengths": ["correctly explained concepts"],
  "missing_concepts": ["important concepts not explained"]
}}
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        if not response.text:
            raise RuntimeError("Gemini returned an empty response.")

        result = json.loads(response.text)

        score = int(result.get("score", 0))
        score = max(0, min(100, score))

        result["score"] = score
        result["passed"] = score >= PASSING_SCORE
        result["topic"] = topic
        result.setdefault("feedback", "Please review the topic.")
        result.setdefault("strengths", [])
        result.setdefault("missing_concepts", [])

        return result

    except Exception as error:
        # Do not turn failed evaluations into passing results.
        raise RuntimeError(
            f"AI evaluation failed: {error}"
        ) from error


if __name__ == "__main__":
    topic = "Photosynthesis"
    answer = (
        "Plants use sunlight, water, and carbon dioxide to make "
        "glucose and release oxygen. Chlorophyll captures light energy."
    )

    try:
        result = evaluate_explanation(topic, answer)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as error:
        print(error)

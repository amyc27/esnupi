import os
import json
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

PASSING_SCORE = 70
PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
FALLBACK_MODELS = ["gemini-3.6-flash", "gemini-flash-latest"]


def evaluate_explanation(topic, student_answer):
    """Evaluate a student's explanation using Gemini."""

    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("A valid topic string is required.")

    if not isinstance(student_answer, str) or not student_answer.strip():
        return {
            "topic": topic.strip(),
            "score": 0,
            "feedback": "Please explain the topic in your own words.",
            "strengths": [],
            "missing_concepts": [],
            "passed": False
        }

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as rkey:
                api_key, _ = winreg.QueryValueEx(rkey, "GEMINI_API_KEY")
        except Exception:
            pass

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an educational evaluator for onTrack.
Evaluate the student's understanding fairly.
Accept correct explanations in their own words.
Do not reward length alone or invent mistakes.

TOPIC: {topic.strip()}
STUDENT EXPLANATION: {student_answer.strip()}

Scoring rubric:
- Accuracy: 0 to 40 points
- Understanding of key concepts: 0 to 30 points
- Completeness: 0 to 20 points
- Clarity: 0 to 10 points

Return only valid JSON in the following exact format:
{{
  "score": integer from 0 to 100,
  "feedback": "specific, encouraging feedback",
  "strengths": ["correctly explained concepts"],
  "missing_concepts": ["important concepts not explained"]
}}
"""

    models_to_try = [PRIMARY_MODEL] + [m for m in FALLBACK_MODELS if m != PRIMARY_MODEL]
    last_error = None

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )

            raw_text = response.text or ""
            text = raw_text.strip()
            if text.startswith("```json"):
                text = text[len("```json"):].strip()
            elif text.startswith("```"):
                text = text[len("```"):].strip()
            if text.endswith("```"):
                text = text[:-3].strip()

            if not text:
                raise RuntimeError("Gemini returned an empty response.")

            result = json.loads(text)

            try:
                score = int(round(float(result.get("score", 0))))
            except (ValueError, TypeError):
                score = 0
            score = max(0, min(100, score))

            strengths = result.get("strengths")
            if not isinstance(strengths, list):
                strengths = [str(strengths)] if strengths else []
            else:
                strengths = [str(s) for s in strengths if s]

            missing_concepts = result.get("missing_concepts")
            if not isinstance(missing_concepts, list):
                missing_concepts = [str(missing_concepts)] if missing_concepts else []
            else:
                missing_concepts = [str(m) for m in missing_concepts if m]

            feedback = result.get("feedback")
            if not isinstance(feedback, str) or not feedback.strip():
                feedback = "Please review the topic and try again."

            return {
                "topic": topic.strip(),
                "score": score,
                "passed": score >= PASSING_SCORE,
                "feedback": feedback,
                "strengths": strengths,
                "missing_concepts": missing_concepts,
            }

        except Exception as error:
            last_error = error
            logger.warning("Generation failed with model %s: %s", model_name, error)

    # Do not fake evaluation results or return passing score on failure
    raise RuntimeError(f"AI evaluation failed: {last_error}") from last_error


if __name__ == "__main__":
    test_topic = "Photosynthesis"
    test_answer = (
        "Plants use sunlight, water, and carbon dioxide to make "
        "glucose and release oxygen. Chlorophyll captures light energy."
    )

    try:
        res = evaluate_explanation(test_topic, test_answer)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    except Exception as err:
        print(f"Evaluation failed: {err}")

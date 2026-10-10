
def evaluate_explanation(topic, student_answer):
    """Give basic feedback on a student's explanation."""

    if not student_answer.strip():
        return {
            "score": 0,
            "feedback": "Try explaining the topic in your own words.",
            "passed": False
        }

    return {
        "topic": topic,
        "student_answer": student_answer,
        "score": 0,
        "feedback": "Your answer has been received. AI evaluation comes next!",
        "passed": False
    }


# Test the function
result = evaluate_explanation(
    "Photosynthesis",
    "Plants use sunlight to make their food."
)

print(result)



from flask import Flask, request, jsonify
from evaluator import evaluate_explanation

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "onTrack AI Evaluation API is running"
    })


@app.route("/evaluate", methods=["POST"])
def evaluate():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Send a JSON object with topic and answer."
        }), 400

    topic = data.get("topic")
    answer = data.get("answer")

    if not isinstance(topic, str) or not topic.strip():
        return jsonify({"error": "A topic is required."}), 400

    if not isinstance(answer, str):
        return jsonify({"error": "Answer must be text."}), 400

    if len(topic) > 300 or len(answer) > 10000:
        return jsonify({"error": "Input is too long."}), 400

    try:
        result = evaluate_explanation(topic, answer)
        return jsonify(result), 200

    except Exception:
        app.logger.exception("Evaluation failed")
        return jsonify({
            "error": "Evaluation is temporarily unavailable. Please try again."
        }), 503


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)

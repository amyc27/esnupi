import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from evaluator import evaluate_explanation

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Configure CORS to allow local development (e.g. 127.0.0.1:5500) and deployed origins
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
else:
    allowed_origins = "*"

CORS(
    app,
    resources={
        r"/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    }
)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "onTrack AI Evaluation API is running"
    })


@app.route("/evaluate", methods=["POST", "OPTIONS"])
def evaluate():
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Send a JSON object with topic and answer."
        }), 400

    topic = data.get("topic")
    answer = data.get("answer")

    if not isinstance(topic, str) or not topic.strip():
        return jsonify({"error": "A topic is required."}), 400

    if not isinstance(answer, str) or not answer.strip():
        return jsonify({"error": "Answer must be non-empty text."}), 400

    if len(topic) > 300 or len(answer) > 10000:
        return jsonify({"error": "Input is too long."}), 400

    try:
        result = evaluate_explanation(topic.strip(), answer.strip())
        return jsonify(result), 200

    except ValueError as ve:
        app.logger.warning("Validation error during evaluation: %s", ve)
        return jsonify({"error": str(ve)}), 400

    except Exception as err:
        app.logger.exception("Evaluation failed: %s", err)
        return jsonify({
            "error": "Evaluation is temporarily unavailable. Please try again."
        }), 503


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

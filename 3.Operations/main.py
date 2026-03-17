import pickle
import json
import numpy as np
import logging
from flask import Flask, redirect, render_template, request, jsonify
from flask_wtf import CSRFProtect
from flask_csp.csp import csp_header

app_log = logging.getLogger(__name__)
logging.basicConfig(
    filename="security_log.log",
    encoding="utf-8",
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
)

app = Flask(__name__)
app.secret_key = b"_53oi3uriq9pifpff;apl"
csrf = CSRFProtect(app)

MODEL_PATH = "my_saved_model.sav"
SCALING_PATH = "scaling_params.json"

BIOME_MAP = {
    0: "beach",
    1: "birch_forest",
    2: "dark_forest",
    3: "forest",
    4: "meadow",
    5: "ocean",
    6: "plains",
    7: "river",
    8: "swamp",
    9: "taiga",
    10: "windswept_gravelly_hills",
    11: "windswept_savanna",
}

# Load model and scaling params once at startup
model = pickle.load(open(MODEL_PATH, "rb"))
scaling_params = json.load(open(SCALING_PATH, "r"))
FEATURES = list(scaling_params.keys())


def scale_input(raw_data: dict) -> np.ndarray:
    scaled = []
    for feature in FEATURES:
        value = raw_data.get(feature, 0.0)
        min_val = scaling_params[feature]["min"]
        max_val = scaling_params[feature]["max"]
        if max_val - min_val > 0:
            scaled_value = (value - min_val) / (max_val - min_val)
        else:
            scaled_value = 0.0
        scaled.append(max(0.0, min(1.0, scaled_value)))
    return np.array([scaled])


# Redirect common index variants to root
@app.route("/index", methods=["GET"])
@app.route("/index.htm", methods=["GET"])
@app.route("/index.asp", methods=["GET"])
@app.route("/index.php", methods=["GET"])
@app.route("/index.html", methods=["GET"])
def root():
    return redirect("/", 302)


# Serve the HTML page with CSP headers
@app.route("/", methods=["GET"])
@csp_header(
    {
        "base-uri": "'self'",
        "default-src": "'self'",
        "style-src": "'self'",
        "script-src": "'self'",
        "img-src": "'self' data:",
        "media-src": "'self'",
        "font-src": "'self'",
        "object-src": "'self'",
        "child-src": "'self'",
        "connect-src": "'self'",
        "worker-src": "'self'",
        "report-uri": "/csp_report",
        "frame-ancestors": "'none'",
        "form-action": "'self'",
        "frame-src": "'none'",
    }
)
def index():
    return render_template("index.html", features=scaling_params)


# API endpoint for prediction
@app.route("/predict", methods=["POST"])
@csrf.exempt
def predict():
    raw_data = request.get_json()
    if not raw_data:
        app.logger.warning("Predict called with no data")
        return jsonify({"error": "No data provided"}), 400

    # Check for out-of-range values before scaling
    warnings = []
    for feature in FEATURES:
        value = raw_data.get(feature, 0.0)
        max_val = scaling_params[feature]["max"]
        if value > max_val:
            warnings.append(f"{feature} ({value} exceeds max of {int(max_val)})")

    inputs = scale_input(raw_data)
    prediction = model.predict(inputs)[0]
    confidence = round(max(model.predict_proba(inputs)[0]) * 100, 1)
    biome = BIOME_MAP.get(prediction, "unknown")
    app.logger.info(f"Prediction: {biome} ({confidence}%)")

    return jsonify(
        {
            "biome": biome,
            "confidence": confidence,
            "warnings": warnings,  # empty list if no issues
        }
    )


# Endpoint for logging CSP violations
@app.route("/csp_report", methods=["POST"])
@csrf.exempt
def csp_report():
    app.logger.critical(request.data.decode())
    return "done"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)

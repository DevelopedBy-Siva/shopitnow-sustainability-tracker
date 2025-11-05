from flask import Blueprint, request, jsonify
import joblib
import pandas as pd
import os

predict_bp = Blueprint("predict", __name__)

BASE_DIR = os.path.dirname(__file__)

eco_model_path = os.path.abspath(
    os.path.join(BASE_DIR, "..", "model", "eco_score_model.pkl")
)
emission_model_path = os.path.abspath(
    os.path.join(BASE_DIR, "..", "model", "emission_model.pkl")
)

eco_model = joblib.load(eco_model_path)
emission_model = joblib.load(emission_model_path)


@predict_bp.route("/predict", methods=["POST"])
def predict_sustainability():
    data = request.get_json()

    category = data.get("category")
    material = data.get("material")
    weight = data.get("weight")
    price = data.get("price")

    if not all([category, material, weight, price]):
        return jsonify({"error": "Missing required fields"}), 400

    df = pd.DataFrame(
        [{"category": category, "material": material, "weight": weight, "price": price}]
    )

    eco_pred = eco_model.predict(df)[0]
    emission_pred = emission_model.predict(df)[0]

    return jsonify(
        {
            "predicted_eco_score": round(float(eco_pred), 2),
            "predicted_emission_factor": round(float(emission_pred), 2),
        }
    )

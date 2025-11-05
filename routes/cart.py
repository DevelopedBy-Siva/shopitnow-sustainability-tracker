from flask import Blueprint, request, jsonify
from models import SustainProduct
from utils.calculator import estimate_emission, calculate_savings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

cart_bp = Blueprint("cart", __name__)


@cart_bp.route("/cart", methods=["POST"])
def cart_optimize():
    data = request.get_json()
    items = data.get("cart_items", [])

    if not items:
        return jsonify({"error": "No items provided"}), 400

    optimized_cart = []
    total_current_co2 = 0.0
    total_optimized_co2 = 0.0

    for item in items:
        product = SustainProduct.query.filter_by(product_id=item["id"]).first()
        if not product:
            continue

        qty = item.get("qty", 1)
        co2 = estimate_emission(product.emission_factor, product.weight, qty, 100)
        total_current_co2 += co2

        candidates = SustainProduct.query.filter_by(category=product.category).all()
        if not candidates:
            continue

        df = pd.DataFrame(
            [
                {
                    "id": p.product_id,
                    "title": p.title or "",
                    "material": p.material or "",
                    "eco_score": p.eco_score,
                    "emission_factor": p.emission_factor,
                    "weight": p.weight,
                }
                for p in candidates
            ]
        )

        df["text"] = (
            (df["title"] + " " + df["material"])
            .str.lower()
            .str.replace(",", " ", regex=False)
        )
        tfidf = TfidfVectorizer(max_features=100)
        tfidf_matrix = tfidf.fit_transform(df["text"])
        base_vec = tfidf_matrix[df.index[df["id"] == product.product_id][0]].reshape(
            1, -1
        )
        df["similarity"] = cosine_similarity(base_vec, tfidf_matrix).flatten()

        base_eco = product.eco_score
        df["eco_gain"] = df["eco_score"] - base_eco
        df["green_score"] = (df["similarity"] * 0.6) + (df["eco_gain"] * 0.4)
        df = df[(df["id"] != product.product_id) & (df["eco_gain"] > 0)]
        df = df.sort_values(by="green_score", ascending=False)

        if not df.empty:
            rec = df.iloc[0]
            greener = SustainProduct.query.filter_by(product_id=int(rec["id"])).first()
            co2_g = estimate_emission(greener.emission_factor, greener.weight, qty, 100)
            total_optimized_co2 += co2_g
            saving = calculate_savings(co2, co2_g)

            optimized_cart.append(
                {
                    "original": {
                        "id": product.product_id,
                        "title": product.title,
                        "eco_score": round(float(product.eco_score), 2),
                        "emission_factor": round(float(product.emission_factor), 2),
                        "co2_kg": round(co2, 2),
                    },
                    "suggested": {
                        "id": greener.product_id,
                        "title": greener.title,
                        "eco_score": round(float(greener.eco_score), 2),
                        "emission_factor": round(float(greener.emission_factor), 2),
                        "co2_kg": round(co2_g, 2),
                        "co2_saved_kg": round(saving, 2),
                        "similarity": round(float(rec["similarity"]), 2),
                        "green_score": round(float(rec["green_score"]), 2),
                    },
                }
            )
        else:
            total_optimized_co2 += co2
            optimized_cart.append(
                {
                    "original": {
                        "id": product.product_id,
                        "title": product.title,
                        "eco_score": round(float(product.eco_score), 2),
                        "emission_factor": round(float(product.emission_factor), 2),
                        "co2_kg": round(co2, 2),
                    },
                    "suggested": None,
                }
            )

    total_saved = calculate_savings(total_current_co2, total_optimized_co2)

    return jsonify(
        {
            "cart_summary": {
                "current_total_kg": round(total_current_co2, 2),
                "optimized_total_kg": round(total_optimized_co2, 2),
                "total_saved_kg": round(total_saved, 2),
                "impact_message": f"🤖 AI Optimizer: Switching suggested items can save {round(total_saved,2)} kg CO₂ 🌿",
            },
            "recommendations": optimized_cart,
        }
    )

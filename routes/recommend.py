from flask import Blueprint, request, jsonify
from models import SustainProduct
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
from utils.calculator import estimate_emission, calculate_savings

recommend_bp = Blueprint("recommend", __name__)


def impact_tag(eco_score: float):
    if eco_score >= 8:
        return "green"
    elif eco_score >= 5:
        return "yellow"
    return "red"


def co2_equivalent_message(co2_kg: float, category: str, impact_tag: str):
    base_phrase = "per item manufactured and shipped 100 km"

    if "mobile" in category.lower() or "laptop" in category.lower():
        equivalent = f"≈ {int(co2_kg * 90)} phone charges ⚡"
    elif "fashion" in category.lower():
        equivalent = f"≈ {round(co2_kg * 0.5, 1)} washing cycles 🧺"
    elif "appliance" in category.lower():
        equivalent = f"≈ {round(co2_kg * 2.0, 1)} hours of fridge use ❄️"
    elif "kids" in category.lower():
        equivalent = f"≈ {round(co2_kg * 0.2, 1)} toy production cycles 🧸"
    else:
        equivalent = f"≈ {int(co2_kg * 80)} daily actions 🌍"

    if impact_tag == "green":
        tone = "Low-impact choice 🌱 — made with sustainable materials and efficient production."
    elif impact_tag == "yellow":
        tone = "Moderate impact 🌤️ — performs decently but can be greener."
    else:
        tone = "High impact ⚠️ — consider switching to a more sustainable alternative."

    return f"{equivalent} ({base_phrase}). {tone}"


@recommend_bp.route("/recommend/eco", methods=["GET"])
def recommend_eco():
    product_id = request.args.get("productId")
    k = int(request.args.get("k", 5))

    if not product_id:
        return jsonify({"error": "Missing productId"}), 400

    products = SustainProduct.query.all()
    if not products:
        return jsonify({"error": "No products found"}), 404

    df = pd.DataFrame(
        [
            {
                "id": p.product_id,
                "title": p.title or "",
                "category": p.category or "",
                "material": p.material or "",
                "weight": p.weight or 0.0,
                "emission_factor": p.emission_factor or 0.0,
                "eco_score": p.eco_score or 5.0,
            }
            for p in products
        ]
    )

    if int(product_id) not in df["id"].values:
        return jsonify({"error": "Product not found"}), 404

    df["text"] = (
        df["title"].fillna("")
        + " "
        + df["category"].fillna("")
        + " "
        + df["material"].fillna("")
    )

    df["text"] = df["text"].str.replace(",", " ", regex=False).str.lower().str.strip()
    tfidf = TfidfVectorizer(max_features=100)
    text_vecs = tfidf.fit_transform(df["text"]).toarray()

    scaler = MinMaxScaler()
    num_vecs = scaler.fit_transform(df[["eco_score", "emission_factor", "weight"]])

    X = np.hstack([text_vecs, num_vecs])

    base_idx = df.index[df["id"] == int(product_id)][0]
    base_vec = X[base_idx].reshape(1, -1)
    similarities = cosine_similarity(base_vec, X).flatten()
    df["similarity"] = similarities

    base = df.iloc[base_idx]

    df["eco_gain"] = (df["eco_score"] - base["eco_score"]) - (
        df["emission_factor"] - base["emission_factor"]
    ) * 0.2
    df["green_score"] = df["similarity"] * 0.6 + df["eco_gain"] * 0.4

    recs = df[
        (df["id"] != int(product_id))
        & (df["category"].str.lower() == base["category"].lower())
        & (df["eco_score"] > base["eco_score"] + 1)
    ]
    recs = recs.sort_values(by="green_score", ascending=False).head(k)

    base_co2 = estimate_emission(base["emission_factor"], base["weight"], 1, 100)
    base_tag = impact_tag(base["eco_score"])

    recommendations = []
    for _, r in recs.iterrows():
        co2 = estimate_emission(r["emission_factor"], r["weight"], 1, 100)
        saving = calculate_savings(base_co2, co2)
        tag = impact_tag(r["eco_score"])
        msg = co2_equivalent_message(co2, r["category"], tag)

        recommendations.append(
            {
                "id": int(r["id"]),
                "title": r["title"],
                "category": r["category"],
                "material": r["material"],
                "eco_score": float(r["eco_score"]),
                "emission_factor": float(r["emission_factor"]),
                "weight": float(r["weight"]),
                "score": round(float(r["green_score"]), 3),
                "co2_kg": co2,
                "co2_saved_kg": round(saving, 3),
                "impact_tag": tag,
                "impact_message": msg,
            }
        )

    return jsonify(
        {
            "base_product": {
                "id": int(base["id"]),
                "title": base["title"],
                "eco_score": float(base["eco_score"]),
                "emission_factor": float(base["emission_factor"]),
                "co2_kg": base_co2,
                "impact_tag": base_tag,
                "impact_message": co2_equivalent_message(
                    base_co2, base["category"], base_tag
                ),
            },
            "recommendations": recommendations,
        }
    )

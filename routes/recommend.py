# recommend_service.py
from flask import Blueprint, request, jsonify
from models import Product
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity

recommend_bp = Blueprint("recommend", __name__)


def build_embeddings(products):
    df = pd.DataFrame(
        [
            {
                "product_id": p.product_id,
                "name": p.name,
                "category": getattr(p, "category", ""),
                "material": p.material,
                "weight_kg": p.weight_kg,
                "emission_factor": p.emission_factor,
                "eco_score": p.eco_score,
            }
            for p in products
        ]
    )

    tfidf = TfidfVectorizer(max_features=100)
    df["text"] = (
        df["name"].fillna("")
        + " "
        + df["material"].fillna("")
        + " "
        + df["category"].fillna("")
    )
    text_vecs = tfidf.fit_transform(df["text"]).toarray()

    scaler = MinMaxScaler()
    num_vecs = scaler.fit_transform(df[["eco_score", "emission_factor", "weight_kg"]])

    X = np.hstack([text_vecs, num_vecs])
    return df, X


@recommend_bp.route("/recommend/eco", methods=["GET"])
def recommend_eco():
    product_id = request.args.get("productId")
    k = int(request.args.get("k", 5))

    if not product_id:
        return jsonify({"error": "Missing productId"}), 400

    products = Product.query.all()
    if not products:
        return jsonify({"error": "No products found"}), 404

    df, X = build_embeddings(products)
    ids = df["product_id"].tolist()
    if product_id not in ids:
        return jsonify({"error": f"Product {product_id} not found"}), 404

    base_idx = ids.index(product_id)
    base = df.iloc[base_idx]
    base_vec = X[base_idx].reshape(1, -1)

    sims = cosine_similarity(base_vec, X).flatten()

    df["similarity"] = sims
    df["eco_diff"] = df["eco_score"] - base["eco_score"]
    df["eco_benefit"] = (0.6 * df["similarity"]) + (0.4 * df["eco_diff"] / 10)

    mask = (df["eco_score"] > base["eco_score"]) & (df["product_id"] != product_id)
    recs = df[mask].sort_values(by="eco_benefit", ascending=False).head(k)

    return jsonify(
        {
            "base_product": {
                "product_id": base["product_id"],
                "name": base["name"],
                "eco_score": float(base["eco_score"]),
                "emission_factor": float(base["emission_factor"]),
            },
            "recommendations": [
                {
                    "product_id": r["product_id"],
                    "name": r["name"],
                    "material": r["material"],
                    "eco_score": float(r["eco_score"]),
                    "emission_factor": float(r["emission_factor"]),
                    "weight_kg": float(r["weight_kg"]),
                    "score": round(float(r["eco_benefit"]), 4),
                }
                for _, r in recs.iterrows()
            ],
        }
    )

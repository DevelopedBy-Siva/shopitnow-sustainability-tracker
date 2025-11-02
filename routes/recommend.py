# routes/recommend.py
from flask import Blueprint, request, jsonify
from models import SustainProduct
from utils.encoder import product_to_vector, cosine_sim

recommend_bp = Blueprint("recommend", __name__)


@recommend_bp.route("/recommend/eco", methods=["GET"])
def recommend_eco():
    product_id = request.args.get("productId")
    k = int(request.args.get("k", 5))

    if not product_id:
        return jsonify({"error": "productId required"}), 400

    base = SustainProduct.query.filter_by(product_id=product_id).first()
    if not base:
        return jsonify({"error": "Product not found"}), 404

    base_vec = product_to_vector(
        base.material, base.weight_kg, base.emission_factor, base.eco_score
    )

    candidates = SustainProduct.query.filter(
        SustainProduct.product_id != product_id
    ).all()
    scored = []

    for p in candidates:
        vec = product_to_vector(p.material, p.weight_kg, p.emission_factor, p.eco_score)
        sim = cosine_sim(base_vec, vec)

        eco_bonus = (p.eco_score / 10.0) - (p.emission_factor / 20.0)
        final_score = sim + 0.25 * eco_bonus

        scored.append(
            {
                "product_id": p.product_id,
                "name": p.name,
                "material": p.material,
                "weight_kg": p.weight_kg,
                "emission_factor": p.emission_factor,
                "eco_score": p.eco_score,
                "score": round(final_score, 4),
            }
        )

    greener = [
        s
        for s in scored
        if s["eco_score"] > base.eco_score
        or s["emission_factor"] < base.emission_factor
    ]
    primary = sorted(greener, key=lambda x: x["score"], reverse=True)[:k]

    if len(primary) < k:
        remaining = sorted(scored, key=lambda x: x["score"], reverse=True)
        chosen_ids = {x["product_id"] for x in primary}
        for cand in remaining:
            if len(primary) >= k:
                break
            if cand["product_id"] not in chosen_ids:
                primary.append(cand)

    return jsonify(
        {
            "base_product": {
                "product_id": base.product_id,
                "name": base.name,
                "eco_score": base.eco_score,
                "emission_factor": base.emission_factor,
            },
            "recommendations": primary[:k],
        }
    )

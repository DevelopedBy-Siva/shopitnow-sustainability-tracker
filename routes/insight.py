from flask import Blueprint, request, jsonify
from models import SustainProduct
from utils.calculator import estimate_emission
import statistics

insight_bp = Blueprint("insight", __name__)


def impact_tag(score):
    if score >= 8:
        return "green"
    elif score >= 5:
        return "yellow"
    return "red"


@insight_bp.route("/api/sustainability/insight", methods=["GET"])
def get_product_insight():
    product_id = request.args.get("productId")
    if not product_id:
        return jsonify({"error": "Missing productId"}), 400

    p = SustainProduct.query.filter_by(product_id=product_id).first()
    if not p:
        return jsonify({"error": "Product not found"}), 404

    products = SustainProduct.query.filter_by(category=p.category).all()
    avg = statistics.mean(
        estimate_emission(i.emission_factor, i.weight, 1, 100) for i in products
    )

    co2 = estimate_emission(p.emission_factor, p.weight, 1, 100)
    diff = ((avg - co2) / avg) * 100
    tag = impact_tag(p.eco_score)

    msg = (
        f"🪴 This product emits {co2:.2f} kg CO₂ per 100 km shipped — "
        f"{abs(diff):.1f}% {'cleaner' if diff>0 else 'higher'} than average. "
        + (
            "🌱 Eco-conscious choice!"
            if diff > 0
            else "⚠️ Consider greener alternatives."
        )
    )

    return jsonify(
        {
            "product_id": product_id,
            "category": p.category,
            "eco_score": p.eco_score,
            "impact_tag": tag,
            "co2_kg": round(co2, 2),
            "difference_pct": round(diff, 1),
            "impact_message": msg,
        }
    )

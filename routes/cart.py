from flask import Blueprint, request, jsonify
from models import SustainProduct
from utils.calculator import estimate_emission, calculate_savings

cart_bp = Blueprint("cart", __name__)


@cart_bp.route("/cart-insight", methods=["POST"])
def cart_insight():
    data = request.get_json()
    items = data.get("cart_items", [])

    if not items:
        return jsonify({"error": "No items provided"}), 400

    total_co2 = 0.0
    total_save = 0.0
    for item in items:
        product = SustainProduct.query.filter_by(product_id=item["id"]).first()
        if not product:
            continue
        co2 = estimate_emission(
            product.emission_factor, product.weight, item.get("qty", 1), 100
        )
        total_co2 += co2
        if product.eco_score < 8:
            greener = (
                SustainProduct.query.filter_by(category=product.category)
                .filter(SustainProduct.eco_score > product.eco_score)
                .order_by(SustainProduct.eco_score.desc())
                .first()
            )
            if greener:
                co2_green = estimate_emission(
                    greener.emission_factor, greener.weight, 1, 100
                )
                total_save += calculate_savings(co2, co2_green)

    return jsonify(
        {
            "total_cart_co2_kg": round(total_co2, 2),
            "potential_savings_kg": round(total_save, 2),
            "impact_message": f"Your cart emits ~{round(total_co2,2)} kg CO₂. Switching to eco items can save {round(total_save,2)} kg 🌍",
        }
    )

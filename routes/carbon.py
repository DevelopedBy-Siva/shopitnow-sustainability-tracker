from flask import Blueprint, request, jsonify
from models import SustainProduct
from utils.calculator import estimate_emission

carbon_bp = Blueprint("carbon", __name__)


@carbon_bp.route("/carbon/estimate", methods=["GET"])
def estimate_carbon():
    product_id = request.args.get("productId")
    qty = float(request.args.get("qty", 1))
    distance = float(request.args.get("distance", 100))

    if not product_id:
        return jsonify({"error": "Missing productId"}), 400

    product = SustainProduct.query.filter_by(product_id=product_id).first()
    if not product:
        return jsonify({"error": "Product not found"}), 404

    co2 = estimate_emission(product.emission_factor, product.weight_kg, qty, distance)
    return jsonify(
        {
            "product_id": product_id,
            "product_name": product.name,
            "co2_kg": co2,
            "equivalent": f"≈ {int(co2*90)} phone charges",
        }
    )

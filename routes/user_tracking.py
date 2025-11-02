from flask import Blueprint, request, jsonify
from models import db, SustainOrder, SustainUser, SustainProduct
from utils.calculator import estimate_emission, calculate_savings

user_bp = Blueprint("user_tracking", __name__)


@user_bp.route("/order", methods=["POST"])
def record_order():
    data = request.get_json()
    if not data or "order_id" not in data or "user_id" not in data:
        return jsonify({"error": "order_id and user_id required"}), 400

    order_id = data["order_id"]
    user_id = data["user_id"]
    items = data.get("items", [])
    distance = float(data.get("distance", 100))

    if SustainOrder.query.filter_by(order_id=order_id).first():
        return jsonify({"message": "Order already recorded"}), 200

    total_co2 = 0
    total_baseline = 0

    for item in items:
        product = SustainProduct.query.filter_by(product_id=item["product_id"]).first()
        if not product:
            continue

        qty = float(item.get("qty", 1))
        co2 = estimate_emission(
            product.emission_factor, product.weight_kg, qty, distance
        )
        total_co2 += co2

        baseline_factor = (
            10.0 if product.material != "plastic" else product.emission_factor
        )
        total_baseline += estimate_emission(
            baseline_factor, product.weight_kg, qty, distance
        )

    co2_saved = calculate_savings(total_baseline, total_co2)

    new_order = SustainOrder(
        order_id=order_id, user_id=user_id, co2_kg=total_co2, ship_distance_km=distance
    )
    db.session.add(new_order)

    user = SustainUser.query.filter_by(user_id=user_id).first()
    if not user:
        user = SustainUser(
            user_id=user_id,
            co2_total_kg=total_co2,
            co2_saved_kg=co2_saved,
            eco_purchase_count=1,
        )
        db.session.add(user)
    else:
        user.co2_total_kg += total_co2
        user.co2_saved_kg += co2_saved
        user.eco_purchase_count += 1

    db.session.commit()

    return (
        jsonify(
            {
                "order_id": order_id,
                "user_id": user_id,
                "co2_kg": round(total_co2, 3),
                "co2_saved_kg": round(co2_saved, 3),
                "equivalent": f"≈ {int(total_co2*90)} phone charges",
            }
        ),
        201,
    )


@user_bp.route("/user/<user_id>/summary", methods=["GET"])
def user_summary(user_id):
    """Return total CO₂ stats for a given user."""
    user = SustainUser.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    orders = (
        SustainOrder.query.filter_by(user_id=user_id)
        .order_by(SustainOrder.created_at.desc())
        .limit(10)
        .all()
    )

    return jsonify(
        {
            "user_id": user.user_id,
            "co2_total_kg": round(user.co2_total_kg, 3),
            "co2_saved_kg": round(user.co2_saved_kg, 3),
            "eco_purchase_count": user.eco_purchase_count,
            "recent_orders": [
                {
                    "order_id": o.order_id,
                    "co2_kg": round(o.co2_kg, 3),
                    "ship_distance_km": o.ship_distance_km,
                    "created_at": o.created_at,
                }
                for o in orders
            ],
        }
    )

# routes/summary.py
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from sqlalchemy import func, desc, cast, Date
from models import db, SustainOrder, SustainUser, SustainProduct

summary_bp = Blueprint("summary", __name__)


@summary_bp.route("/summary/global", methods=["GET"])
def global_summary():
    """
    Returns platform-wide sustainability metrics:
      - totals: co2_emitted, co2_saved, users, orders
      - timeseries (last N days): emissions_by_day
      - top eco users, top eco products
    Optional query params:
      - days (default 30)
      - top_k (default 5)
    """
    days = int(request.args.get("days", 30))
    top_k = int(request.args.get("top_k", 5))
    since = datetime.utcnow() - timedelta(days=days)

    # totals
    total_emitted = db.session.query(
        func.coalesce(func.sum(SustainOrder.co2_kg), 0.0)
    ).scalar()
    total_saved = db.session.query(
        func.coalesce(func.sum(SustainUser.co2_saved_kg), 0.0)
    ).scalar()
    total_orders = db.session.query(func.count(SustainOrder.order_id)).scalar()
    total_users = db.session.query(func.count(SustainUser.user_id)).scalar()

    emissions_rows = (
        db.session.query(
            cast(SustainOrder.created_at, Date).label("day"),
            func.sum(SustainOrder.co2_kg).label("co2_kg"),
        )
        .filter(SustainOrder.created_at >= since)
        .group_by("day")
        .order_by("day")
        .all()
    )
    emissions_by_day = [
        {"day": d.strftime("%Y-%m-%d"), "co2_kg": float(v)} for d, v in emissions_rows
    ]

    top_users_rows = (
        db.session.query(
            SustainUser.user_id,
            SustainUser.co2_total_kg,
            SustainUser.co2_saved_kg,
            SustainUser.eco_purchase_count,
        )
        .order_by(desc(SustainUser.co2_saved_kg), SustainUser.co2_total_kg)
        .limit(top_k)
        .all()
    )
    top_users = [
        {
            "user_id": uid,
            "co2_total_kg": float(total),
            "co2_saved_kg": float(saved),
            "eco_purchase_count": int(cnt),
        }
        for uid, total, saved, cnt in top_users_rows
    ]

    top_products_rows = (
        db.session.query(
            SustainProduct.product_id,
            SustainProduct.name,
            SustainProduct.eco_score,
            SustainProduct.emission_factor,
        )
        .order_by(desc(SustainProduct.eco_score), SustainProduct.emission_factor)
        .limit(top_k)
        .all()
    )
    top_products = [
        {
            "product_id": pid,
            "name": name,
            "eco_score": int(eco),
            "emission_factor": float(ef),
        }
        for pid, name, eco, ef in top_products_rows
    ]

    return jsonify(
        {
            "totals": {
                "co2_emitted_kg": float(total_emitted),
                "co2_saved_kg": float(total_saved),
                "users": int(total_users),
                "orders": int(total_orders),
            },
            "series": {"emissions_by_day": emissions_by_day},
            "top": {"users": top_users, "products": top_products},
        }
    )

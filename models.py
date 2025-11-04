from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Product(db.Model):
    __tablename__ = "product"
    product_id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(200))
    category = db.Column(db.String(100))
    material = db.Column(db.String(100))
    weight_kg = db.Column(db.Float)
    emission_factor = db.Column(db.Float)
    eco_score = db.Column(db.Float)
    origin_location = db.Column(db.String(100))


class SustainOrder(db.Model):
    __tablename__ = "sustain_orders"
    order_id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50))
    co2_kg = db.Column(db.Float)
    ship_distance_km = db.Column(db.Float)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class SustainUser(db.Model):
    __tablename__ = "sustain_users"
    user_id = db.Column(db.String(50), primary_key=True)
    co2_total_kg = db.Column(db.Float, default=0)
    co2_saved_kg = db.Column(db.Float, default=0)
    eco_purchase_count = db.Column(db.Integer, default=0)
    updated_at = db.Column(
        db.DateTime, server_default=db.func.now(), onupdate=db.func.now()
    )

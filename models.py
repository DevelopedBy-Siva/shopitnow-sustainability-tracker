from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class SustainProduct(db.Model):
    __tablename__ = "products"

    product_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    price = db.Column(db.Float)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    material = db.Column(db.String(100))
    origin_location = db.Column(db.String(100))
    emission_factor = db.Column(db.Float)
    eco_score = db.Column(db.Float)
    weight = db.Column(db.Float)

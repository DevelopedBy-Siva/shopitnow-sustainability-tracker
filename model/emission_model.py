import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib

df = pd.read_csv("./synthetic_data.csv")

df["material"] = df["material"].astype(str)

X = df[["category", "material", "weight", "price"]]
y_eco = df["eco_score"]
y_emission = df["emission_factor"]

categorical_cols = ["category", "material"]
numeric_cols = ["weight", "price"]

preprocessor = ColumnTransformer(
    [
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
    ],
    remainder="passthrough",
)

eco_model = Pipeline(
    [
        ("preprocessor", preprocessor),
        ("model", RandomForestRegressor(n_estimators=200, random_state=42)),
    ]
)

emission_model = Pipeline(
    [
        ("preprocessor", preprocessor),
        ("model", RandomForestRegressor(n_estimators=200, random_state=42)),
    ]
)

X_train, X_test, y_eco_train, y_eco_test = train_test_split(
    X, y_eco, test_size=0.2, random_state=42
)
_, _, y_emission_train, y_emission_test = train_test_split(
    X, y_emission, test_size=0.2, random_state=42
)

eco_model.fit(X_train, y_eco_train)
emission_model.fit(X_train, y_emission_train)

print("Eco Score test R²:", eco_model.score(X_test, y_eco_test))
print("Emission Factor test R²:", emission_model.score(X_test, y_emission_test))

joblib.dump(eco_model, "./eco_score_model.pkl")
joblib.dump(emission_model, "./emission_model.pkl")

print("Models saved...")

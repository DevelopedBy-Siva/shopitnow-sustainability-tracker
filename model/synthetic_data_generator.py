import pandas as pd
import numpy as np
import random

df = pd.read_csv("./data.csv")

synthetic_rows = []
for _ in range(200):
    base = df.sample(1).iloc[0]
    weight = round(base.weight * random.uniform(0.8, 1.2), 2)
    price = round(base.price * random.uniform(0.7, 1.3), 2)
    eco = round(base.eco_score + np.random.uniform(-0.5, 0.5), 2)
    emission = round(base.emission_factor + np.random.uniform(-0.5, 0.5), 2)
    synthetic_rows.append(
        {
            "title": f"{base.title} variant {_}",
            "category": base.category,
            "material": base.material,
            "weight": weight,
            "price": price,
            "origin_location": base.origin_location,
            "eco_score": eco,
            "emission_factor": emission,
        }
    )

synth_df = pd.concat([df, pd.DataFrame(synthetic_rows)], ignore_index=True)
synth_df.to_csv("./synthetic_data.csv", index=False)
print("Data generated.")

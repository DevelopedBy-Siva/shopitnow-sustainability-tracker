import math
import torch

MATERIALS = [
    "bamboo",
    "stainless_steel",
    "plastic",
    "cotton",
    "polyester",
    "leather",
    "recycled_paper",
]
MAT_INDEX = {m: i for i, m in enumerate(MATERIALS)}


def product_to_vector(
    material: str, weight_kg: float, emission_factor: float, eco_score: int
) -> torch.Tensor:

    one_hot = torch.zeros(len(MATERIALS))
    if material in MAT_INDEX:
        one_hot[MAT_INDEX[material]] = 1.0

    w = torch.tensor([math.log1p(max(0.0, weight_kg))], dtype=torch.float32)
    ef = torch.tensor([min(max(emission_factor / 12.0, 0.0), 1.0)], dtype=torch.float32)
    es = torch.tensor([min(max(eco_score / 10.0, 0.0), 1.0)], dtype=torch.float32)

    return torch.cat([one_hot, w, ef, es], dim=0)


def cosine_sim(a: torch.Tensor, b: torch.Tensor) -> float:
    a = a.unsqueeze(0) if a.dim() == 1 else a
    b = b.unsqueeze(0) if b.dim() == 1 else b
    a = torch.nn.functional.normalize(a, dim=1)
    b = torch.nn.functional.normalize(b, dim=1)
    return float((a @ b.T).item())

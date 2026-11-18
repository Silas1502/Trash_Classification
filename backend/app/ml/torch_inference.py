from time import perf_counter

import numpy as np
import torch

from app.core.safety_gate import SafetyFilter

from .inference import InferenceResult
from .model_loader import ModelBundle
from .xai_engine import render_explanations


def classify_with_torch(
    model: ModelBundle, rgb: np.ndarray, zoom: np.ndarray, safety: SafetyFilter, adaptive_enabled: bool,
) -> list[InferenceResult]:
    started = perf_counter()
    device = next(model.sub_logits_model.parameters()).device
    inputs = torch.as_tensor(rgb, dtype=torch.float32, device=device)
    with torch.no_grad():
        views = [inputs]
        if zoom.size:
            views.extend((
                inputs.flip(2), inputs.rot90(1, (1, 2)), inputs.rot90(3, (1, 2)),
                torch.as_tensor(zoom, dtype=torch.float32, device=device),
            ))
        probabilities = torch.stack([
            model.sub_logits_model(view, training=False).float().softmax(dim=-1) for view in views
        ])
        mean = probabilities.mean(dim=0)
        stability = [None] * len(rgb)
        if len(views) > 1:
            stability = (probabilities.argmax(dim=-1) == mean.argmax(dim=-1)).float().mean(dim=0).tolist()
        decisions = [
            safety.evaluate(values, vote, adaptive_enabled=adaptive_enabled)
            for values, vote in zip(mean.cpu().numpy(), stability, strict=True)
        ]
    after_inference = perf_counter()
    with torch.no_grad():
        features, skip = model.spatial(inputs, training=False)
    with torch.enable_grad():
        features.requires_grad_(True)
        logits = model.head([features, skip], training=False)
        targets = torch.tensor([decision.top_index for decision in decisions], device=device)
        scores = logits.gather(1, targets[:, None]).sum()
        gradients, = torch.autograd.grad(scores, features)

    explanations = render_explanations(
        list(rgb), features.detach().float().cpu().numpy(), gradients.float().cpu().numpy(),
    )
    ended = perf_counter()
    return [
        InferenceResult(decision, explanation,
                        (after_inference - started) * 1000 / len(rgb), (ended - after_inference) * 1000 / len(rgb))
        for decision, explanation in zip(decisions, explanations, strict=True)
    ]

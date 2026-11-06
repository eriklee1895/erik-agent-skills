"""Example project recipe: contact noise plus damped wooden resonances, 48 kHz."""

import numpy as np
from earshot.forge import dsp

DEFAULTS = {"duration": 0.24, "body_hz": 170.0, "decay": 0.038, "texture": 0.12}


def render(params, rng):
    duration = float(params["duration"])
    frequency = float(params["body_hz"])
    decay = float(params["decay"])
    texture = float(params["texture"])
    if not 0.03 <= duration <= 2 or not 60 <= frequency <= 1200:
        raise ValueError("duration must be 0.03–2 s and body_hz 60–1200 Hz")
    if not 0.005 <= decay <= 0.4 or not 0 <= texture <= 0.6:
        raise ValueError("decay must be 0.005–0.4 s and texture 0–0.6")
    body = dsp.modal(
        [frequency, frequency * 1.63, frequency * 2.71],
        [decay, decay * 0.6, decay * 0.3],
        [1, 0.32, 0.1],
        duration,
        rng,
    )
    contact = dsp.butter(dsp.noise(duration, rng), "band", (650, 4300))
    contact *= dsp.env_exp(duration, 0.007, attack=0.0005)
    return np.asarray(body + texture * contact, dtype=np.float64)

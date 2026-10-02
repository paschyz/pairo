#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "scipy", "pillow"]
# ///
"""Cut the Pairo mascot out of its cream tile so it can sit on the film's dark background.

    uv run score/mascot.py   -> public/mascot.png (transparent), score/qa/mascot-on-dark.png

The logo is flat art on a flat background, so the matte is exact: an edge pixel is a mix of
the background and the nearest solid colour, and alpha is how far along that line it sits.
"""

from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT.parent / "dashboard" / "src" / "assets" / "pairo.png"

rgb = np.asarray(Image.open(SOURCE).convert("RGB")).astype(float)
bg = np.median(np.vstack([rgb[:8].reshape(-1, 3), rgb[-8:].reshape(-1, 3)]), axis=0)
dist = np.linalg.norm(rgb - bg, axis=2)

labels, _ = ndi.label(dist < 150)  # background plus the soft edge that touches it
outside = np.isin(labels, np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])))
solid = ~ndi.binary_dilation(outside, iterations=2)  # safely inside the artwork
nearest = ndi.distance_transform_edt(~solid, return_distances=False, return_indices=True)
colour = rgb[nearest[0], nearest[1]]  # what each edge pixel would be without the background

span = colour - bg
alpha = np.clip(((rgb - bg) * span).sum(axis=2) / ((span**2).sum(axis=2) + 1e-9), 0, 1)
alpha[solid] = 1
alpha[outside & (dist < 6)] = 0

out = np.dstack([np.where(solid[..., None], rgb, colour), alpha * 255]).round().astype(np.uint8)
(ROOT / "public").mkdir(exist_ok=True)
Image.fromarray(out, "RGBA").save(ROOT / "public" / "mascot.png", optimize=True)

dark = Image.new("RGBA", out.shape[1::-1], "#08090d")
dark.alpha_composite(Image.fromarray(out, "RGBA"))
(ROOT / "score" / "qa").mkdir(exist_ok=True)
dark.convert("RGB").resize((627, 627), Image.LANCZOS).save(ROOT / "score" / "qa" / "mascot-on-dark.png")
print("background", bg, "| opaque", int((alpha == 1).sum()), "| edge", int(((alpha > 0) & (alpha < 1)).sum()))

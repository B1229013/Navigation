"""GroundingDINO + SAM perception. Loaded once at server startup."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

import torch
from PIL import Image

from server.config import (
    GROUNDINGDINO_CONFIG, GROUNDINGDINO_WEIGHTS, SAM_WEIGHTS,
    GROUNDINGDINO_BOX_THRESHOLD, GROUNDINGDINO_TEXT_THRESHOLD, SAM_TOP_K_BOXES,
)

log = logging.getLogger(__name__)


@dataclass
class Detection:
    label: str
    box: List[float]  # [x1,y1,x2,y2] absolute pixels
    score: float


class Perception:
    def __init__(self) -> None:
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._gd_model = None
        self._sam_predictor = None

    def load(self) -> None:
        from groundingdino.util.inference import load_model
        from segment_anything import sam_model_registry, SamPredictor

        log.info("loading GroundingDINO from %s", GROUNDINGDINO_WEIGHTS)
        self._gd_model = load_model(str(GROUNDINGDINO_CONFIG), str(GROUNDINGDINO_WEIGHTS))
        log.info("loading SAM from %s", SAM_WEIGHTS)
        sam = sam_model_registry["vit_h"](checkpoint=str(SAM_WEIGHTS))
        sam.to(self.device)
        self._sam_predictor = SamPredictor(sam)
        log.info("perception loaded on %s", self.device)

    def detect(self, image_path: str, prompt_classes: List[str]) -> List[Detection]:
        if not prompt_classes:
            return []
        from groundingdino.util.inference import predict, load_image
        text_prompt = " . ".join(prompt_classes) + " ."
        image_source, image = load_image(image_path)
        boxes, logits, phrases = predict(
            model=self._gd_model,
            image=image,
            caption=text_prompt,
            box_threshold=GROUNDINGDINO_BOX_THRESHOLD,
            text_threshold=GROUNDINGDINO_TEXT_THRESHOLD,
            device=self.device,
        )

        h, w = image_source.shape[:2]
        results: List[Detection] = []
        for box_cxcywh, score, phrase in zip(boxes, logits, phrases):
            cx, cy, bw, bh = box_cxcywh.tolist()
            x1 = (cx - bw / 2) * w
            y1 = (cy - bh / 2) * h
            x2 = (cx + bw / 2) * w
            y2 = (cy + bh / 2) * h
            results.append(Detection(label=phrase, box=[x1, y1, x2, y2], score=float(score)))

        results.sort(key=lambda d: -d.score)
        return results[:SAM_TOP_K_BOXES]

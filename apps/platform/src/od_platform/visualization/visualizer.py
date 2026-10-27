"""美化绘制模块（简化版兜底实现）。
提供与 D8 讲义兼容的 DrawStyle 和 BeautifyVisualizer 接口。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np


@dataclass
class DrawStyle:
    """绘制样式配置（根据图像尺寸自适应）。"""
    box_thickness: int = 2
    text_scale: float = 0.5
    text_thickness: int = 1
    text_color: tuple[int, int, int] = (255, 255, 255)
    text_bg_alpha: float = 0.6

    @classmethod
    def from_image_size(cls, h: int, w: int, **kwargs: Any) -> DrawStyle:
        """根据图片尺寸生成默认样式（尺寸越大线越粗）。"""
        # 简单自适应逻辑
        base = min(h, w)
        thickness = max(1, int(base / 300))
        scale = max(0.4, float(base / 1000))

        style = cls(
            box_thickness=kwargs.get("box_thickness", thickness),
            text_scale=kwargs.get("text_scale", scale),
            text_thickness=kwargs.get("text_thickness", max(1, thickness - 1)),
            text_color=tuple(kwargs.get("text_color", [255, 255, 255])),
            text_bg_alpha=kwargs.get("text_bg_alpha", 0.6)
        )
        return style


@dataclass
class Detection:
    """单个检测框的数据结构。"""
    box: tuple[float, float, float, float]  # x1, y1, x2, y2
    confidence: float
    label: str


class BeautifyVisualizer:
    """画框与文字的美化渲染器（简化版）。"""

    def __init__(
        self,
        labels: list[str],
        label_mapping: dict[str, str] | None = None,
        color_mapping: dict[str, tuple[int, int, int]] | None = None,
        default_color: tuple[int, int, int] = (0, 255, 0),
        font_path: str | None = None,
    ):
        self.labels = labels
        self.label_mapping = label_mapping or {}
        self.color_mapping = color_mapping or {}
        self.default_color = default_color
        self.font_path = font_path

        # 为没有指定颜色的类别分配随机但固定的颜色
        self._fallback_colors: dict[str, tuple[int, int, int]] = {}

    @classmethod
    def from_yolo_results(
        cls, boxes: np.ndarray, confidences: np.ndarray, labels: list[str]
    ) -> list[Detection]:
        """从 YOLO 推理结果提取检测数据。"""
        dets = []
        for box, conf, label in zip(boxes, confidences, labels, strict=False):
            dets.append(Detection(box=tuple(box), confidence=float(conf), label=label))
        return dets

    def _get_color(self, label: str) -> tuple[int, int, int]:
        if label in self.color_mapping:
            return self.color_mapping[label]
        if label not in self._fallback_colors:
            # 随机生成一个鲜艳的 BGR 颜色
            rng = np.random.default_rng(hash(label) % (2**32))
            self._fallback_colors[label] = tuple(int(c) for c in rng.integers(50, 255, 3))
        return self._fallback_colors[label]

    def _draw_text_bg(
        self, img: np.ndarray, text: str, x: int, y: int,
        font_scale: float, thickness: int, alpha: float
    ) -> None:
        """画半透明的文字背景框。"""
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        overlay = img.copy()
        cv2.rectangle(overlay, (x, y - th - 4), (x + tw + 4, y), (0, 0, 0), -1)
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

    def draw(
        self,
        image: np.ndarray,
        detections: list[Detection],
        style: DrawStyle,
        use_label_mapping: bool = True,
    ) -> np.ndarray:
        """在图像上绘制检测框和标签。"""
        # 必须 copy 一份，不能改变原图（原图可能还要给别的模块用）
        canvas = image.copy()

        for det in detections:
            x1, y1, x2, y2 = map(int, det.box)
            color = self._get_color(det.label)

            # 1. 画框
            cv2.rectangle(canvas, (x1, y1), (x2, y2), color, style.box_thickness)

            # 2. 准备文字
            display_label = det.label
            if use_label_mapping and det.label in self.label_mapping:
                display_label = self.label_mapping[det.label]

            text = f"{display_label} {det.confidence:.2f}"

            # 3. 画文字背景（半透明）
            text_y = max(y1 - 5, 15)
            self._draw_text_bg(
                canvas, text, x1, text_y,
                style.text_scale, style.text_thickness, style.text_bg_alpha
            )

            # 4. 画文字
            cv2.putText(
                canvas, text, (x1 + 2, text_y - 2),
                cv2.FONT_HERSHEY_SIMPLEX, style.text_scale,
                style.text_color, style.text_thickness, cv2.LINE_AA
            )

        return canvas

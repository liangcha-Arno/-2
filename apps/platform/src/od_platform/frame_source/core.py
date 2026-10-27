# apps/platform/src/od_platform/frame_source/core.py
from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")

class SourceType:
    IMAGE = "image"
    VIDEO = "video"
    CAMERA = "camera"
    RTSP = "rtsp"

@dataclass
class FrameInfo:
    frame_index: int = 0
    filename: str | None = None
    fps: float | None = None

@dataclass
class Frame:
    image: np.ndarray
    info: FrameInfo

class BaseFrameSource:
    def __init__(self, source: Any):
        self.source = source

    def get_source_type(self) -> str:
        return SourceType.IMAGE

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __iter__(self) -> Iterator[Frame]:
        raise NotImplementedError

class ImageFolderSource(BaseFrameSource):
    def get_source_type(self) -> str:
        return SourceType.IMAGE

    def __iter__(self):
        p = Path(self.source)
        if p.is_file():
            files = [p]
        else:
            files = [f for f in p.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS]
            files.sort()

        for idx, f in enumerate(files):
            img = cv2.imread(str(f))
            if img is not None:
                yield Frame(image=img, info=FrameInfo(frame_index=idx, filename=f.name))

class VideoSource(BaseFrameSource):
    def get_source_type(self) -> str:
        return SourceType.VIDEO

    def __iter__(self):
        cap = cv2.VideoCapture(str(self.source))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        idx = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret: break  # noqa: E701
                yield Frame(image=frame, info=FrameInfo(frame_index=idx, fps=fps))
                idx += 1
        finally:
            cap.release()

class CameraSource(BaseFrameSource):
    def get_source_type(self) -> str:
        return SourceType.CAMERA

    def __init__(self, source: int, camera_config: Any = None):
        super().__init__(source)
        self.camera_config = camera_config

    def __iter__(self):
        # 简单处理:直接开默认摄像头
        cap = cv2.VideoCapture(self.source)
        idx = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret: break  # noqa: E701
                yield Frame(image=frame, info=FrameInfo(frame_index=idx, fps=30.0))
                idx += 1
        finally:
            cap.release()

def create_frame_source(source: Any, **kwargs) -> BaseFrameSource:
    """工厂函数:根据传入的 source 类型返回对应的 FrameSource。"""
    if isinstance(source, int) or (isinstance(source, str) and source.isdigit()):
        return CameraSource(int(source), kwargs.get("camera_config"))

    s = str(source).lower()
    if s.startswith(("rtsp://", "rtmp://", "http://")):
        return VideoSource(source)

    p = Path(source)
    if p.is_dir() or (p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS):
        return ImageFolderSource(source)

    return VideoSource(source)

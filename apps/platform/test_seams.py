# /tmp/test_seams.py
"""验证 3 个接缝模块的关键合约."""
import logging

logging.basicConfig(level=logging.INFO)

import threading  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

# ============================================================
# 1. CancelToken: 基础 + 跨线程
# ============================================================
from od_platform.inference import CancelToken

t = CancelToken()
assert not t.is_cancelled()
t.cancel()
assert t.is_cancelled()
t.cancel(); t.cancel()       # 幂等, 不炸  # noqa: E702
print("✅ CancelToken 基础 + 幂等")

# 跨线程: 一个线程 cancel, 另一个立即看到
t2 = CancelToken()
seen = threading.Event()
def watcher():
    for _ in range(100):
        if t2.is_cancelled():
            seen.set(); return  # noqa: E702
        time.sleep(0.005)
threading.Thread(target=watcher).start()
time.sleep(0.05); t2.cancel()  # noqa: E702
assert seen.wait(0.5)
print("✅ CancelToken 跨线程可见")

# ============================================================
# 2. InferHooks: 默认空 + 业务回调被调 + ★ 业务异常被吞
# ============================================================
from od_platform.inference import FrameEvent, InferHooks, ProgressEvent  # type: ignore # noqa: E402

h = InferHooks()
assert h.on_frame is None and h.progress_interval_frames == 30
fe = FrameEvent(0, np.zeros((1,1,3),dtype=np.uint8),
                np.zeros((1,1,3),dtype=np.uint8), 0)
pe = ProgressEvent(10, 100, 1.0, 30.0, 60.0, 5)
# 空 hooks: 全 short-circuit
h.fire_frame(fe); h.fire_progress(pe); h.fire_complete("R"); h.fire_error(RuntimeError())  # noqa: E702
print("✅ InferHooks 空回调 short-circuit")

# 业务回调被调
calls = []
h2 = InferHooks(
    on_frame=lambda e: calls.append(("frame", e.frame_idx)),
    on_complete=lambda r: calls.append(("done", r)),
)
h2.fire_frame(fe); h2.fire_complete("OK")  # noqa: E702
assert calls == [("frame", 0), ("done", "OK")]
print("✅ InferHooks 业务回调被调")

# ★ 业务 hook 抛异常被吞 (核心纪律)
def bad(*a, **kw): raise RuntimeError("user code bug")
h3 = InferHooks(on_frame=bad, on_progress=bad, on_complete=bad, on_error=bad)
try:
    h3.fire_frame(fe); h3.fire_progress(pe); h3.fire_complete("x"); h3.fire_error(Exception())  # noqa: E702
    print("✅ InferHooks ★ 业务 hook 异常被吞 (核心纪律)")
except Exception as e:
    print(f"❌ FAIL: 业务 hook 异常应被吞但泄露了: {e}")

# ============================================================
# 3. OutputSink: ABC + LocalFileSink + NullSink
# ============================================================
from unittest.mock import MagicMock  # noqa: E402

from od_platform.frame_source import SourceType  # type: ignore # noqa: E402
from od_platform.inference import LocalFileSink, NullSink, OutputSink  # type: ignore # noqa: E402

# ABC 不能直接实例化
try:
    OutputSink()
    print("❌ FAIL: OutputSink ABC 居然能直接实例化")
except TypeError:
    print("✅ OutputSink ABC 拒绝直接实例化")

# NullSink: open/write/close 都不出错, 不写文件
import tempfile  # noqa: E402

with tempfile.TemporaryDirectory() as tmp:
    sink = NullSink()
    sink.open(Path(tmp), SourceType.VIDEO)
    for _ in range(5):
        sink.write(MagicMock(), np.zeros((10,10,3),dtype=np.uint8))
    sink.close(); sink.close()    # 幂等  # noqa: E702
    assert list(Path(tmp).iterdir()) == []
    print("✅ NullSink no-op + 幂等")

# LocalFileSink: 图片源写 jpg
with tempfile.TemporaryDirectory() as tmp:
    sink = LocalFileSink()
    sink.open(Path(tmp), SourceType.IMAGE)
    for i in range(3):
        frame = MagicMock(); frame.info.filename = f"test_{i}.png"  # noqa: E702
        sink.write(frame, np.full((50,50,3), 128, dtype=np.uint8))
    sink.close()
    jpgs = sorted(Path(tmp).glob("*.jpg"))
    assert len(jpgs) == 3 and jpgs[0].name == "test_0.jpg"
    print("✅ LocalFileSink 图片源 → 3 张 jpg")

# LocalFileSink: 视频源写 mp4
with tempfile.TemporaryDirectory() as tmp:
    sink = LocalFileSink()
    sink.open(Path(tmp), SourceType.VIDEO)
    for i in range(8):
        frame = MagicMock(); frame.info.fps = 30.0; frame.info.frame_index = i  # noqa: E702
        sink.write(frame, np.full((100,200,3), i*30, dtype=np.uint8))
    sink.close()
    assert (Path(tmp) / "output.mp4").exists()
    print("✅ LocalFileSink 视频源 → output.mp4")

print("\n========== 接缝模块全部通过 ==========")

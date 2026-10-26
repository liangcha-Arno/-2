import sys
from pathlib import Path

# 强行把当前目录下的 src 文件夹加入环境变量
src_dir = Path(__file__).resolve().parent / "src"
if src_dir.exists():
    sys.path.insert(0, str(src_dir))

# /tmp/test_overlay.py
from od_platform.inference.overlay import FPSCounter, Metrics  # type: ignore  # noqa: E402

# --- FPSCounter ---
fps = FPSCounter(window_size=5)
for ms in [10, 12, 11, 9, 10]:
    fps.update(ms)
assert abs(fps.fps - 95.2) < 1.0, f"{fps.fps}"   # 1000/10.4 ≈ 96
assert abs(fps.inst - 100.0) < 1.0                 # 最近一个是 10ms → 100 FPS
print(f"✅ FPSCounter: fps={fps.fps:.1f}, inst={fps.inst:.1f}")

# --- Metrics ---
m = Metrics()
m.capture.update(33.3)        # 30 FPS
m.add_speed({"preprocess": 1.5, "inference": 8.0, "postprocess": 2.0})
m.add_speed({"preprocess": 1.6, "inference": 8.5, "postprocess": 2.1})
m.render.update(28.0)
m.loop.update(50.0)           # 20 FPS

snap = m.snapshot()
print(f"✅ Metrics snapshot: {snap}")
assert snap["capture_fps"] > 25
assert snap["infer_fps"] > 100      # 1000/8.25 ≈ 121
assert snap["loop_fps"] > 15
print(f"✅ speed_avg: {m.speed_avg_ms()}")

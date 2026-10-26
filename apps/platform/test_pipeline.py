import os
import sys
from pathlib import Path

# 暴力且有效：把 src 目录强行写入环境变量和 sys.path
current_dir = Path(__file__).resolve().parent
src_dir = str(current_dir / "src")
os.environ["PYTHONPATH"] = src_dir + os.pathsep + os.environ.get("PYTHONPATH", "")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# 导入模块
from od_platform.inference.pipeline_config import load_pipeline_config  # noqa: E402

print("--- 1. 测试正常加载 ---")
pc = load_pipeline_config("/tmp/d8v_verify/infer_pipeline.yaml")
print("viz_enabled:", pc.viz_enabled, "| label_mapping:", len(pc.label_mapping), "| color_mapping:", pc.color_mapping)
print("camera_raw:", pc.camera_raw)

print("\n--- 2. 测试构建 CameraConfig ---")
cam = pc.build_camera_config()
if cam is not None:
    print("CameraConfig:", cam.camera_id, cam.width, cam.height, cam.fps, cam.backend)
else:
    print("CameraConfig: None (因为读取的是默认空配置)")

print("\n--- 3. 测试 to_audit ---")
print("to_audit:", pc.to_audit())

print("\n--- 4. 测试缺失文件兜底 ---")
pc2 = load_pipeline_config("/tmp/d8v_verify/nonexist.yaml")
print("缺失文件兜底:", pc2.viz_enabled, pc2.camera_raw)

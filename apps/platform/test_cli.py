from od_platform.inference import infer_yolo

# 真正跑一次
result = infer_yolo(
    cli_args={
        "source": "data/raw/demo/images/c_000.jpg",  # 比如 data/raw/demo/images/c_000.jpg
        "model": "yolo11n.pt",           # 真模型，它会去下载
        "show": False,
        "save": True
    }
)

if result.success:
    print(f"✅ 真实推理成功！图片保存在: {result.output_dir}")
else:
    print(f"❌ 失败: {result.error}")

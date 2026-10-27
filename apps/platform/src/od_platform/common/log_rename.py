# apps/platform/src/od_platform/common/log_rename.py
import logging
from pathlib import Path


def rename_log_to_save_dir(output_dir: Path, model_stem: str) -> None:
    """把当前进程的日志文件重命名，追加 output_dir 的名字。"""
    logger = logging.getLogger()

    # 遍历所有的 handler，找到 FileHandler
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            old_path = Path(handler.baseFilename)
            if not old_path.exists():
                continue
            # 构造新文件名: 原文件名 + _ + 输出目录名 + 模型名.log
            # 比如: infer_20231024.log -> infer_20231024_predict8_yolo11n.log
            dir_name = output_dir.name
            new_name = f"{old_path.stem}_{dir_name}_{model_stem}{old_path.suffix}"
            new_path = old_path.parent / new_name

            try:
                # 1. 关闭当前 handler 的文件句柄
                handler.close()
                # 2. 重命名文件
                old_path.rename(new_path)
                # 3. 重新打开新文件，并重新绑定到 handler
                handler.baseFilename = str(new_path.absolute())
                handler.stream = handler._open()

                logger.info(f"日志已重命名对齐输出目录: {new_path.name}")
            except Exception as e:
                logger.warning(f"重命名日志失败: {e}")

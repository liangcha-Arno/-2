# apps/platform/src/od_platform/data_validation/checks/visual_diagnosis.py
import csv

from tqdm import tqdm

from od_platform.common import paths
from od_platform.data_validation.labels import parse_label_line
from od_platform.data_validation.registry import CheckContext, CheckResult, CheckSeverity, check

_NAME = "visual_diagnosis"

@check(_NAME)
def generate_error_statistics(ctx: CheckContext) -> CheckResult:
    """纯文本解析：统计所有越界/极小框的错误，并输出 CSV 报告。"""
    snap = ctx.snapshot
    if snap.data_root is None:
        return CheckResult(_NAME, CheckSeverity.PASS, "未找到数据根目录，跳过", {})

    csv_path = paths.VALIDATION_RUNS_DIR / "error_statistics.csv"
    error_records = []  # 用于写入 CSV 的统计

    # 遍历所有 split 和标签文件 (不读图，速度极快)
    for split in snap.splits:
        for lbl in tqdm(snap.label_files_per_split.get(split, ()), desc=f"统计 {split} 异常"):
            # 读取标签文本
            for line_no, line in enumerate(lbl.read_text(encoding="utf-8").splitlines(), 1):
                line = line.strip()
                if not line: continue  # noqa: E701
                box, kind = parse_label_line(line, snap.task_type)

                if box:
                    cid, coords = box
                    err_types = []

                    if len(coords) == 4: # detect 的 cx, cy, w, h (归一化)
                        cx, cy, w, h = coords
                        if cx - w/2 < 0 or cx + w/2 > 1 or cy - h/2 < 0 or cy + h/2 > 1:
                            err_types.append("坐标越界")
                        if w < 0.01 or h < 0.01:
                            err_types.append("极小框")
                    else: # segment 的多边形坐标
                        xs = coords[0::2]
                        ys = coords[1::2]
                        if min(xs) < 0 or max(xs) > 1 or min(ys) < 0 or max(ys) > 1:
                            err_types.append("坐标越界")

                    if err_types:
                        err_str = "|".join(err_types)
                        error_records.append({
                            "split": split,
                            "label_file": lbl.name,
                            "line_no": line_no,
                            "class_id": cid,
                            "error_type": err_str,
                            "raw_line": line
                        })

    # 写入 CSV 统计文件
    if error_records:
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["split", "label_file", "line_no", "class_id", "error_type", "raw_line"])
            writer.writeheader()
            writer.writerows(error_records)

        msg = f"共发现 {len(error_records)} 处标签异常，已生成统计报告"
        return CheckResult(_NAME, CheckSeverity.WARNING, msg, {"csv_path": str(csv_path)})

    return CheckResult(_NAME, CheckSeverity.PASS, "未发现需统计的异常标签", {})

from od_platform.data_validation.labels import parse_label_line
from od_platform.data_validation.registry import CheckContext, CheckResult, CheckSeverity, check

_NAME = "bbox_normalized"

@check(_NAME)
def validate_bbox_normalized(ctx: CheckContext) -> CheckResult:
    snap = ctx.snapshot
    nc = snap.nc
    if nc is None:
        return CheckResult(_NAME, CheckSeverity.PASS, "nc 不可用，跳过")

    bad_lines = []
    for split in snap.splits:
        for lbl in snap.label_files_per_split.get(split, ()):
            for line_no, line in enumerate(lbl.read_text(encoding="utf-8").splitlines(), 1):
                line = line.strip()
                if not line: continue  # noqa: E701
                box, kind = parse_label_line(line, snap.task_type)
                if box:
                    cls_id, coords = box
                    if not (0 <= cls_id < nc):
                        bad_lines.append(f"{lbl.name}:{line_no} class_id={cls_id} 越界")
                    if any(c < 0 or c > 1 for c in coords):
                        bad_lines.append(f"{lbl.name}:{line_no} 坐标未归一化或越界")

    if bad_lines:
        return CheckResult(_NAME, CheckSeverity.ERROR, f"{len(bad_lines)} 处标签越界/非法", {"bad_lines": bad_lines[:10]})
    return CheckResult(_NAME, CheckSeverity.PASS, "所有标签类别与归一化坐标均合法")

import json
import sys
from pathlib import Path
from typing import Any


def load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def compare_reports(report_path_old: Path, report_path_new: Path) -> int:
    old = load_report(report_path_old)
    new = load_report(report_path_new)

    print("=== 质检报告对比 ===")
    old_checks = {r['name']: r['severity'] for r in old.get('results', [])}
    new_checks = {r['name']: r['severity'] for r in new.get('results', [])}

    fixed, introduced = [], []
    order = {"PASS": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}

    for name, old_sev in old_checks.items():
        new_sev = new_checks.get(name)
        if new_sev is None: continue  # noqa: E701
        if order.get(new_sev, 0) < order.get(old_sev, 0):
            fixed.append(f"{name}: {old_sev} -> {new_sev}")
        elif order.get(new_sev, 0) > order.get(old_sev, 0):
            introduced.append(f"{name}: {old_sev} -> {new_sev}")

    print("✅ 已修复/改善的项:")
    for f in (fixed or ["(无)"]): print(f"  - {f}")  # noqa: E701
    print("\n❌ 新引入的问题:")
    for i in (introduced or ["(无)"]): print(f"  - {i}")  # noqa: E701
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python compare_reports.py <旧report.json> <新report.json>")
        sys.exit(1)
    compare_reports(Path(sys.argv[1]), Path(sys.argv[2]))

from pathlib import Path

from od_platform.data_validation.identity import reconcile_data_identity

# 注意！这里指定的是 configs 下的 yaml 文件，而不是 data/raw 文件夹！
yaml_file_path = Path("configs/datasets/demo.yaml")

print("--- 测试默认门禁 ---")
ident = reconcile_data_identity(yaml_file_path, require_validated=True)
print('ok =', ident.ok, '| reason =', ident.reason[:50])

print("\n--- 测试放宽模式 ---")
ident2 = reconcile_data_identity(yaml_file_path, require_validated=False)
print('ok =', ident2.ok, '| reconciled =', ident2.reconciled, '| validated_pass =', ident2.validated_pass)

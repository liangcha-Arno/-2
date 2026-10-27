# apps/platform/src/od_platform/common/config_log.py
import logging
from typing import Any


def log_effective_config(config: Any, merger: Any, logger: logging.Logger = None) -> None:
    """打印当前生效的配置参数及来源。"""
    log = logger or logging.getLogger(__name__)
    log.info("=" * 60)
    log.info("生效配置参数 (Effective Config)".center(60))
    log.info("=" * 60)

    # 遍历配置对象的所有字段
    for field_name in type(config).model_fields:
        value = getattr(config, field_name)
        # 尝试从 merger 获取该字段的来源
        source = "DEFAULT"
        if merger and hasattr(merger, "get_metadata"):
            meta = merger.get_metadata(field_name)
            if meta:
                source = getattr(meta, "source_label", str(meta.source))

        log.info(f"{field_name:<20}: {value}  (来源: {source})")

def log_override_chains(config: Any, merger: Any, logger: logging.Logger = None) -> None:
    """打印被覆盖的参数及其溯源链。"""
    log = logger or logging.getLogger(__name__)

    if not merger or not hasattr(merger, "_overridden_keys"):
        return

    overridden_keys = list(set(merger._overridden_keys))
    if not overridden_keys:
        return

    log.info("-" * 60)
    log.info("配置覆盖溯源 (Override Chains)".center(60))
    log.info("-" * 60)

    for key in sorted(overridden_keys):
        meta = merger.get_metadata(key)
        if meta and hasattr(meta, "chain_str"):
            log.info(f"{key:<20}: {meta.chain_str()}")

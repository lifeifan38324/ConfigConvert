import logging
from collections import Counter

import yaml

# Clash 内建策略，允许被策略组直接引用（与 builder 保持独立定义，避免守门逻辑被同一处 bug 污染）
BUILTIN_POLICIES = {"DIRECT", "REJECT", "REJECT-DROP", "PASS", "COMPATIBLE", "GLOBAL"}


class ConfigValidationError(Exception):
    """产出未通过发布前校验。调用方应中止发布，保留 Gist 上一版内容。"""


def validate_before_publish(final: dict, stats: dict, min_nodes: int, min_success_ratio: float) -> None:
    """
    发布前的守门校验。任一条不满足即抛异常，阻止覆盖 Gist。

    :param final: (dict) 组装完成的最终配置字典
    :param stats: (dict) 构建统计，形如 {"total": 订阅总数, "success": 取到节点的订阅数}
    :param min_nodes: (int) 节点数下限
    :param min_success_ratio: (float) 订阅成功率下限，0~1
    :return: None，校验不通过时抛 ConfigValidationError
    """
    proxies = final.get("proxies") or []
    groups = final.get("proxy-groups") or []
    rules = final.get("rules") or []
    total = stats.get("total", 0)
    success = stats.get("success", 0)

    errors = []

    if total == 0:
        errors.append("SUBSCRIBE_LIST 为空，无任何订阅可拉取")
    elif success / total < min_success_ratio:
        errors.append(f"订阅成功率 {success}/{total} 低于阈值 {min_success_ratio:.0%}")

    if not proxies:
        errors.append("节点列表为空（所有订阅均未取到有效 proxies）")
    elif len(proxies) < min_nodes:
        errors.append(f"节点数 {len(proxies)} 低于下限 {min_nodes}")

    if not groups:
        errors.append("proxy-groups 为空（检查 CONFIG_URL 及 custom_proxy_group 段）")
    if not rules:
        errors.append("rules 为空（检查 CONFIG_URL 及 ruleset 段）")

    node_names = [p.get("name") for p in proxies if isinstance(p, dict) and p.get("name")]

    # 重名节点会让 Clash 拒绝加载整份配置
    duplicates = [name for name, count in Counter(node_names).items() if count > 1]
    if duplicates:
        errors.append(f"存在 {len(duplicates)} 个重名节点：{duplicates[:3]}")

    # 策略组引用必须可达（节点、其它策略组、内建策略），自引用同样非法
    group_names = {g.get("name") for g in groups if isinstance(g, dict)}
    valid_targets = group_names | BUILTIN_POLICIES | set(node_names)
    dangling = []
    for group in groups:
        group_name = group.get("name")
        for member in group.get("proxies") or []:
            if member == group_name or member not in valid_targets:
                dangling.append(f"{group_name} -> {member}")
    if dangling:
        errors.append(f"存在 {len(dangling)} 处指向不存在目标的引用：{dangling[:3]}")

    # MATCH 之后不可再有规则，否则这些规则永远不会命中
    match_indexes = [
        i for i, rule in enumerate(rules)
        if str(rule).split(",")[0].strip().upper() == "MATCH"
    ]
    if match_indexes and (len(match_indexes) > 1 or match_indexes[0] != len(rules) - 1):
        errors.append("MATCH 规则必须唯一且位于末尾")

    if errors:
        raise ConfigValidationError("；".join(errors))

    if rules and not match_indexes:
        logging.warning("未找到 MATCH 兜底规则，未匹配流量将按默认策略处理")

    logging.info(
        f"发布前校验通过：节点 {len(proxies)}，策略组 {len(groups)}，"
        f"规则 {len(rules)}，订阅 {success}/{total}"
    )


def verify_serialized(yaml_string: str, expected_proxy_count: int) -> None:
    """
    回读自检：产物必须能被 safe_load 解析，且节点数不丢，防止静默截断或序列化异常。

    :param yaml_string: (str) 即将上传的 YAML 文本
    :param expected_proxy_count: (int) 预期节点数
    :return: None，异常时抛 ConfigValidationError
    """
    try:
        reloaded = yaml.safe_load(yaml_string)
    except yaml.YAMLError as e:
        raise ConfigValidationError(f"生成的 YAML 无法回读：{e}")

    if not isinstance(reloaded, dict):
        raise ConfigValidationError("生成的 YAML 顶层不是映射结构")

    actual_count = len(reloaded.get("proxies") or [])
    if actual_count != expected_proxy_count:
        raise ConfigValidationError(
            f"回读节点数不一致：期望 {expected_proxy_count}，实际 {actual_count}"
        )

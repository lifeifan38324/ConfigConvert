import regex
import logging

# Clash 内建策略，允许被策略组直接引用
BUILTIN_POLICIES = {"DIRECT", "REJECT", "REJECT-DROP", "PASS", "COMPATIBLE", "GLOBAL"}


def build_proxy_groups(config_lines: list, node_names: list) -> list:
    """
    根据配置文件内容和已有的节点名称，构建策略组(proxy-groups)。
    对应原代码的 ProxyGroupCls.get_proxy_group() 逻辑。

    :param config_lines: (list[str]) 通过 fetch_config_lines 获取的有效配置行
    :param node_names: (list[str]) 所有可用的节点名称集合
    :return: (list[dict]) 构建好的策略组列表
    """
    proxy_groups = []

    for line in config_lines:
        if not line.startswith("custom_proxy_group="):
            continue

        logging.info(f"正在处理策略组规则：{line}")
        line_content = line.removeprefix("custom_proxy_group=")
        ruleset_list = [i.strip() for i in line_content.split("`")]

        # 基础信息提取
        group_name = ruleset_list[0]
        group_type = ruleset_list[1]
        group_proxies = []

        # 根据类型处理正则匹配和特殊字段
        if group_type == "select":
            regex_str = ""
            for item in ruleset_list[2:]:
                if "[]" in item:
                    group_proxies.append(item[2:])
                else:
                    regex_str = item
            if regex_str:
                group_proxies.extend([name for name in node_names if regex.search(regex_str, name)])

            if not group_proxies:
                group_proxies = ["DIRECT"]

            proxy_groups.append({
                "name": group_name, "type": group_type, "proxies": group_proxies
            })

        elif group_type in ["url-test", "load-balance"]:
            test_url = ruleset_list[3]
            regex_str = ruleset_list[2]
            proxy_group_interval, proxy_group_timeout, proxy_group_tolerance = ruleset_list[-1].split(',')

            group_proxies.extend([name for name in node_names if regex.search(regex_str, name)])
            if not group_proxies:
                group_proxies = ["DIRECT"]

            item = {
                "name": group_name, "type": group_type, "url": test_url,
                "interval": int(proxy_group_interval),
                "tolerance": int(proxy_group_tolerance),
                "proxies": group_proxies
            }
            if group_type == "load-balance":
                item["timeout"] = int(proxy_group_timeout)

            proxy_groups.append(item)

    return sanitize_proxy_groups(proxy_groups, node_names)


def sanitize_proxy_groups(proxy_groups: list, node_names: list) -> list:
    """
    清理策略组内的无效引用。

    远端配置可能引用已被改名/删除的策略组，或引用已下线的具体节点；
    Clash 遇到不存在的引用会拒绝加载整份配置，因此这里主动剔除并告警，
    剔除后为空的组回落 DIRECT。

    :param proxy_groups: (list[dict]) 构建好的策略组列表
    :param node_names: (list[str]) 当前可用的节点名
    :return: (list[dict]) 清理后的策略组列表（原地修改并返回）
    """
    group_names = {group["name"] for group in proxy_groups}
    valid_targets = group_names | BUILTIN_POLICIES | set(node_names)

    for group in proxy_groups:
        members = []
        dropped = []

        for name in group.get("proxies") or []:
            # 自引用同样会导致 Clash 校验失败
            if name == group["name"] or name not in valid_targets:
                dropped.append(name)
            elif name not in members:
                members.append(name)

        if dropped:
            preview = dropped[:5]
            more = f" 等 {len(dropped)} 个" if len(dropped) > 5 else ""
            logging.warning(f"策略组「{group['name']}」剔除了无效引用：{preview}{more}")

        group["proxies"] = members or ["DIRECT"]

    return proxy_groups


def build_rules(config_lines: list, fetch_external_rules_func) -> list:
    """
    生成并组装路由规则(rules)。
    对应原代码的 ProxyGroupCls.get_rules() 逻辑。

    :param config_lines: (list[str]) 通过 fetch_config_lines 获取的有效配置行
    :param fetch_external_rules_func: (Callable) 传入一个可以获取外部规则文件的函数
    :return: (list[str]) 构建好的分流规则字符串列表
    """
    rule_item_list = []

    for line in config_lines:
        if not line.startswith("ruleset="):
            continue

        logging.info(f"正在处理分流规则：{line}")
        line_content = line.removeprefix("ruleset=")
        ruleset_list = [i.strip() for i in line_content.split(",")]

        ruleset_name = ruleset_list[0]
        ruleset_target = ruleset_list[1]

        if ruleset_target.startswith("[]FINAL"):  # 特例，eg:  "[]FINAL"
            rule_item_list.append(f"MATCH,{ruleset_name}")
            continue

        if ruleset_target.startswith("[]"):  # 特例，eg: "[]GEOIP,CN"
            start_index = line_content.find("[]") + 2
            rule_item_list.append(f"{line_content[start_index:].strip()},{ruleset_name}")
            continue

        if ruleset_target.startswith("http"):
            # 外部规则拉取与转换
            external_rules = fetch_external_rules_func(ruleset_target)
            for item in external_rules:
                if item.startswith("IP-CIDR") and item.endswith("no-resolve"):
                    insert_index = item.find("no-resolve")
                    rule_item_list.append(f"{item[:insert_index]}{ruleset_name},{item[insert_index:]}")
                elif item.startswith(("USER-AGENT", "URL-REGEX", "IP-ASN")):  # 手机版clash不支持的规则
                    continue
                else:
                    rule_item_list.append(f"{item},{ruleset_name}")

    return normalize_match_rules(rule_item_list)


def normalize_match_rules(rule_item_list: list) -> list:
    """
    将 MATCH 兜底规则归位到末尾。

    MATCH 之后的所有规则永远不会命中，若远端配置把 FINAL 放在中间，
    后续规则会全部失效。此处保留最后一条 MATCH 并移到末尾；多余的 MATCH 丢弃。

    :param rule_item_list: (list[str]) 构建好的规则列表
    :return: (list[str]) 归位后的规则列表
    """
    if not rule_item_list:
        return rule_item_list

    match_indexes = [
        i for i, rule in enumerate(rule_item_list)
        if rule.split(",")[0].strip().upper() == "MATCH"
    ]
    if not match_indexes:
        logging.warning("未找到 MATCH 兜底规则，未匹配流量将按默认策略处理")
        return rule_item_list

    if len(match_indexes) > 1:
        logging.warning(f"存在 {len(match_indexes)} 条 MATCH 规则，仅保留最后一条")

    match_rule = rule_item_list[match_indexes[-1]]
    drop_set = set(match_indexes)
    rest = [rule for i, rule in enumerate(rule_item_list) if i not in drop_set]

    if len(match_indexes) == 1 and match_indexes[0] == len(rule_item_list) - 1:
        return rule_item_list

    logging.warning("MATCH 规则不在末尾，已移动到末尾以保证其余规则可达")
    return rest + [match_rule]


def assemble_final_config(template: dict, proxies: list, proxy_groups: list, rules: list) -> dict:
    """
    将所有部件组装为一个完整的字典，准备导出。

    :param template: (dict) 基础模板字典
    :param proxies: (list) 节点列表
    :param proxy_groups: (list) 策略组列表
    :param rules: (list) 规则列表
    :return: (dict) 合并后的完整字典
    """
    final_dict = template.copy()
    final_dict["proxies"] = proxies
    final_dict["proxy-groups"] = proxy_groups
    final_dict["rules"] = rules
    return final_dict

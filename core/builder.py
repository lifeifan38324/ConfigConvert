import regex
import logging


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
                elif item.startswith("USER-AGENT") or item.startswith("URL-REGEX"):
                    continue
                else:
                    rule_item_list.append(f"{item},{ruleset_name}")

    return rule_item_list


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

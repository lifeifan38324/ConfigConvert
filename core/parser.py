import yaml
import logging


def extract_nodes_from_yaml(yaml_text: str, fallback_prefix: str = "节点",
                            taken_prefixes: set = None) -> list:
    """
    解析订阅返回的 YAML 文本，提取其中的代理节点(proxies)列表。

    解析层是纯函数，任何畸形输入都收敛为「返回空列表 + 明确日志」，不向上抛异常，
    避免单个订阅的格式问题击穿整轮任务。

    :param yaml_text: (str) 机场订阅链接返回的完整 YAML 字符串
    :param fallback_prefix: (str) 订阅缺少策略组名时使用的节点名前缀
    :param taken_prefixes: (set) 已被其它订阅占用的前缀集合，命中则改用 fallback
    :return: (list[dict]) 提取出的节点列表。无法解析时返回空列表。
    """
    if not yaml_text:
        return []

    try:
        yaml_data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        logging.error(f"YAML 解析节点失败: {e}")
        return []

    # base64 订阅会被解析成字符串，此处必须显式校验类型
    if not isinstance(yaml_data, dict):
        logging.warning("订阅内容不是 Clash YAML（疑似 base64 格式），已跳过")
        return []

    proxies = yaml_data.get("proxies")
    if not isinstance(proxies, list) or not proxies:
        logging.warning("订阅内容缺少有效的 proxies 列表，已跳过")
        return []

    prefix = _resolve_prefix(yaml_data, fallback_prefix)

    # 多个机场的首个策略组常同名（如「🚀 节点选择」），撞前缀会直接造成节点重名
    if taken_prefixes is not None:
        if prefix in taken_prefixes:
            logging.warning(f"前缀「{prefix}」已被其它订阅占用，本订阅改用「{fallback_prefix}」")
            prefix = fallback_prefix
        taken_prefixes.add(prefix)

    valid_nodes = []
    for item in proxies:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        item["name"] = f"{prefix}_{item['name']}"
        valid_nodes.append(item)

    return valid_nodes


def ensure_unique_names(proxies: list) -> list:
    """
    保证节点名唯一。Clash 遇到重名节点会拒绝加载整份配置，
    因此对重复项追加递增序号（首个节点保留原名）。

    两遍扫描：先登记全部原名，再处理重名，避免生成的后缀反过来抢占
    其它节点原本合法的名字（如 A、A、A_2 应得到 A、A_3、A_2）。

    :param proxies: (list[dict]) 节点列表
    :return: (list[dict]) 处理后的节点列表（原地修改并返回）
    """
    taken = {item.get("name") for item in proxies if item.get("name")}
    used = set()
    renamed = 0

    for item in proxies:
        name = item.get("name")
        if not name:
            continue
        if name not in used:
            used.add(name)
            continue

        index = 2
        while f"{name}_{index}" in taken or f"{name}_{index}" in used:
            index += 1
        new_name = f"{name}_{index}"
        item["name"] = new_name
        used.add(new_name)
        taken.add(new_name)
        renamed += 1

    if renamed:
        logging.warning(f"检测到 {renamed} 个重名节点，已自动追加序号后缀")
    return proxies


def _resolve_prefix(yaml_data: dict, fallback: str) -> str:
    """
    从订阅的第一个策略组名推导节点前缀，取不到时回退到 fallback。

    :param yaml_data: (dict) 订阅解析后的完整字典
    :param fallback: (str) 兜底前缀
    :return: (str) 节点名前缀
    """
    groups = yaml_data.get("proxy-groups")
    if isinstance(groups, list) and groups and isinstance(groups[0], dict):
        name = str(groups[0].get("name") or "").replace("机场", "").strip()
        if name:
            return name

    logging.warning(f"订阅缺少可用策略组名，节点前缀回退为「{fallback}」")
    return fallback


def preprocess_subscribe_url(url: str) -> str:
    """
    处理单个订阅链接，例如附加必要的参数。(对应原先的 __pre_process_subscribe_list)

    :param url: (str) 原始订阅链接
    :return: (str) 处理后的订阅链接
    """
    # 此处可保留您原有的解析参数或添加 flag 的逻辑
    # 示例简化版：直接返回原 URL
    return url

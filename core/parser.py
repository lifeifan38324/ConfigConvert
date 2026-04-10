import yaml
import logging


def extract_nodes_from_yaml(yaml_text: str) -> list:
    """
    解析订阅返回的 YAML 文本，提取其中的代理节点(proxies)列表。

    :param yaml_text: (str) 机场订阅链接返回的完整 YAML 字符串
    :return: (list[dict]) 提取出的节点列表。如果解析失败返回空列表。
    """
    if not yaml_text:
        return []

    try:
        yaml_data = yaml.safe_load(yaml_text)
        if yaml_data and "proxies" in yaml_data:
            # 给节点加前缀
            airport_name = yaml_data["proxy-groups"][0]["name"][:2]
            for i in range(len(yaml_data["proxies"])):
                yaml_data["proxies"][i]["name"] = airport_name + "_" + yaml_data["proxies"][i]["name"]
            return yaml_data["proxies"]
        return []
    except yaml.YAMLError as e:
        logging.error(f"YAML 解析节点失败: {e}")
        return []


def preprocess_subscribe_url(url: str) -> str:
    """
    处理单个订阅链接，例如附加必要的参数。(对应原先的 __pre_process_subscribe_list)

    :param url: (str) 原始订阅链接
    :return: (str) 处理后的订阅链接
    """
    # 此处可保留您原有的解析参数或添加 flag 的逻辑
    # 示例简化版：直接返回原 URL
    return url

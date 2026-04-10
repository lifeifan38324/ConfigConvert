import requests
import logging


def fetch_text_from_url(url: str, is_clash_client: bool = False) -> str:
    """
    通过 HTTP GET 请求获取 URL 的文本内容。

    :param url: (str) 需要下载的链接地址
    :param is_clash_client: (bool) 是否需要伪装成 Clash 客户端拉取 (针对机场订阅)
    :return: (str) 下载到的文本内容。如果失败则返回空字符串。
    """
    headers = {}
    if is_clash_client:
        headers["user-agent"] = "clash-verge/v1.6.0"

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"网络请求失败 [URL: {url}]: {e}")
        return ""


def fetch_config_lines(url: str) -> list:
    """
    下载配置文件(如分流规则)，并清洗掉空行和注释行。

    :param url: (str) 规则配置文件的 URL
    :return: (list[str]) 清洗后的有效行列表
    """
    raw_text = fetch_text_from_url(url)
    if not raw_text:
        return []

    valid_lines = []
    for line in raw_text.split('\n'):
        line = line.strip()
        # 过滤掉空行和以 # 开头的注释行
        if line and not line.startswith("#"):
            valid_lines.append(line)
    return valid_lines

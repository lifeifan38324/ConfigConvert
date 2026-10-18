import logging
import random
import time

import requests

from config import config

# 值得重试的 HTTP 状态码：服务端临时故障与限流
RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}


class NetWorkFetcher:
    fail_request_count = 0
    retry_count = 0

    @staticmethod
    def fetch_text_from_url(url: str, is_clash_client: bool = False,
                            retries: int = None, timeout: int = None) -> str:
        """
        通过 HTTP GET 请求获取 URL 的文本内容，带指数退避重试。

        仅对可恢复的故障重试（超时、连接错误、5xx、408/429、空响应体）；
        其余 4xx 属于客户端问题，立即放弃，避免无意义地重复请求对方接口。

        :param url: (str) 需要下载的链接地址
        :param is_clash_client: (bool) 是否需要伪装成 Clash 客户端拉取 (针对机场订阅)
        :param retries: (int) 最大尝试次数，默认取 config.subscribe_retries
        :param timeout: (int) 单次请求超时秒数，默认取 config.subscribe_timeout
        :return: (str) 下载到的文本内容。最终失败则返回空字符串。
        """
        retries = retries if retries is not None else config.subscribe_retries
        timeout = timeout if timeout is not None else config.subscribe_timeout
        retries = max(1, retries)

        headers = {}
        if is_clash_client:
            headers["user-agent"] = "clash-verge/v1.6.0"

        last_error = ""
        for attempt in range(1, retries + 1):
            retryable = False

            try:
                response = requests.get(url, headers=headers, timeout=timeout)
            except requests.RequestException as e:
                # 超时、连接重置、DNS 失败均属可恢复；URL 非法属配置错误，重试无意义
                last_error = type(e).__name__
                retryable = not isinstance(e, (
                    requests.exceptions.MissingSchema,
                    requests.exceptions.InvalidSchema,
                    requests.exceptions.InvalidURL,
                    requests.exceptions.URLRequired,
                ))
            else:
                if response.status_code in RETRYABLE_STATUS:
                    last_error, retryable = f"HTTP {response.status_code}", True
                else:
                    try:
                        response.raise_for_status()
                    except requests.HTTPError:
                        # 4xx（除 408/429）重试无意义
                        last_error, retryable = f"HTTP {response.status_code}", False
                    else:
                        if response.text.strip():
                            return response.text
                        # 机场限流时常见 200 空包，值得再试
                        last_error, retryable = "响应体为空", True

            if not retryable or attempt == retries:
                break

            NetWorkFetcher.retry_count += 1
            delay = config.subscribe_backoff * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
            logging.warning(f"请求失败（{attempt}/{retries}）：{last_error}，{delay:.1f}s 后重试")
            time.sleep(delay)

        safe_url = url if url and "github" in url else "***"
        logging.error(f"网络请求失败 [URL: {safe_url}]：{last_error}，已尝试 {attempt} 次")
        NetWorkFetcher.fail_request_count += 1
        return ""

    @staticmethod
    def fetch_config_lines(url: str) -> list:
        """
        下载配置文件(如分流规则)，并清洗掉空行和注释行。

        :param url: (str) 规则配置文件的 URL
        :return: (list[str]) 清洗后的有效行列表
        """
        raw_text = NetWorkFetcher.fetch_text_from_url(url)
        if not raw_text:
            return []

        valid_lines = []
        for line in raw_text.split('\n'):
            line = line.strip()
            # 过滤掉空行和以 # 开头的注释行
            if line and not line.startswith("#"):
                valid_lines.append(line)
        return valid_lines

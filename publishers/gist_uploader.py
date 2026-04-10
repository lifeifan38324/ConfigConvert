import requests
import logging


def upload_to_github_gist(content: str, token: str, gist_id: str, filename: str) -> bool:
    """
    调用 GitHub API 更新 Gist 内容。

    :param content: (str) 需要更新的文件文本内容
    :param token: (str) GitHub 访问令牌 (GIST_TOKEN)
    :param gist_id: (str) Gist 的 ID
    :param filename: (str) Gist 中的文件名
    :return: (bool) 是否上传成功
    """
    if not gist_id or not token:
        logging.error("上传终止: 缺失 GIST_TOKEN 或 GIST_ID 环境变量。")
        return False

    url = f"https://api.github.com/gists/{gist_id}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = {
        "files": {
            filename: {"content": content}
        }
    }

    try:
        response = requests.patch(url, json=data, headers=headers)
        if response.status_code == 200:
            logging.info("成功推送到 GitHub Gist！")
            return True
        else:
            logging.error(f"Gist 更新失败。状态码: {response.status_code}, 响应: {response.text}")
            return False
    except requests.RequestException as e:
        logging.error(f"Gist API 请求异常: {e}")
        return False

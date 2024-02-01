import requests
import configparser
import json


def upload_to_gist():
    # 创建配置解析器对象
    config = configparser.ConfigParser(comment_prefixes='/', allow_no_value=True)
    # 读取配置文件
    config.read('./config/gist_config.ini', encoding='utf-8')

    # 获取字段值
    token = config['custom']['token']
    gist_id = config['custom']['gist_id']
    file_path = config['custom']['file_path']
    # 设置文件名
    file_name = config['custom']['upload_file_name']

    # 读取本地文件内容
    with open(file_path, "r", encoding="utf-8") as file:
        file_content = file.read()

    # 定义请求头
    Authorization = f"Bearer {token}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": Authorization,
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # 检查 gist_id 是否填写，已填写直接更新此 gist 仓库内容，不存在创建新的 gist
    if gist_id:     # 已存在，更新内容
        url = f"https://api.github.com/gists/{gist_id}"
        data = {"files": {file_name: {"content": file_content}}}
        response = requests.patch(url, json=data, headers=headers)

        if response.status_code == 200:     # 检查是否更新成功
            print("Updated successfully!")

        else:     # 处理更新失败的情况
            print(f"Failed to update Gist. Status code: {response.status_code}, Response: {response.text}")

    else:    # 不存在，发送 POST 请求创建新的 Gist
        url = "https://api.github.com/gists"
        data = {"description": "A description of Gist", "public": False, "files": {file_name: {"content": file_content}}}
        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 201:     # 检查是否创建成功

            # 提取新创建的 Gist ID 并赋值
            gist_id = response.json()["id"]
            config.set('custom', 'gist_id', gist_id)

            print("Successfully obtained the new gist ID!")

            # 将更改写回配置文件
            with open('config.ini', 'w', encoding='utf-8') as config_file:
                config.write(config_file)

            print("Config file updated!")

        else:     # 处理创建失败的情况
            print(f"Failed to create Gist. Status code: {response.status_code}, Response: {response.text}")


if __name__ == "__main__":
    subscribe_config_path = "config/subscribe_config.json5"
    # 创建配置解析器对象
    config = configparser.ConfigParser(comment_prefixes='/', allow_no_value=True)
    # 读取配置文件
    config.read(subscribe_config_path, encoding='utf-8')
    # 获取字段值
    custom = json.loads(config['custom']["subscribe_url_list"])
    print(custom)
    print(type(custom))
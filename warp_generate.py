import yaml
import os
import regex
import configparser
import requests


class WarpGenerate(object):
    def __init__(self):
        pass

    def __load_template(self):
        """ 获取warp_proxies.yaml中的参数 """
        cur_path = os.path.dirname(os.path.abspath(__file__))
        template_file_path = os.path.join(cur_path, "config", "warp_proxies.yaml")
        with open(template_file_path, "r", encoding="utf-8") as f:
            temp_class = yaml.safe_load(f)
        return temp_class

    def __load_yxip(self):
        """ 获取优选的ip """
        cur_path = os.path.dirname(os.path.abspath(__file__))
        yxip_file_path = os.path.join(cur_path, "config", "yxip.csv")
        with open(yxip_file_path, "r", encoding="utf-8") as f:
            ip_port_list = []
            for row in f.readlines():
                row.split()
                if row.startswith("IP"):
                    continue
                ip = regex.search(r"^([\d.]+):", row)
                port = regex.search(r":(\d+),", row)
                ip_port_list.append({"ip": ip.group(1), "port": int(port.group(1))})
        return ip_port_list

    def __generate_warp_node(self):
        temp_class = self.__load_template()
        temp = temp_class["proxies"][0]
        temp_class["proxies"] = []
        ip_port_list = self.__load_yxip()
        for i, ip_port in enumerate(ip_port_list):
            t = temp.copy()
            t["name"] = "{}-{}".format(t["name"], i)
            t["server"] = ip_port["ip"]
            t["port"] = ip_port["port"]
            temp_class["proxies"].append(t)
        yaml_format_temp_class = yaml.safe_dump(temp_class, default_flow_style=False)
        return yaml_format_temp_class

    def __upload_to_gist(self):
        # 创建配置解析器对象
        config = configparser.ConfigParser(comment_prefixes='/', allow_no_value=True)
        # 读取配置文件
        config.read('./config/gist_config_warp.ini', encoding='utf-8')

        # 获取字段值
        token = config['custom']['token']
        gist_id = config['custom']['gist_id']
        # 设置文件名
        file_name = config['custom']['upload_file_name']

        # 读取文件内容
        file_content = self.__generate_warp_node()

        # 定义请求头
        Authorization = f"Bearer {token}"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": Authorization,
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # 检查 gist_id 是否填写，已填写直接更新此 gist 仓库内容，不存在创建新的 gist
        if gist_id:  # 已存在，更新内容
            url = f"https://api.github.com/gists/{gist_id}"
            data = {"files": {file_name: {"content": file_content}}}
            response = requests.patch(url, json=data, headers=headers)

            if response.status_code == 200:  # 检查是否更新成功
                print("Updated successfully!")

            else:  # 处理更新失败的情况
                print(f"Failed to update Gist. Status code: {response.status_code}, Response: {response.text}")

        else:  # 不存在，发送 POST 请求创建新的 Gist
            url = "https://api.github.com/gists"
            data = {"description": "A description of Gist", "public": False,
                    "files": {file_name: {"content": file_content}}}
            response = requests.post(url, json=data, headers=headers)

            if response.status_code == 201:  # 检查是否创建成功

                # 提取新创建的 Gist ID 并赋值
                gist_id = response.json()["id"]
                config.set('custom', 'gist_id', gist_id)

                print("Successfully obtained the new gist ID!")

                # 将更改写回配置文件
                with open('config.ini', 'w', encoding='utf-8') as config_file:
                    config.write(config_file)

                print("Config file updated!")

            else:  # 处理创建失败的情况
                print(f"Failed to create Gist. Status code: {response.status_code}, Response: {response.text}")

    def run(self):
        self.__upload_to_gist()
        print("warp上传完成")


if __name__ == "__main__":
    w = WarpGenerate()
    w.run()

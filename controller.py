# coding:utf-8
import json5
import yaml
import json
import os
from parse_subscribe import Subscribe
from parse_convert import ConvertConfig
import parse_url
import configparser


class Controller:
    def __init__(self, subscribe_config_path=""):
        self.load_subscribe_config(subscribe_config_path)
        if self.use_subscribe_convert:
            url_dict = parse_url.parse_url(subscribe_convert)
            self.subscribe_url_list = url_dict["url"]
            self.config_url = url_dict["config"]

    def load_subscribe_config(self, subscribe_config_path):
        # 创建配置解析器对象
        with open(subscribe_config_path, "r", encoding="utf-8") as f:
            config = json5.load(f)
        # 获取字段值
        self.use_subscribe_convert = config["use_subscribe_convert"]
        self.subscribe_convert = config["subscribe_convert"]
        self.subscribe_url_list = config["subscribe_url_list"]
        self.config_url = config["config_url"]

    def load_template(self):
        cur_path = os.path.dirname(os.path.abspath(__file__))
        template_file_path = os.path.join(cur_path, "resource", "template.yaml")
        with open(template_file_path, "r", encoding="utf-8") as f:
            temp_class = yaml.safe_load(f)
        return temp_class

    def get_main_param(self):
        node_dict = Subscribe().get_node_dict(self.subscribe_url_list)
        proxies_name_list = node_dict["proxies_name_list"]
        proxies = node_dict["proxies"]
        cc = ConvertConfig()
        rules = cc.get_rules(self.config_url)
        proxy_groups = cc.get_proxy_group(self.config_url, proxies_name_list)
        return {"proxies": proxies, "proxy-groups": proxy_groups, "rules": rules}

    def output_file(self):
        basic_param = self.load_template()
        main_param = self.get_main_param()
        date = {}
        date.update(basic_param)
        date.update(main_param)
        # s = json.dumps(date)
        # print(s)
        cur_path = os.path.dirname(os.path.abspath(__file__))
        template_file_path = os.path.join(cur_path, "output", "output.yaml")
        with open(template_file_path, 'w', encoding="utf-8") as f:
            yaml.safe_dump(date, f, allow_unicode=True)


if __name__ == "__main__":
    subscribe_convert = ""
    url_dict = parse_url.parse_url(subscribe_convert)
    subscribe_url_list = url_dict["url"]
    config_url = url_dict["config"]
    c = Controller(subscribe_url_list, config_url)
    c.output_file()

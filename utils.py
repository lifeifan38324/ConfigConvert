import requests
from urllib import parse
import yaml
import json5
import regex


class ProxiesCls:
    """ 管理各个订阅的node节点信息 """

    def __init__(self):
        self.__node_list = []
        self.__parse_subscribe_list_from_config()

    def __get_nodes_from_subscribe(self, subscribe):
        """
        提取单个订阅链接中的节点
        :param subscribe:给定的可以直接访问的订阅地址url，或者包括请求头信息
        """
        # 下载配置文件
        headers = {"user-agent": "clash-verge/v1.3.8"}
        cfg = requests.get(url=subscribe, headers=headers).text
        # 解析配置文件
        yaml_class = yaml.load(cfg, Loader=yaml.FullLoader)
        print(yaml_class)
        # 提取其中的节点信息
        nodes = yaml_class["proxies"]
        return nodes

    def __get_all_nodes(self, subscribe_list: list):
        """ 获取所有订阅链接的节点信息 """
        for subscribe in subscribe_list:
            nodes = self.__get_nodes_from_subscribe(subscribe)
            self.__node_list.extend(nodes)

    def __pre_process_subscribe_list(self, subscribe_list):
        """ 预处理配置文件的订阅链接 """
        # 1.去除空值
        subscribe_list = [i for i in subscribe_list if i]
        # 2.解析后缀参数
        for i, subscribe in enumerate(subscribe_list):
            url = parse.urlparse(subscribe)
            parad = parse.parse_qs(url.query)
            # print(type(parad))
            # print(parad)
            flag = False
            ks = ["flag", "types"]
            for s in ks:
                if s in parad.keys():
                    flag = True
            if "gist.githubusercontent.com" in subscribe:
                flag = True
            if not flag:
                subscribe_list[i] = subscribe + "&flag=clash"

        return subscribe_list

    def __parse_subscribe_list_from_config(self):
        """ 处理配置文件中的订阅节点列表 """
        # 读取订阅配置文件
        subscribe_config_path = "./config/subscribe_config.json5"
        with open(subscribe_config_path, "r", encoding="utf-8") as f:
            config = json5.load(f)
        subscribe_list = config["subscribe_list"]
        # 提取其中的节点信息
        subscribe_list = self.__pre_process_subscribe_list(subscribe_list)
        self.__get_all_nodes(subscribe_list)

    def get_nodes(self):
        """ 获取所有节点 """
        return self.__node_list

    def get_nodes_name(self):
        """ 获取所有节点的名称 """
        return [i["name"] for i in self.__node_list]


class ProxyGroupCls:
    """ 处理代理组和分流规则 """
    def __init__(self):
        pass

    def __get_file_from_url(self, url):
        """ 下载url中的文件，并删除空行和注释，返回行列表 """
        config_content = requests.get(url=url).text
        config_content_rows = []
        for i in config_content.split('\n'):
            i.strip()
            if i and (not i.startswith("#")):
                config_content_rows.append(i)  # 去除首尾空格
        return config_content_rows


    """ 下载并预处理配置转换文件 """
    def __get_file_from_config(self):
        """ 下载配置文件中config_url中的文件，并删除空行和注释，返回行列表 """
        # 读取订阅配置文件中的 config_url
        subscribe_config_path = "./config/subscribe_config.json5"
        with open(subscribe_config_path, "r", encoding="utf-8") as f:
            config = json5.load(f)
        config_url = config["config_url"]
        # 下载 config_url 到 config_content
        config_content_rows = self.__get_file_from_url(config_url)
        return config_content_rows

    def get_proxy_group(self):
        """ 获取并生成proxy_group """

        proxy_group_item_list = []
        proxy_group_item = None
        proxies_name_list = ProxiesCls().get_nodes_name()
        for res_line in self.__get_file_from_config():
            if res_line.startswith("custom_proxy_group="):  # 处理custom_proxy_group的行
                print("正在处理：{}".format(res_line))
                res_line = res_line.removeprefix("custom_proxy_group=")
                ruleset_list = [i.strip() for i in res_line.split("`")]

                proxy_group_name = ruleset_list[0]  # 策略组的名称
                proxy_group_type = ruleset_list[1]  # 策略组的类型
                proxy_group_proxies = []  # 策略组的元素，包括其他策略组 和 节点
                if proxy_group_type == "select":  # 处理"select"类型的策略组
                    regex_str = ""
                    for i in ruleset_list[2:]:  # 从第2个开始有策略组元素
                        if "[]" in i:
                            proxy_group_proxies.append(i[2:])  # 去除"[]"并加入到策略组中
                        else:
                            regex_str = i
                    if regex_str:
                        for i in proxies_name_list:  # 用正则 筛选proxies_name_list中的节点
                            res = regex.search(regex_str, i)
                            if res:
                                proxy_group_proxies.append(i)
                    if not proxy_group_proxies:  # 如果最终筛选结果为空, 则将策略集重置为"DIRECT"
                        proxy_group_proxies = ["DIRECT"]
                    proxy_group_item = {"name": proxy_group_name, "type": proxy_group_type,
                                        "proxies": proxy_group_proxies}
                if proxy_group_type == "url-test":  # 处理"url-test"类型的策略组
                    test_url = ruleset_list[3]
                    regex_str = ruleset_list[2]
                    proxy_group_interval, lff, proxy_group_tolerance = ruleset_list[-1].split(',')
                    for i in proxies_name_list:
                        res = regex.search(regex_str, i)
                        if res:
                            proxy_group_proxies.append(i)
                    if not proxy_group_proxies:
                        proxy_group_proxies = ["DIRECT"]
                    proxy_group_item = {"name": proxy_group_name, "type": proxy_group_type, "url": test_url,
                                        "interval": int(proxy_group_interval), "tolerance": int(proxy_group_tolerance),
                                        "proxies": proxy_group_proxies}
                proxy_group_item_list.append(proxy_group_item)
        return proxy_group_item_list

    def get_rules(self):
        """ 获取并生成 ruleset """
        rule_item_list = []  # 存储所有rule
        # 遍历config所有的行
        for res_line in self.__get_file_from_config():
            if res_line.startswith("ruleset="):  # 处理ruleset的行
                print("正在处理：{}".format(res_line))
                res_line = res_line.removeprefix("ruleset=")
                ruleset_list = [i.strip() for i in res_line.split(",")]  # 按照","分割行

                ruleset_name = ruleset_list[0]
                if ruleset_list[1].startswith("[]FINAL"):  # 特例，eg:  "[]FINAL"
                    rule_item = "{}, {}".format("MATCH", ruleset_name)
                    rule_item_list.append(rule_item)
                    continue
                if ruleset_list[1].startswith("[]"):  # 特例，eg: "[]GEOIP,CN"
                    stert_index = res_line.find("[]") + 2
                    rule_item = "{}, {}".format(res_line[stert_index:], ruleset_name)
                    rule_item_list.append(rule_item)
                    continue
                if ruleset_list[1].startswith("http"):  # 处理http的规则集
                    ruleset_url = ruleset_list[1]
                    for item in self.__get_file_from_url(ruleset_url):
                        if item.startswith("IP-CIDR") and item.endswith("no-resolve"):
                            insert_index = item.find("no-resolve")
                            rule_item = "{}{},{}".format(item[:insert_index], ruleset_name, item[insert_index:])
                        elif item.startswith("USER-AGENT") | item.startswith("URL-REGEX"):
                            continue
                        else:
                            rule_item = "{},{}".format(item, ruleset_name)
                        rule_item_list.append(rule_item)
        return rule_item_list


if __name__ == '__main__':
    # p = ProxyGroupCls()
    # for i in p.get_rules():
    #     print(i)
    subscribe = ""
    headers = {"user-agent": "clash-verge/v1.3.8"}
    cfg = requests.get(url=subscribe, headers=headers).text
    print(cfg)
    # yaml_class = yaml.load(cfg, Loader=yaml.FullLoader)
    # print(yaml_class["proxies"])

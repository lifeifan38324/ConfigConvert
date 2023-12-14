# coding:utf-8
import regex
import requests


class ConvertConfig:
    """ 解析配置转换文件 """
    def __get_file_from_url(self, config_url):
        """ 下载url中的文件，并删除空行和注释，返回行列表 """
        config_content = requests.get(url=config_url).text
        config_content_rows = []
        for i in config_content.split('\n'):
            if i and (not i.startswith("#")):
                config_content_rows.append(i.strip())  # 去除首尾空格
        return config_content_rows

    def get_rules(self, config_url):
        """ 获取并生成 ruleset """
        rule_item_list = []  # 存储所有rule
        # 遍历config所有的行
        for res_line in self.__get_file_from_url(config_url):
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

    def get_proxy_group(self, config_url, proxies_name_list):
        """ 获取并生成proxy_group """

        proxy_group_item_list = []
        proxy_group_item = None
        for res_line in self.__get_file_from_url(config_url):
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


if __name__ == "__main__":
    config_url = ""
    proxy_group = ""
    cc = ConvertConfig()
    res = cc.get_rules(config_url)
    print(res)

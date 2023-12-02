# coding:utf-8
import requests
import yaml


class Subscribe:
    """ 用于提取订阅列表中的节点 """
    def get_node_dict(self, subscribe_url_list):
        self.__pre_process_url_list(subscribe_url_list)
        node_class = self.__get_all_node_list(subscribe_url_list)
        return node_class

    def __pre_process_url_list(self, subscribe_url_list):
        """ 预处理订阅地址，在尾部加‘&flag=clash’ """
        for i, subscribe_url in enumerate(subscribe_url_list):
            if "flag=" not in subscribe_url:
                subscribe_url_list[i] = subscribe_url + "&flag=clash"

    def __get_node_list_from_subscribe(self, subscribe_url):
        """ 处理单个订阅链接 """
        cfg = requests.get(url=subscribe_url).text
        yaml_class = yaml.load(cfg, Loader=yaml.FullLoader)
        proxies_list = yaml_class["proxies"]
        proxies_name_list = [i["name"] for i in proxies_list]
        return {"proxies_name_list": proxies_name_list, "proxies": proxies_list}

    def __get_all_node_list(self, subscribe_url_list):
        """ 按顺序处理所有的url订阅 """
        all_proxies_name_list = []
        all_proxies_list = []
        for subscribe_url in subscribe_url_list:
            proxies_dict = self.__get_node_list_from_subscribe(subscribe_url)
            all_proxies_name_list.extend(proxies_dict["proxies_name_list"])
            all_proxies_list.extend(proxies_dict["proxies"])
        return {"proxies_name_list": all_proxies_name_list, "proxies": all_proxies_list}


if __name__ == "__main__":
    subscribe_url_list = []
    s = Subscribe()
    a = s.get_node_dict(subscribe_url_list)
    for i in a.keys():
        print(i)
        print(a[i])
        for j in a[i]:
            print("\t", j)
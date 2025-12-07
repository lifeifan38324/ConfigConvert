# coding:utf-8
import yaml
import os
from upload_to_gist import upload_to_gist
import utils


class Controller:
    def __init__(self):
        pass

    def __load_template(self):
        """ 获取template.yaml中的参数 """
        cur_path = os.path.dirname(os.path.abspath(__file__))
        template_file_path = os.path.join(cur_path, "resource", "template.yaml")
        with open(template_file_path, "r", encoding="utf-8") as f:
            temp_class = yaml.safe_load(f)
        return temp_class

    def __get_main_param(self):
        """ 获取proxies、proxy_groups和rules """
        p = utils.ProxiesCls()
        proxies_name_list = p.get_nodes_name()
        proxies = p.get_nodes()
        pg = utils.ProxyGroupCls()
        rules = pg.get_rules()
        proxy_groups = pg.get_proxy_group()
        return {"proxies": proxies, "proxy-groups": proxy_groups, "rules": rules}

    def __get_all_file(self):
        basic_param = self.__load_template()
        main_param = self.__get_main_param()
        date = {}
        date.update(basic_param)
        date.update(main_param)
        return date

    def __output_file(self):
        date = self.__get_all_file()
        cur_path = os.path.dirname(os.path.abspath(__file__))
        template_file_path = os.path.join(cur_path, "output", "output.yaml")
        # 提取目录路径
        output_dir = os.path.dirname(template_file_path)
        # 检查并创建目录（多层目录也能创建，exist_ok=True 避免重复创建报错）
        os.makedirs(output_dir, exist_ok=True)

        with open(template_file_path, 'w', encoding="utf-8") as f:
            yaml.safe_dump(date, f, allow_unicode=True)

    def run(self):
        # 输出文件到output.yaml
        self.__output_file()
        # 上传输出文件到gist
        upload_to_gist()


if __name__ == "__main__":
    pass

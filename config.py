import os
import logging

# 配置基础日志格式
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class Config:
    def __init__(self):
        """ 初始化并校验所有所需的环境变量 """
        # 基础模板路径 (相对于主程序执行目录)
        self.template_path = os.path.join("resource", "template.yaml")

        # 配置文件的路径
        self.config_url = os.getenv("CONFIG_URL")

        # 将逗号分隔的订阅列表转换为真实的 Python 列表，并去除空值
        raw_subscribe_list = os.getenv("SUBSCRIBE_LIST", "")
        self.subscribe_list = [url.strip() for url in raw_subscribe_list.split(",") if url.strip()]

        # 输出文件的路径
        self.output_path = os.path.join("output", "output.yaml")

        # 上传gist需要的参数
        self.gist_token = os.getenv("GIST_TOKEN")
        self.gist_id = os.getenv("GIST_ID")
        self.gist_filename = os.getenv("GIST_FILENAME")


# 实例化一个单例供全局使用
config = Config()

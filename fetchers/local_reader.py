import yaml
import logging


def load_yaml_template(file_path: str) -> dict:
    """
    加载本地基础模板文件。

    :param file_path: (str) 模板文件的相对或绝对路径
    :return: (dict) 模板的字典结构，如果文件不存在则返回空字典
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logging.error(f"找不到模板文件: {file_path}")
        return {}
    except yaml.YAMLError as e:
        logging.error(f"解析模板文件失败: {e}")
        return {}

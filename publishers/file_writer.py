import os
import yaml
import logging


def save_yaml_to_file(data: dict, file_path: str) -> None:
    """
    将字典数据序列化为 YAML 字符串并保存到本地文件。

    :param data: (dict) 最终配置字典
    :param file_path: (str) 输出文件路径
    :return: None
    """
    output_dir = os.path.dirname(file_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        with open(file_path, 'w', encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
        logging.info(f"本地文件写入成功: {file_path}")

    except Exception as e:
        logging.error(f"保存文件失败: {e}")

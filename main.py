import logging
import yaml
from config import config

# 引入各个解耦模块
from fetchers.local_reader import load_yaml_template
from fetchers.network_fetcher import fetch_text_from_url, fetch_config_lines
from core.parser import preprocess_subscribe_url, extract_nodes_from_yaml
from core.builder import build_proxy_groups, build_rules, assemble_final_config
from publishers.file_writer import save_yaml_to_file
from publishers.gist_uploader import upload_to_github_gist


def main():
    logging.info("=== 开始执行配置转换流程 ===")

    # # 1. 读取基础模板
    template_data = load_yaml_template(config.template_path)

    # 2. 拉取并解析所有的代理节点 (proxies)
    all_proxies = []
    for sub_url in config.subscribe_list:
        processed_url = preprocess_subscribe_url(sub_url)
        # 伪装成客户端获取订阅 YAML
        yaml_text = fetch_text_from_url(processed_url, is_clash_client=True)
        nodes = extract_nodes_from_yaml(yaml_text)
        all_proxies.extend(nodes)

    logging.info(f"共获取到 {len(all_proxies)} 个代理节点。")
    node_names = [node["name"] for node in all_proxies if "name" in node]

    # 3. 拉取分流规则配置文件
    logging.info(f"正在拉取配置文件: {config.config_url}")
    config_lines = fetch_config_lines(config.config_url)

    # 4. 核心构建：生成策略组与路由规则
    proxy_groups = build_proxy_groups(config_lines, node_names)
    # 将拉取外部规则的函数依赖注入给 build_rules
    rules = build_rules(config_lines, fetch_external_rules_func=fetch_config_lines)

    # 5. 组装最终配置字典
    final_data = assemble_final_config(template_data, all_proxies, proxy_groups, rules)

    # # 6. 转换格式与上传
    # save_yaml_to_file(final_data, config.output_path)  # 保存到文件中，用于本地查看
    yaml_string = yaml.safe_dump(final_data, allow_unicode=True, sort_keys=False)

    if yaml_string:
        upload_to_github_gist(
            content=yaml_string,
            token=config.gist_token,
            gist_id=config.gist_id,
            filename=config.gist_filename
        )

    logging.info("=== 流程执行完毕 ===")


if __name__ == "__main__":
    main()

文档目录以及结构说明
```text
configconvert/
├── config.py             # 集中管理所有环境变量和应用配置
├── main.py               # 程序的唯一入口，负责依赖注入和流程编排
├── models/               # 数据模型层 (可选，推荐使用 dataclasses 或 Pydantic)
│   └── types.py          # 定义 Node, ProxyGroup 等数据结构
├── fetchers/             # 网络/I/O层 (只负责获取数据，不处理逻辑)
│   ├── sub_fetcher.py    # 负责下载订阅链接
│   └── rule_fetcher.py   # 负责下载自定义分流规则和模板
├── core/                 # 核心业务逻辑层 (纯函数，容易测试)
│   ├── parser.py         # 负责解析 YAML、URI参数等
│   └── builder.py        # 负责执行正则匹配，将节点分配到对应的策略组，生成最终结构
└── publishers/           # 输出层
    ├── file_writer.py    # 负责将字典安全地序列化为 YAML 并写入本地
    └── gist_uploader.py  # 负责调用 GitHub API 上传
```

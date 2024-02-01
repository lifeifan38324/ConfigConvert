from controller import Controller
from upload_to_gist import upload_to_gist


c = Controller(subscribe_config_path="config/subscribe_config.json5")
c.output_file()

# 上传输出文件到gist
upload_to_gist()

# coding=utf-8
import urllib
from urllib import parse


def parse_url(encoded_url):
    """ URL解码 """
    # 参数提取
    parse_res = parse.urlparse(encoded_url)
    param_list = parse_res.query.split('&')
    res_dict = {}
    for param in param_list:
        decode_param = urllib.parse.unquote(param)  # Base64解码
        # print(decode_param)
        index = decode_param.find("=")
        key = decode_param[:index]
        value = decode_param[index+1:]
        if key == "url":
            value = value.split('|')
        res_dict[key] = value
    return res_dict


if __name__ == "__main__":
    txt = 'subscribe_url'
    res = parse_url(txt)
    for k, v in res.items():
        print("{} = {}".format(k, v))


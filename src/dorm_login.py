# pyright: standard
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 校园网自动登录脚本
# 用法: 填写账号、密码后运行。会根据网络环境自动选择登录方式。

import json
import re
import time
from datetime import datetime

import requests

from config import config

# ====== 用户配置 ======
username: str = config.get("USERNAME") or ""  # 学号/账号
password: str = config.get("PASSWORD") or ""  # 密码

# ====== 登录地址推测 ======
# 有线网络通常是 192.168.115.8, CMCC 无线网络一般是 192.168.116.8
wired_ip = "192.168.115.8"
cmcc_ip = "192.168.116.8"


def extract_json(raw_text: str):
    match = re.search(r"dr(\d+)\((.*)\)", raw_text.strip())
    if not match:
        raise ValueError("无法提取 JSON 数据")
    timestamp = int(match.group(1)) // 1000
    data = json.loads(match.group(2))
    return data, timestamp


def login_dorm(username: str, password: str):
    """用于登录宿舍有线网络"""
    timestamp = int(time.time() * 1000)
    login_url = f"http://{wired_ip}/drcom/login"

    params = {
        "callback": f"dr{timestamp}",
        "DDDDD": username,
        "upass": password,
        "0MKKey": "123456",
        "R1": "0",
        "R3": "0",
        "R6": "0",
        "para": "00",
        "v6ip": "",
        "R7": "0",
        "_": timestamp,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
        "Referer": f"http://{wired_ip}/",
    }

    resp = requests.get(login_url, params=params, headers=headers)
    data, ts = extract_json(resp.text)

    print("[有线网络登录结果]")
    print(json.dumps(data, indent=4, ensure_ascii=False))
    # 判断登录状态
    if data.get("result") == 0 and data.get("msga") == "error5 waitsec <3":
        print("该设备已经登录了")
    elif data.get("result") == 1 and data.get("uid") == username:
        print("登录成功")
    elif data.get("result") == 0 and data.get("uid") == username:
        print("登录成功 (已在线)")
    else:
        print("登录状态未知")
    print("请求时间:", datetime.fromtimestamp(ts))

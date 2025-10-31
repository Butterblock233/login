# pyright: standard
import json
import re
import time
from datetime import datetime
from typing import NamedTuple
from urllib.parse import urlencode

import requests


class CMCCParamater(NamedTuple):
    username: str
    password: str
    login_ip: str = "192.168.116.8"
    login_url: str = ""
    wlan_acname: str = "SR8805F"
    wlan_acip: str = "218.207.103.209"
    wlan_mac: str = "98BD80DBFE66"
    wlan_ip: str = ""


class CMCCLogin:
    """CMCC登录管理器，负责完整的登录流程"""

    def __init__(self, username: str, password: str) -> None:
        """
        初始化登录管理器

        Args:
                                        username: 用户名/学号
                                        password: 密码
        """
        # 创建初始参数对象
        self.params = CMCCParamater(username=username, password=password)

        # 在初始化时自动解析重定向获取完整参数
        self.parse_redirect()

    def parse_redirect(
        self, url: str = "http://www.msftconnecttest.com/redirect"
    ) -> "CMCCLogin":
        """
        从重定向页面解析校园网登录参数

        Args:
                                        url: 重定向检测URL

        Returns:
                                        self: 支持链式调用
        """
        import re

        from .redirect import parse_redirect

        print(f"解析重定向: {url}")
        redirect_url = parse_redirect(url)
        if redirect_url is None:
            raise ValueError("无法解析重定向url")

        m = re.search(
            r"wlanuserip=([\d\.]+).*?wlanacname=([^&]+).*?wlanacip=([\d\.]+).*?(?:mac|wlanusermac)=([\w\-:]+)",
            redirect_url,
            re.I,
        )
        if not m:
            print("未能从重定向 URL 提取完整参数，使用默认。")
            self.params = self.params._replace(wlan_ip="172.30.137.210")
            return self

        wlan_ip, wlan_acname, wlan_acip, wlan_mac = m.groups()
        wlan_mac = wlan_mac.replace("-", "").replace(":", "").upper()

        # 更新参数对象
        self.params = self.params._replace(
            wlan_acname=wlan_acname,
            wlan_acip=wlan_acip,
            wlan_mac=wlan_mac,
            wlan_ip=wlan_ip,
            login_url=redirect_url,
        )

        return self

    def construct_url(self) -> tuple[str, dict]:
        """
        构造CMCC登录URL和请求头

        Returns:
                                        tuple: (登录URL, 请求头字典)
        """
        ts = int(time.time() * 1000)
        params = {
            "c": "Portal",
            "a": "login",
            "callback": f"dr{ts}",
            "login_method": "1",
            "user_account": f",0,{self.params.username}@fjwlan",
            "user_password": self.params.password,
            "wlan_user_ip": self.params.wlan_ip,
            "wlan_user_mac": self.params.wlan_mac,
            "wlan_ac_ip": self.params.wlan_acip,
            "wlan_ac_name": self.params.wlan_acname,
            "jsVersion": "3.0",
            "_": ts,
        }

        url = f"http://{self.params.login_ip}:801/eportal/?{urlencode(params)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "Referer": self.params.login_url,
            "Accept": "*/*",
            "Connection": "keep-alive",
        }

        return url, headers

    def login(self) -> str | None:
        """
        执行完整的CMCC登录流程

        Returns:
                                        str | None: 原始响应文本，失败时返回None
        """
        print("获取登录参数...")

        # 1. 解析重定向获取完整参数
        self.parse_redirect()

        # 2. 构造登录请求
        url, headers = self.construct_url()

        print(f"尝试登录 {url}")
        try:
            res = requests.get(url, headers=headers, timeout=12)
            res.raise_for_status()
        except requests.RequestException as e:
            print("登录请求失败：", e)
            return None

        raw = res.text.strip()
        print("登录返回:", raw)
        return raw

    def parse_result(self, raw: str):
        """
        解析 CMCC 登录结果（JSONP 格式）

        Args:
                        raw: 原始响应文本，如 dr171234567890({...})

        Returns:
                        dict: 包含解析结果的字典，含状态码、消息、时间戳等
        """
        print("Raw Response:\n", raw)

        # 1. 解析 JSONP 外壳
        json_match = re.match(r"dr(\d+)\((.*)\)", raw)
        if not json_match:
            print("无法解析服务器响应：不符合 JSONP 格式")
            return {"error": "invalid_response", "raw": raw}

        timestamp_ms_str, json_str = json_match.groups()
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSON 解析失败: {e}")
            return {"error": "json_decode_error", "raw": raw}

        # 2. 提取关键字段
        ret_code = data.get("ret_code") or data.get("result", "")
        msg = data.get("msg", "")
        uid = data.get("uid", "")

        # 3. 统一转为字符串（有些返回可能是 int）
        if isinstance(ret_code, int):
            ret_code = str(ret_code)

        # 4. 状态码含义映射
        STATUS_MAP = {
            "1": "登录成功",
            "8": "用户名或密码错误",
            "logout_ok": "退出成功",
        }

        status_msg = STATUS_MAP.get(ret_code, f"未知返回码: {ret_code}")

        # 5. 输出结果
        print("\n[CMCC 登录结果]")
        print(f"状态: {status_msg}")
        if msg:
            print(f"消息: {msg}")
        if uid:
            print(f"用户: {uid}")

        # 6. 解析请求时间
        try:
            request_time = datetime.fromtimestamp(int(timestamp_ms_str) // 1000)
            print(f"请求时间: {request_time}")
        except (ValueError, OSError):
            request_time = None
            print("无法解析请求时间")

    def run(self):
        result = self.login()
        if result is None:
            return
        self.parse_result(result)

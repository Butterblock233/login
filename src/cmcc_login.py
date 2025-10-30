import json
import re
import time
from datetime import datetime
from typing import NamedTuple
from urllib.parse import urlencode

import requests


def is_cmcc() -> bool:
    import subprocess

    wifi = subprocess.check_output(["netsh", "WLAN", "show", "interfaces"])
    data = wifi.decode("utf-8")
    ssid = "CMCC-PTU"
    if ssid in data:
        print(f"connected to {ssid}")
        return True
    else:
        print(f"{ssid} not connected")
        return False


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
        print(f"解析重定向: {url}")
        try:
            resp = requests.get(url, timeout=5, allow_redirects=False)
        except requests.RequestException as e:
            print(f"获取重定向页面失败: {e}")
            self.params = self.params._replace(wlan_ip="172.30.137.210")
            return self

        redirect_url = None

        # 1. 从 HTTP 头获取
        if resp.status_code in [301, 302, 303, 307, 308]:
            redirect_url = resp.headers.get("Location", "")
            print(f"从 HTTP 头部获取到重定向 URL: {redirect_url}")
        else:
            # 2. 从 HTML 提取
            m = re.search(r'location\.href\s*=\s*"(http[^"]+)"', resp.text)
            if m:
                redirect_url = m.group(1)
                print(f"从 HTML 提取到重定向 URL: {redirect_url}")

        if not redirect_url:
            print("未能提取重定向 URL，使用默认参数。")
            self.params = self.params._replace(wlan_ip="172.30.137.210")
            return self

        # 从重定向 URL 解析参数
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

    def parse_result(self, raw: str) -> dict:
        """
        解析CMCC登录结果

        Args:
                raw: 原始响应文本

        Returns:
                dict: 解析后的结果字典
        """
        print("Raw Response:\n", raw)

        # 1. 解析 JSONP
        m = re.match(r"dr\d+\((.*)\)", raw)
        if not m:
            print("无法解析服务器响应。")
            return {}

        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError as e:
            print(f"JSON 解析失败: {e}")
            return {}

        # 2. 解析返回码
        result = data.get("result", "")
        msg = data.get("msg", "")
        ret_code = data.get("ret_code", "")

        print(f"返回码: {ret_code}")
        print(f"结果: {result}")
        print(f"消息: {msg}")

        # 3. 根据返回码判断状态
        if ret_code == "2":
            print("登录成功！")
        elif ret_code == "1":
            print("登录失败：", msg)
        else:
            print("未知状态：", msg)

        # 4. 打印请求时间
        ts_str = re.match(r"^dr(\d+)", raw)
        if ts_str:
            print("请求时间：", datetime.fromtimestamp(int(ts_str.group(1)) // 1000))

        return {"ret_code": ret_code, "result": result, "msg": msg, "raw": raw}

    def run(self):
        result = self.login()
        if result is not None:
            print(self.parse_result(result))


if __name__ == "__main__":
    login = CMCCLogin("username", "password")
    login.run()

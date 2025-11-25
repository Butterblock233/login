import re

import requests
from requests import Response


def is_cmcc() -> bool:
    import subprocess

    wifi = subprocess.check_output(["netsh", "WLAN", "show", "interfaces"])
    data = wifi.decode("utf-8")
    ssid = ["CMCC-PTU", "programer"]
    if any(i in data for i in ssid):
        return True
    else:
        return False


def get_redirect_response(
    url: str = "http://www.msftconnecttest.com/redirect",
    timeout: int = 10,
):
    s = requests.session()
    s.proxies.clear()
    s.trust_env = False
    try:
        result: Response = s.get(
            url, timeout=timeout, proxies=None, allow_redirects=False, verify=False
        )
        print(result.headers)
        return result
    except Exception as e:
        print(f"Failed to get redirect url {e}")
        raise


def parse_redirect(resp: Response = get_redirect_response()) -> str | None:
    """
    从重定向页面解析校园网登录参数

    Args:
            resp: 从重定向url获取的响应
            max_retries: 最大重试次数

    Returns:
            str: 用于登录的url
    """

    print(resp.headers)

    # 1. 从 HTTP 头获取
    if resp.status_code in [301, 302, 303, 307, 308]:
        redirect_url = resp.headers.get("Location", "")
        if "go.microsoft.com" in redirect_url:
            print("该设备已经登录过了")
            return None
        elif redirect_url:
            print(f"从 HTTP headers获取到重定向 URL: {redirect_url}")
            return redirect_url
    else:
        # 2. 从 HTML 提取
        m = re.search(r'location\.href\s*=\s*"(http[^"]+)"', resp.text)
        if m:
            redirect_url = m.group(1)
            print(f"从 HTML 提取到重定向 URL: {redirect_url}")
            return redirect_url

    return None


if __name__ == "__main__":
    url = get_redirect_response()
    if url:
        print(url)
    else:
        print("Failed to get redirect URL")

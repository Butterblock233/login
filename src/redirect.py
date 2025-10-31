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


def parse_redirect(url: str = "http://www.msftconnecttest.com/redirect") -> str | None:
    """
    从重定向页面解析校园网登录参数

    Args:
                                    url: 重定向检测URL, 默认为`http://www.msftconnecttest.com/redirect`

    Returns:
                                    str: 用于登录的url
    """
    import re

    import requests

    resp = requests.get(url, allow_redirects=False, timeout=8)
    # 1. 从 HTTP 头获取
    if resp.status_code in [301, 302, 303, 307, 308]:
        redirect_url = resp.headers.get("Location", "")
        if "go.microsoft.com" in redirect_url:
            print("该设备已经登录过了")
            return
        else:
            print(f"从 HTTP 头部获取到重定向 URL: {redirect_url}")
            return redirect_url
    else:
        # 2. 从 HTML 提取
        m = re.search(r'location\.href\s*=\s*"(http[^"]+)"', resp.text)
        if m:
            redirect_url = m.group(1)
            print(f"从 HTML 提取到重定向 URL: {redirect_url}")
            return redirect_url


if __name__ == "__main__":
    url = parse_redirect()
    print(url)

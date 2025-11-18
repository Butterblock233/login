def is_cmcc() -> bool:
    import subprocess

    wifi = subprocess.check_output(["netsh", "WLAN", "show", "interfaces"])
    data = wifi.decode("utf-8")
    ssid = ["CMCC-PTU", "programer"]
    if any(i in data for i in ssid):
        print("CMCC connected")
        return True
    else:
        print("CMCC not connected")
        return False


def parse_redirect(
    url: str = "http://www.msftconnecttest.com/redirect", max_retries: int = 3
) -> str | None:
    """
    从重定向页面解析校园网登录参数

    Args:
        url: 重定向检测URL, 默认为`http://www.msftconnecttest.com/redirect`
        max_retries: 最大重试次数

    Returns:
        str: 用于登录的url
    """
    import re
    import time

    import requests

    for attempt in range(max_retries):
        try:
            # 使用系统默认代理设置，而不是强制禁用代理
            resp = requests.get(url, allow_redirects=False, timeout=10)

            # 1. 从 HTTP 头获取
            if resp.status_code in [301, 302, 303, 307, 308]:
                redirect_url = resp.headers.get("Location", "")
                if "go.microsoft.com" in redirect_url:
                    print("该设备已经登录过了")
                    return None
                elif redirect_url:
                    print(f"从 HTTP 头部获取到重定向 URL: {redirect_url}")
                    return redirect_url

            # 2. 从 HTML 提取
            m = re.search(r'location\.href\s*=\s*"(http[^"]+)"', resp.text)
            if m:
                redirect_url = m.group(1)
                print(f"从 HTML 提取到重定向 URL: {redirect_url}")
                return redirect_url

            # 3. 如果既没有重定向头也没有JS重定向，检查是否已经联网
            if resp.status_code == 200 and len(resp.text) < 100:
                print("可能已经连接到互联网，无需登录")
                return None

        except requests.exceptions.Timeout:
            print(f"请求超时 (尝试 {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待2秒后重试
            continue

        except requests.exceptions.ConnectionError as e:
            print(f"连接错误: {e} (尝试 {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2)
            continue

        except Exception as e:
            print(f"其他错误: {e} (尝试 {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2)
            continue

    print(f"经过 {max_retries} 次尝试后仍无法解析重定向")
    return None


if __name__ == "__main__":
    url = parse_redirect()
    print(url)

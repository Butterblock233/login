# pyright: strict
from src.cmcc_login import CMCCLogin
from src.config import config
from src.redirect import is_cmcc


def main():
    username: str = config.get("USERNAME") or ""
    password: str = config.get("PASSWORD") or ""
    if username == "" or password == "":
        print("username or password not found")
        return

    if is_cmcc():
        print("CMCC connected")
        login = CMCCLogin(username, password)
        login.run()
    else:
        from src.dorm_login import login_dorm

        login_dorm(username, password)


if __name__ == "__main__":
    main()

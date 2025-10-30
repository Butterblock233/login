from src.cmcc_login import CMCCLogin, is_cmcc
from src.config import config


def main():
    username = config.get("USERNAME")
    password = config.get("PASSWORD")
    if not username or not password:
        print("Username or password not found")
        return

    if is_cmcc():
        login = CMCCLogin(username, password)
        login.run()
    else:
        from src.login import login_dorm

        login_dorm(username, password)


if __name__ == "__main__":
    main()

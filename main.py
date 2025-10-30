from src.cmcc_login import CMCCLogin, is_cmcc


def main():
    username: str = "username"
    password: str = "password"
    if is_cmcc():
        login = CMCCLogin(username, password)
        login.run()
    else:
        from src.login import login_dorm

        login_dorm(username, password)


if __name__ == "__main__":
    main()

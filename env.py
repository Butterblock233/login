import os

from dotenv import set_key

# Template env config
config = {"USERNAME": "用户名", "PASSWORD": "你的密码"}

if os.path.exists(".env"):
    os.remove(".env")
    print("Removed existing .env file")
for key, value in config.items():
    _ = set_key(".env",key,value)
print("Created template .env file")

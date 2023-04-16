#!/usr/local/bin/python3
import os
import sys
import paramiko

CONF_FILE = './rp.conf' # 対象RPのIPアドレス
TEMP_FILE = './template/script.sh' # テンプレートファイル
SCRIPT_FILE = "./script.sh" # RP上で実行させるスクリプトファイル
USERNAME = 'pi'
PASSWORD = 'raspberry'
URL = 'https://raw.githubusercontent.com/isk727/RP-PR/main/'

def main():
    ver = input('Enter update version : ')
    if ver == '':
        sys.exit('canceled.')
    data = open(CONF_FILE, "r") # 対象RPのIPアドレスを読み込み
    for line in data:
        line = line.replace('\n', '') # 行末の改行をとる
        makeScript(ver)
        if line[0] != '#':
            print("... updating " + line)
            doScript(line) # 更新処理
    data.close()
#    os.remove(SCRIPT_FILE)
    print("[done]")

# 実行用SQLファイル作成 ##############################
def makeScript(ver):
    with open(TEMP_FILE, encoding="utf-8") as f:
        data_lines = f.read()
    data_lines = data_lines.replace("{URL}", URL) # プレースホルダーを置き換え
    data_lines = data_lines.replace("{VERSION}", ver) # プレースホルダーを置き換え
    with open(SCRIPT_FILE, mode="w", encoding="utf-8") as f: # スクリプトファイルを書き込み
        f.write(data_lines)

# サーバー上でデータ更新スクリプトを実行する #######################
def doScript(host):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=host, username=USERNAME, password=PASSWORD)
        bash_script = open(SCRIPT_FILE).read()
        stdin, stdout, stderr = client.exec_command(bash_script)
        print(stdout.read().decode())
    finally:
        client.close()
        del client, stdin, stdout, stderr # 必須

if __name__ == "__main__":
    main()

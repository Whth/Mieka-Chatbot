import hashlib
import json
import random

import requests


class Translater:
    appid, appkey, url = None, None, None
    # configPath = f'{os.path.dirname(os.getcwd())}/baidu_translater/chat_dict.json'
    configPath='L:\pycharm projects\chatBotComponents\\baidu_translater\config.json'
    def __init__(self):
        assert self.load_secret() == 1
        print(f"Loading as \n"
              f"\tappid: {self.appid}\n"
              f"\tappkey: {self.appkey}\n"
              f"\turl: {self.url}\n"
              f"################################\n"
              f"################################\n")

    def generate_sign(self, q, salt=None):
        """
        函数 generate_sign() 是一个用于生成签名的函数，
        它接收4个参数: appid, q, salt, secret_key。

        appid: 平台分配的应用ID。

        q: 需要翻译的文本，需要使用 UTF-8 编码。

        salt: 随机数，可以使用 Python 的 random 库生成。

        secret_key: 平台分配的密钥，用于生成签名。
        """
        return_salt = False

        if salt is None:
            salt = random.randint(32768, 65536)
            return_salt = True
        sign_str = f'{self.appid}{q}{salt}{self.appkey}'
        m = hashlib.md5()
        m.update(sign_str.encode('utf-8'))
        if return_salt:
            # 入参没有salt时，返回salt
            return m.hexdigest(), salt
        else:
            return m.hexdigest()

    def load_secret(self, path: str=None):
        if path is None:
            path = self.configPath

        print(f'congfigPath: {path}')
        with open(path) as f:
            dataPack = json.load(f)
            self.appid, self.appkey, self.url = dataPack.get('appid'), dataPack.get('appkey'), dataPack.get('url')
            print('loading.....')
        return 1

    def translate(self, to_lang: str, q: str, from_lang: str = 'auto'):
        """

        :param from_lang:
        :param to_lang:
        :param q:
        :return:
        """
        try:
            assert type(to_lang) == str
            assert type(from_lang) == str
            assert type(q) == str
        except AssertionError:
            return '......'
        sign, salt = self.generate_sign(q=q)

        payload = {'appid': self.appid, 'q': q, 'from': from_lang, 'to': to_lang, 'salt': salt, 'sign': sign}

        r = requests.post(self.url, params=payload)
        result = r.json()

        # Show response
        trans_result = result.get('trans_result')[0]

        return str(trans_result.get('dst'))


if __name__ == '__main__':
    t = Translater()

    q = '你好'
    for i in range(10):

        print(t.translate(to_lang='en', q=input()))



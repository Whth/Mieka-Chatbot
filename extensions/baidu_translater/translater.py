import hashlib
import random
from typing import Dict

import requests

RESULT_KEY = "trans_result"


class Translater:
    """
    a simple baidu-based translator plugin for python
    """

    def __init__(self, appid, appkey, url):
        self.appid = appid
        self.appkey = appkey
        self.url = url
        print(
            f"Loading as \n"
            f"\tappid: {self.appid}\n"
            f"\tappkey: {self.appkey}\n"
            f"\turl: {self.url}\n"
            f"################################\n"
            f"################################\n"
        )

    def _generate_sign(self, q, salt=None):
        """
        函数 _generate_sign() 是一个用于生成签名的函数，
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
        sign_str = f"{self.appid}{q}{salt}{self.appkey}"
        m = hashlib.md5()
        m.update(sign_str.encode("utf-8"))
        if return_salt:
            # 入参没有salt时，返回salt
            return m.hexdigest(), salt
        else:
            return m.hexdigest()

    def translate(self, to_lang: str, q: str, from_lang: str = "auto"):
        """
        Translates the given text from one language to another using the API.

        Args:
            to_lang (str): The language code to translate the text into.
            q (str): The text to be translated.
            from_lang (str, optional): The language code of the text to be translated. Defaults to "auto".

        Returns:
            str: The translated text.
        """
        try:
            assert isinstance(to_lang, str)
            assert isinstance(q, str)
            assert isinstance(from_lang, str)
        except AssertionError:
            return ""
        if q == "":
            return ""
        # Generate sign and salt for the request
        sign, salt = self._generate_sign(q=q)

        payload = {
            "appid": self.appid,
            "q": q,
            "from": from_lang,
            "to": to_lang,
            "salt": salt,
            "sign": sign,
        }

        # Send POST request to the translation API
        result: Dict = requests.post(self.url, params=payload).json()

        # Get the translated text from the response
        if RESULT_KEY not in result:
            error_string = ""
            for k, v in result.items():
                error_string += f"{k}: {v}"

            return error_string
        trans_result = result.get(RESULT_KEY)[0]

        return str(trans_result.get("dst"))

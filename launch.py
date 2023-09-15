from graia.ariadne.connection.config import WebsocketClientConfig

from constant import CONFIG_FILE_NAME, CONFIG_DIR
from modules.chat_bot import ChatBot
from modules.config_utils import ConfigRegistry

WEBSOCKET_HOST = "websocket_host"

REGISTRY_PATH = "bot_name"

VERIFY_KEY = "verify_key"

ACCOUNT_ID = "account_id"
__version__ = "v0.3.1"


class Mieka(object):
    """
    Mieka chatbot
    """

    __NAME = "Mieka"
    __config = ConfigRegistry(f"{CONFIG_DIR}/{__NAME}_{CONFIG_FILE_NAME}")
    __config.register_config(ACCOUNT_ID, 1234567890)
    __config.register_config(VERIFY_KEY, "INITKEYXBVCdNG0")

    __config.register_config(WEBSOCKET_HOST, "http://127.0.0.1:8080")

    __config.load_config()
    __bot = ChatBot(
        account_id=__config.get_config(ACCOUNT_ID),
        bot_name=__NAME,
        verify_key=__config.get_config(VERIFY_KEY),
        websocket_config=WebsocketClientConfig(host=__config.get_config(WEBSOCKET_HOST)),
    )

    @classmethod
    def run(cls):
        """
        run the bot, save config on exit
        Returns:

        """
        cls.__bot.run()
        cls.__config.save_all_configs()


if __name__ == "__main__":
    bot = Mieka()
    bot.run()

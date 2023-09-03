from graia.ariadne.connection.config import WebsocketClientConfig

from modules.chat_bot import ChatBot

if __name__ == "__main__":
    bot = ChatBot(
        account_id=1801719211,
        bot_name="Mieka",
        verify_key="INITKEYXBVCdNG0",
        websocket_config=WebsocketClientConfig(host="http://127.0.0.1:8080"),
    )

    bot.run()

from typing import Dict

from modules.shared import AbstractPlugin


class SysAnal(AbstractPlugin):
    CONFIG_DETECTED_KEYWORD = "detected_keyword"

    DefaultConfig: Dict = {CONFIG_DETECTED_KEYWORD: "hello"}

    @classmethod
    def get_plugin_name(cls) -> str:
        return "TemplatePlugin"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "description test"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "None"

    def install(self):
        from graia.ariadne.message.parser.base import ContainKeyword
        from graia.ariadne.model import Group
        from graia.ariadne.event.message import GroupMessage, FriendMessage
        from graia.ariadne import Ariadne

        @self.receiver(
            [FriendMessage, GroupMessage],
            decorators=[ContainKeyword(keyword=self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD))],
        )
        async def hello(app: Ariadne, group: Group):
            await app.send_message(group, "hello")

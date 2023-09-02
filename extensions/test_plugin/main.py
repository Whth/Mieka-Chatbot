from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.base import ContainKeyword
from graia.ariadne.model import Group

from modules.plugin_base import AbstractPlugin

__all__ = ['TestPlugin']


class TestPlugin(AbstractPlugin):

    @classmethod
    def get_plugin_name(cls) -> str:
        return "test"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "test plugin"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def install(self):
        # TODO decouple this call as plugin
        from paintingBot import get_random_file
        ariadne_app = self._ariadne_app
        bord_cast = ariadne_app.broadcast

        gif_dir_path = r'N:\CloudDownloaded\01 GIF格式4700个'

        @bord_cast.receiver("GroupMessage", decorators=[ContainKeyword(keyword='mk')])
        async def random_emoji(group: Group):
            """
            random send a gif in a day
            :param group:
            :return:
            """

            await ariadne_app.send_message(group, Image(path=get_random_file(gif_dir_path)))

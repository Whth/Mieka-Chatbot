import os
from typing import List

from modules.plugin_base import AbstractPlugin

__all__ = ["PicEval"]


class PicEval(AbstractPlugin):
    CONFIG_PICTURE_ASSET_PATH = "PictureAssetPath"
    CONFIG_PICTURE_IGNORED_DIRS = "PictureIgnored"
    CONFIG_PICTURE_CACHE_DIR_PATH = "PictureCacheDirPath"
    CONFIG_STORE_DIR_PATH = "StoreDirPath"
    CONFIG_LEVEL_RESOLUTION = "LevelResolution"

    CONFIG_DETECTED_KEYWORD = "DetectedKeyword"

    CONFIG_RAND_KEYWORD = "RandKeyword"

    def _get_config_parent_dir(self) -> str:
        return os.path.abspath(os.path.dirname(__file__))

    @classmethod
    def get_plugin_name(cls) -> str:
        return "PicEval"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "send random selection of pic, let group member to evaluate the pic"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(self.CONFIG_PICTURE_ASSET_PATH, f"{self._get_config_parent_dir()}/asset")
        self._config_registry.register_config(self.CONFIG_PICTURE_IGNORED_DIRS, [])
        self._config_registry.register_config(self.CONFIG_DETECTED_KEYWORD, "eval")
        self._config_registry.register_config(self.CONFIG_RAND_KEYWORD, "ej")
        self._config_registry.register_config(self.CONFIG_STORE_DIR_PATH, f"{self._get_config_parent_dir()}/store")
        self._config_registry.register_config(self.CONFIG_LEVEL_RESOLUTION, 10)
        self._config_registry.register_config(
            self.CONFIG_PICTURE_CACHE_DIR_PATH, f"{self._get_config_parent_dir()}/cache"
        )

    def install(self):
        from graia.ariadne.message.chain import MessageChain
        from graia.ariadne.model import Group

        from graia.ariadne.message.parser.base import ContainKeyword
        from graia.ariadne.message.element import Image, MultimediaElement, Plain
        from graia.ariadne.util.cooldown import CoolDown
        from graia.ariadne.event.message import MessageEvent
        from graia.ariadne.event.message import GroupMessage
        from graia.ariadne.exception import UnknownTarget
        from modules.file_manager import download_file, compress_image_max_vol
        from .select import Selector
        from .evaluate import Evaluate

        self.__register_all_config()
        self._config_registry.load_config()
        ariadne_app = self._ariadne_app
        bord_cast = ariadne_app.broadcast

        asset_dir_path: str = self._config_registry.get_config(self.CONFIG_PICTURE_ASSET_PATH)
        ignored: List[str] = self._config_registry.get_config(self.CONFIG_PICTURE_IGNORED_DIRS)
        cache_dir_path: str = self._config_registry.get_config(self.CONFIG_PICTURE_CACHE_DIR_PATH)
        store_dir_path: str = self._config_registry.get_config(self.CONFIG_STORE_DIR_PATH)
        level_resolution: int = self._config_registry.get_config(self.CONFIG_LEVEL_RESOLUTION)
        selector: Selector = Selector(asset_dir=asset_dir_path, cache_dir=cache_dir_path, ignore_dirs=ignored)
        evaluator: Evaluate = Evaluate(store_dir_path=store_dir_path, level_resolution=level_resolution)

        @bord_cast.receiver(
            "GroupMessage",
        )
        async def eval(group: Group, message: MessageChain, event: MessageEvent):
            if not hasattr(event.quote, "origin"):
                return
            try:
                score = int(str(message.get(Plain, 1)[0]))
            except ValueError:
                return
            try:
                origin_message: GroupMessage = await ariadne_app.get_message_from_id(
                    message=event.quote.id, target=group
                )
            except UnknownTarget:
                await ariadne_app.send_group_message(group, "a, 这次不行")
                return
            origin_chain: MessageChain = origin_message.message_chain
            if Image in origin_chain:
                print("FOUND IMAGE")
                path = await download_file(origin_chain.get(Image, 1)[0].url, cache_dir_path)
            elif MultimediaElement in origin_chain:
                print("FOUND MULTIMEDIA")
                path = await download_file(origin_chain.get(MultimediaElement, 1)[0].url, cache_dir_path)
            else:
                return
            # TODO use deepdanboru to interrogate the content
            print(f"eval {score} at {path}")
            evaluator.mark(path, score)
            await ariadne_app.send_group_message(group, f"Evaluated pic as {score}")

        @bord_cast.receiver(
            "GroupMessage",
            decorators=[
                ContainKeyword(keyword=self._config_registry.get_config(self.CONFIG_RAND_KEYWORD)),
            ],
            dispatchers=[CoolDown(5)],
        )
        async def rand_picture(group: Group):
            picture = selector.random_select()
            output_path = f"{cache_dir_path}/{os.path.basename(picture)}"
            print(f"Compress to {compress_image_max_vol(picture, output_path, 6 * 1024 * 1024)}")

            await ariadne_app.send_group_message(group, Image(path=output_path))

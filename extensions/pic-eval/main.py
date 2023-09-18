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

    CONFIG_MAX_FILE_SIZE = "MaxFileSize"

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
        return "0.0.2"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(
            self.CONFIG_PICTURE_ASSET_PATH, [f"{self._get_config_parent_dir()}/asset"]
        )
        self._config_registry.register_config(self.CONFIG_PICTURE_IGNORED_DIRS, [])
        self._config_registry.register_config(self.CONFIG_DETECTED_KEYWORD, "eval")
        self._config_registry.register_config(self.CONFIG_RAND_KEYWORD, "ej")
        self._config_registry.register_config(self.CONFIG_STORE_DIR_PATH, f"{self._get_config_parent_dir()}/store")
        self._config_registry.register_config(self.CONFIG_LEVEL_RESOLUTION, 10)
        self._config_registry.register_config(
            self.CONFIG_PICTURE_CACHE_DIR_PATH, f"{self._get_config_parent_dir()}/cache"
        )
        self._config_registry.register_config(self.CONFIG_MAX_FILE_SIZE, 6 * 1024 * 1024)

    def install(self):
        from colorama import Fore
        from graia.ariadne.message.chain import MessageChain
        from graia.ariadne.model import Group
        from graia.ariadne.message.parser.base import ContainKeyword
        from graia.ariadne.message.element import Image, MultimediaElement, Plain
        from graia.ariadne.util.cooldown import CoolDown
        from graia.ariadne.event.message import GroupMessage, ActiveGroupMessage, MessageEvent
        from graia.ariadne.exception import UnknownTarget
        from modules.file_manager import download_file, compress_image_max_vol
        from .select import Selector
        from .evaluate import Evaluate
        from .img_manager import ImageRegistry

        self.__register_all_config()
        self._config_registry.load_config()
        ariadne_app = self._ariadne_app
        bord_cast = ariadne_app.broadcast
        img_registry = ImageRegistry(f"{self._get_config_parent_dir()}/images_registry.json")
        asset_dir_path: List[str] = self._config_registry.get_config(self.CONFIG_PICTURE_ASSET_PATH)
        ignored: List[str] = self._config_registry.get_config(self.CONFIG_PICTURE_IGNORED_DIRS)
        cache_dir_path: str = self._config_registry.get_config(self.CONFIG_PICTURE_CACHE_DIR_PATH)
        store_dir_path: str = self._config_registry.get_config(self.CONFIG_STORE_DIR_PATH)
        level_resolution: int = self._config_registry.get_config(self.CONFIG_LEVEL_RESOLUTION)
        selector: Selector = Selector(asset_dirs=asset_dir_path, cache_dir=cache_dir_path, ignore_dirs=ignored)
        evaluator: Evaluate = Evaluate(store_dir_path=store_dir_path, level_resolution=level_resolution)

        @bord_cast.receiver(
            "GroupMessage",
        )
        async def evaluate(group: Group, message: MessageChain, event: MessageEvent):
            """
            Asynchronous function that evaluates a message in a group chat and assigns a score to it.

            Args:
                group (Group): The group where the message is being evaluated.
                message (MessageChain): The message that is being evaluated.
                event (MessageEvent): The event associated with the message.

            Returns:
                None

            Raises:
                UnknownTarget: If the origin message cannot be found.

            Notes:
                - This function is decorated with `@bord_cast.receiver`.
                - The message is evaluated based on the score provided in the message.
                - The origin message is retrieved using the `ariadne_app.get_message_from_id` method.
                - The evaluated message can be an image or a multimedia element.
                - The evaluated message is marked with the assigned score using the `evaluator.mark` method.
                - The evaluated message and its score are sent as a group message using the `ariadne_app.send_group_message` method.
            """
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

            print(f"{Fore.GREEN}eval {score} at {path}")
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
            """
            An asynchronous function that is decorated as a receiver for the "GroupMessage" event.
            This function is triggered when a group message is received and contains a keyword
            specified in the configuration.
            It selects a random picture using the "selector"
            object, compresses the image to a specified maximum file size using the
            "compress_image_max_vol" function, and sends the compressed image to the group using
            the "ariadne_app.send_group_message" function.

            Parameters:
                group (Group): The group object representing the group where the message was
                received.

            Returns:
                None
            """
            picture = selector.random_select()

            output_path = f"{cache_dir_path}/{os.path.basename(picture)}"
            quality = compress_image_max_vol(
                picture, output_path, self._config_registry.get_config(self.CONFIG_MAX_FILE_SIZE)
            )
            print(f"Compress to {quality}")

            await ariadne_app.send_group_message(group, Image(path=output_path) + Plain(picture))

        @bord_cast.receiver(
            "ActiveGroupMessage",
        )
        async def watcher(message: ActiveGroupMessage):
            chain = message.message_chain
            if Image in chain and os.path.exists(chain.get(Plain, 1)[0].text):
                img_registry.register(message.id, str(chain))
                print(f"registered {message.id}, Current len = {len(img_registry.images_registry)}")

        @bord_cast.receiver(
            "GroupMessage",
            decorators=(
                [
                    ContainKeyword("rm"),
                ],
            ),
        )
        async def rm_picture(group: Group, message: MessageChain, event: MessageEvent):
            if not hasattr(event.quote, "origin"):
                return
            success = img_registry.remove(event.quote.id, save=True)
            await ariadne_app.send_group_message(group, f"Remove id-{event.quote.id}\nSuccess = {success}")

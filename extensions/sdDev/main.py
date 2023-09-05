import os
import re
from typing import Tuple, List, Optional, Callable

from colorama import Fore
from graia.ariadne.message.chain import MessageChain, Image
from graia.ariadne.message.parser.base import ContainKeyword
from graia.ariadne.model import Group

from modules.file_manager import download_image
from modules.plugin_base import AbstractPlugin

__all__ = ["StableDiffusionPlugin"]


class StableDiffusionPlugin(AbstractPlugin):
    __TRANSLATE_PLUGIN_NAME: str = "BaiduTranslater"
    __TRANSLATE_METHOD_NAME: str = "translate"
    __TRANSLATE_METHOD_TYPE = Callable[[str, str, str], str]  # [tolang, query, fromlang] -> str
    # TODO deal with this super high coupling

    TXT2IMG_DIRNAME = "txt2img"
    IMG2IMG_DIRNAME = "img2img"

    CONFIG_OUTPUT_DIR_PATH = "output_dir_path"
    CONFIG_IMG_TEMP_DIR_PATH = "temp"

    CONFIG_SD_HOST = "sd_host"

    CONFIG_POS_KEYWORD = "positive_keyword"
    CONFIG_NEG_KEYWORD = "negative_keyword"

    CONFIG_WILDCARD_DIR_PATH = "wildcard_dir_path"
    CONFIG_STYLES = "styles"

    # TODO this should be removed, use pos prompt keyword and neg prompt keyword
    def _get_config_parent_dir(self) -> str:
        return os.path.abspath(os.path.dirname(__file__))

    @classmethod
    def get_plugin_name(cls) -> str:
        return "stable_diffusion"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "stable diffusion plugin"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(self.CONFIG_POS_KEYWORD, "+")
        self._config_registry.register_config(self.CONFIG_NEG_KEYWORD, "-")
        self._config_registry.register_config(self.CONFIG_OUTPUT_DIR_PATH, f"{self._get_config_parent_dir()}/output")
        self._config_registry.register_config(self.CONFIG_IMG_TEMP_DIR_PATH, f"{self._get_config_parent_dir()}/temp")
        self._config_registry.register_config(self.CONFIG_SD_HOST, "http://localhost:7860")

        self._config_registry.register_config(
            self.CONFIG_WILDCARD_DIR_PATH, f"{self._get_config_parent_dir()}/asset/wildcard"
        )
        self._config_registry.register_config(self.CONFIG_STYLES, [])

    def install(self):
        self.__register_all_config()
        self._config_registry.load_config()
        translater: Optional[AbstractPlugin] = self._plugin_view.get(self.__TRANSLATE_PLUGIN_NAME, None)
        if translater:
            translate: StableDiffusionPlugin.__TRANSLATE_METHOD_TYPE = getattr(translater, self.__TRANSLATE_METHOD_NAME)
        output_dir_path = self._config_registry.get_config(self.CONFIG_OUTPUT_DIR_PATH)
        temp_dir_path = self._config_registry.get_config(self.CONFIG_IMG_TEMP_DIR_PATH)
        ariadne_app = self._ariadne_app
        bord_cast = ariadne_app.broadcast
        from dynamicprompts.wildcards import WildcardManager
        from dynamicprompts.generators import JinjaGenerator
        from .stable_diffusion import StableDiffusionApp, DiffusionParser

        SD_app = StableDiffusionApp(host_url=self._config_registry.get_config(self.CONFIG_SD_HOST))
        gen = JinjaGenerator(
            wildcard_manager=WildcardManager(path=self._config_registry.get_config(self.CONFIG_WILDCARD_DIR_PATH))
        )

        # TODO use dynamicprompts here
        # TODO add quick async response
        @bord_cast.receiver(
            "GroupMessage",
            decorators=[ContainKeyword(keyword=self._config_registry.get_config(self.CONFIG_POS_KEYWORD))],
        )
        async def group_diffusion(group: Group, message: MessageChain):
            """
            Generate an image and send it as a message in a group.

            Args:
                group (Group): The group to send the message to.
                message (MessageChain): The message chain to process.

            Returns:
                None
            """
            # Extract positive and negative prompts from the message
            pos_prompt, neg_prompt = de_assembly(str(message))

            # Translate prompts to English if translate a flag is set
            if translate:
                pos_prompt = translate("en", "".join(pos_prompt), "auto")
                neg_prompt = translate("en", "".join(neg_prompt), "auto")
            else:
                pos_prompt = "".join(pos_prompt)
                neg_prompt = "".join(neg_prompt)

            # Create a diffusion parser with the prompts
            diffusion_paser = DiffusionParser(
                prompt=pos_prompt,
                negative_prompt=neg_prompt,
                styles=self._config_registry.get_config(self.CONFIG_STYLES),
            )
            if Image in message:
                # Download the first image in the chain
                print(
                    f"{Fore.YELLOW}IMG TO IMG ORDER\n"
                    f"Downloading image from: {message[Image, 1][0].url}\n"
                    f"{Fore.MAGENTA}___________________________________________\n"
                    f"{Fore.GREEN}POSITIVE PROMPT: {pos_prompt}\n"
                    f"{Fore.MAGENTA}___________________________________________\n"
                    f"{Fore.RED}NEGATIVE PROMPT: {neg_prompt}\n"
                    f"{Fore.MAGENTA}___________________________________________\n" + Fore.RESET
                )
                img_path = download_image(save_dir=temp_dir_path, url=message[Image, 1][0].url)
                send_result = await SD_app.img2img(
                    diffusion_parameters=diffusion_paser, image_path=img_path, output_dir=output_dir_path
                )
            else:
                print(
                    f"{Fore.YELLOW}TXT TO IMG ORDER\n"
                    f"{Fore.MAGENTA}___________________________________________\n"
                    f"{Fore.GREEN}POSITIVE PROMPT: {pos_prompt}\n"
                    f"{Fore.MAGENTA}___________________________________________\n"
                    f"{Fore.RED}NEGATIVE PROMPT: {neg_prompt}\n"
                    f"{Fore.MAGENTA}___________________________________________\n" + Fore.RESET
                )
                # Generate the image using the diffusion parser
                send_result = await SD_app.txt2img(diffusion_parameters=diffusion_paser, output_dir=output_dir_path)

            # Send the image as a message in the group
            await ariadne_app.send_message(group, MessageChain("") + Image(path=send_result[0]))


def de_assembly(
    message: str, specify_batch_size: bool = False
) -> Tuple[List[str], List[str], int] | Tuple[List[str], List[str]]:
    """
    Generates the function comment for the given function body.

    Args:
        message (str): The input message.
        specify_batch_size (bool, optional): Whether to specify the batch size. Defaults to False.

    Returns:
        tuple: A tuple containing the positive prompt, negative prompt, and batch size (if specified).
    """
    if message == "":
        return [""], [""]
    # TODO seems needs a regex format checker to allow the customize split kward
    pos_pattern = r"(\+(.*?)\+)?"
    pos_prompt = re.findall(pattern=pos_pattern, string=message)
    pos_prompt = [i[1] for i in pos_prompt if i[0] != ""]

    neg_pattern = r"(\-(.*?)\-)?"
    neg_prompt = re.findall(pattern=neg_pattern, string=message)
    neg_prompt = [i[1] for i in neg_prompt if i[0] != ""]

    if specify_batch_size:
        batch_size_pattern = r"(\d+[pP])?"
        temp = re.findall(pattern=batch_size_pattern, string=message)
        batch_sizes = [int(match[0].strip(match[1])) for match in temp if match[0] != ""]
        if batch_sizes:
            return pos_prompt, neg_prompt, batch_sizes[0]
        return pos_prompt, neg_prompt, 1

    return pos_prompt, neg_prompt

import os
import re
from typing import Tuple, List, Optional, Callable, Dict, Any

from modules.file_manager import download_image
from modules.plugin_base import AbstractPlugin

__all__ = ["StableDiffusionPlugin"]


class StableDiffusionPlugin(AbstractPlugin):
    __TRANSLATE_PLUGIN_NAME: str = "BaiduTranslater"
    __TRANSLATE_METHOD_NAME: str = "translate"
    __TRANSLATE_METHOD_TYPE = Callable[[str, str, str], str]  # [tolang, query, fromlang] -> str
    # TODO deal with this super high coupling

    __CONFIG_CMD = "config"
    __CONFIG_LIST_CMD = "list"

    __CONFIG_SET_CMD = "set"

    TXT2IMG_DIRNAME = "txt2img"
    IMG2IMG_DIRNAME = "img2img"

    CONFIG_OUTPUT_DIR_PATH = "output_dir_path"
    CONFIG_IMG_TEMP_DIR_PATH = "temp"

    CONFIG_SD_HOST = "sd_host"

    CONFIG_POS_KEYWORD = "positive_keyword"
    CONFIG_NEG_KEYWORD = "negative_keyword"

    CONFIG_WILDCARD_DIR_PATH = "wildcard_dir_path"
    CONFIG_STYLES = "styles"
    CONFIG_ENABLE_HR = "enable_hr"

    CONFIG_ENABLE_TRANSLATE = "enable_translate"

    CONFIG_ENABLE_SHUFFLE_PROMPT = "enable_shuffle_prompt"
    CONFIG_ENABLE_DYNAMIC_PROMPT = "enable_dynamic_prompt"
    CONFIG_CONFIG_CLIENT_KEYWORD = "config_client_keyword"

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
        return "0.0.8"

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
        self._config_registry.register_config(self.CONFIG_ENABLE_HR, 0)
        self._config_registry.register_config(self.CONFIG_ENABLE_TRANSLATE, 0)
        self._config_registry.register_config(self.CONFIG_ENABLE_DYNAMIC_PROMPT, 1)
        self._config_registry.register_config(self.CONFIG_ENABLE_SHUFFLE_PROMPT, 0)
        self._config_registry.register_config(self.CONFIG_CONFIG_CLIENT_KEYWORD, "sd")

    def install(self):
        from graia.ariadne.message.chain import MessageChain, Image
        from graia.ariadne.message.parser.base import ContainKeyword, DetectPrefix
        from graia.ariadne.model import Group
        from dynamicprompts.wildcards import WildcardManager
        from dynamicprompts.generators import RandomPromptGenerator
        from .stable_diffusion import StableDiffusionApp, DiffusionParser

        from modules.config_utils import ConfigClient, CmdBuilder

        self.__register_all_config()
        self._config_registry.load_config()
        cmd_builder = CmdBuilder(
            config_setter=self._config_registry.set_config, config_getter=self._config_registry.get_config
        )
        configurable_options: List[str] = [
            self.CONFIG_ENABLE_HR,
            self.CONFIG_ENABLE_TRANSLATE,
            self.CONFIG_ENABLE_DYNAMIC_PROMPT,
            self.CONFIG_ENABLE_SHUFFLE_PROMPT,
        ]

        cmd_syntax_tree: Dict = {
            self._config_registry.get_config(self.CONFIG_CONFIG_CLIENT_KEYWORD): {
                self.__CONFIG_CMD: {
                    self.__CONFIG_LIST_CMD: cmd_builder.build_list_out_for(configurable_options),
                    self.__CONFIG_SET_CMD: cmd_builder.build_setter_hall(),
                }
            }
        }
        config_client = ConfigClient(cmd_syntax_tree)
        translater: Optional[AbstractPlugin] = self._plugin_view.get(self.__TRANSLATE_PLUGIN_NAME, None)
        if translater:
            translate: StableDiffusionPlugin.__TRANSLATE_METHOD_TYPE = getattr(translater, self.__TRANSLATE_METHOD_NAME)
        output_dir_path = self._config_registry.get_config(self.CONFIG_OUTPUT_DIR_PATH)
        temp_dir_path = self._config_registry.get_config(self.CONFIG_IMG_TEMP_DIR_PATH)
        ariadne_app = self._ariadne_app
        bord_cast = ariadne_app.broadcast

        SD_app = StableDiffusionApp(host_url=self._config_registry.get_config(self.CONFIG_SD_HOST))
        gen = RandomPromptGenerator(
            wildcard_manager=WildcardManager(path=self._config_registry.get_config(self.CONFIG_WILDCARD_DIR_PATH))
        )
        processor = PromptProcessorRegistry()

        def _dynamic_process(pos_prompt: str, neg_prompt: str) -> Tuple[str, str]:
            pos_interpreted = gen.generate(template=pos_prompt)
            neg_interpreted = gen.generate(template=neg_prompt)
            pos_prompt = pos_interpreted[0] if pos_interpreted else pos_prompt
            neg_prompt = neg_interpreted[0] if neg_interpreted else neg_prompt
            return pos_prompt, neg_prompt

        processor.register(
            judge=lambda: self._config_registry.get_config(self.CONFIG_ENABLE_DYNAMIC_PROMPT),
            processor=_dynamic_process,
            process_name="DYNAMIC_PROMPT_INTERPRET",
        )

        def _translate_process(pos_prompt: str, neg_prompt: str) -> Tuple[str, str]:
            pos_prompt = translate("en", pos_prompt, "auto")
            neg_prompt = translate("en", neg_prompt, "auto")
            return pos_prompt, neg_prompt

        processor.register(
            judge=lambda: self._config_registry.get_config(self.CONFIG_ENABLE_TRANSLATE) and translate,
            processor=_translate_process,
            process_name="TRANSLATE",
        )

        def _shuffle_process(pos_prompt: str, neg_prompt: str) -> Tuple[str, str]:
            from random import shuffle

            pos_tokens = pos_prompt.split(",")
            shuffle(pos_tokens)
            pos_prompt: str = ",".join(pos_tokens)
            neg_tokens = neg_prompt.split(",")
            shuffle(neg_tokens)
            neg_prompt: str = ",".join(neg_tokens)
            return pos_prompt, neg_prompt

        processor.register(
            judge=lambda: self._config_registry.get_config(self.CONFIG_ENABLE_SHUFFLE_PROMPT),
            processor=_shuffle_process,
            process_name="SHUFFLE",
        )
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

            pos_prompt, neg_prompt = processor.process("".join(pos_prompt), "".join(neg_prompt))
            # Create a diffusion parser with the prompts
            diffusion_paser = (
                DiffusionParser(
                    prompt=pos_prompt,
                    negative_prompt=neg_prompt,
                    styles=self._config_registry.get_config(self.CONFIG_STYLES),
                    enable_hr=self._config_registry.get_config(self.CONFIG_ENABLE_HR),
                )
                if pos_prompt
                else DiffusionParser(
                    styles=self._config_registry.get_config(self.CONFIG_STYLES),
                    enable_hr=self._config_registry.get_config(self.CONFIG_ENABLE_HR),
                )
            )
            if Image in message:
                # Download the first image in the chain
                print(f"Downloading image from: {message[Image, 1][0].url}\n")
                img_path = download_image(save_dir=temp_dir_path, url=message[Image, 1][0].url)
                send_result = await SD_app.img2img(
                    diffusion_parameters=diffusion_paser, image_path=img_path, output_dir=output_dir_path
                )
            else:
                # Generate the image using the diffusion parser
                send_result = await SD_app.txt2img(diffusion_parameters=diffusion_paser, output_dir=output_dir_path)

            # Send the image as a message in the group
            await ariadne_app.send_message(group, MessageChain("") + Image(path=send_result[0]))

        @bord_cast.receiver(
            "GroupMessage",
            decorators=[DetectPrefix(prefix=self._config_registry.get_config(self.CONFIG_CONFIG_CLIENT_KEYWORD))],
        )
        async def sd_client(group: Group, message: MessageChain):
            """
            Allows cli operations
            Args:
                group ():
                message ():

            Returns:

            """
            out_string = config_client.interpret(str(message))
            if isinstance(out_string, str):
                await ariadne_app.send_message(group, message=out_string)


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


class PromptProcessorRegistry(object):
    def __init__(self):
        self._registry_list: List[Tuple[Callable[[], Any], Callable[[str, str], Tuple[str, str]]]] = []
        self._process_name: List[str] = []

    def process(self, pos_prompt: str, neg_prompt: str) -> Tuple[str, str]:
        from colorama import Fore

        """
        Process the given positive and negative prompts using the registered processors.

        Args:
            pos_prompt (str): The positive prompt to be processed.
            neg_prompt (str): The negative prompt to be processed.

        Returns:
            Tuple[str, str]: A tuple containing the processed positive prompt and the processed negative prompt.
        """
        for processor, name in zip(self._registry_list, self._process_name):
            if processor[0]():
                pos_prompt, neg_prompt = processor[1](pos_prompt, neg_prompt)
                print(
                    f"\n{Fore.YELLOW}Executing {name}\n"
                    f"{self.prompt_string_constructor(pos_prompt=pos_prompt, neg_prompt=neg_prompt)}"
                )

        return pos_prompt, neg_prompt

    def register(
        self, judge: Callable[[], Any], processor: Callable[[str, str], Tuple[str, str]], process_name: str = None
    ) -> None:
        """
        Register a new judge and processor pair to the registry list.

        Args:
            judge: A callable that takes no arguments and returns any value.
            processor: A callable that takes two strings as arguments and returns a tuple of two strings.
            process_name: (optional) A string representing the process name.
                If not provided, a default process name will be generated.

        Returns:
            None
        """
        self._registry_list.append((judge, processor))
        if not process_name:
            process_name = f"Process-{len(self._registry_list)}"
        self._process_name.append(process_name)

    @staticmethod
    def prompt_string_constructor(pos_prompt: str, neg_prompt: str) -> str:
        """
        Generate a formatted string containing positive and negative prompts.

        Args:
            pos_prompt (str): The positive prompt.
            neg_prompt (str): The negative prompt.

        Returns:
            str: A formatted string containing the positive and negative prompts.
        """
        from colorama import Fore

        return (
            f"{Fore.MAGENTA}___________________________________________\n"
            f"{Fore.GREEN}POSITIVE PROMPT:\n\t{pos_prompt}\n"
            f"{Fore.RED}NEGATIVE PROMPT:\n\t{neg_prompt}\n"
            f"{Fore.MAGENTA}___________________________________________\n{Fore.RESET}"
        )

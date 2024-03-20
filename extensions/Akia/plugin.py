import hashlib
import re
from pathlib import Path
from typing import Dict, List, Set

from graia.ariadne import Ariadne
from graia.ariadne.event.lifecycle import ApplicationLaunch
from graia.ariadne.event.message import GroupMessage, FriendMessage
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.base import MatchRegex
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr

from modules.shared import AbstractPlugin, EnumCMD, get_pwd, NameSpaceNode, ExecutableNode, CmdBuilder, explore_folder
from .few_shot import FewShotsCreator, make_derived_fs_examples


class CMD(EnumCMD):
    akia = ["ak", "aki"]
    mute = ["m", "mu", "mut"]
    debug = ["d", "de", "deb"]
    config = ["c", "con", "conf"]
    list = ["l", "li", "ls", "lis"]
    set = ["s", "se", "st"]
    pmute = ["pm", "pmu", "pmut"]


class Akia(AbstractPlugin):
    CONFIG_API_HOST = "api_host"
    CONFIG_RETRIEVER_DATA_DIR = "retriever_data_dir"
    CONFIG_API_KEY = "api_key"
    CONFIG_OUTPUT_DIR = "output_dir"
    CONFIG_MUTE = "mute"
    CONFIG_FREQ_PENALTY = "freq_penalty"
    CONFIG_MAX_TOKENS = "max_tokens"
    CONFIG_PRESENCE_PENALTY = "presence_penalty"
    CONFIG_TEMPERATURE = "temperature"
    CONFIG_TOP_P = "top_p"
    CONFIG_STOP_SIGN = "stop_sign"
    CONFIG_DEBUG = "debug"
    CONFIG_TEMP_DIR = "temp_dir"
    CONFIG_PERSONAL_MUTE = "personal_mute"
    CONFIG_NO_NEWLINE = "no_newline"
    CONFIG_EXAMPLES_PATH = "examples_path"
    CONFIG_REMAIN_SEGMENT = "remain_segment"
    DefaultConfig: Dict = {
        CONFIG_TEMP_DIR: f"{get_pwd()}/temp",
        CONFIG_API_HOST: "http://localhost:8000",
        CONFIG_API_KEY: "sk-",
        CONFIG_OUTPUT_DIR: f"{get_pwd()}/output",
        CONFIG_RETRIEVER_DATA_DIR: f"{get_pwd()}/data",
        CONFIG_EXAMPLES_PATH: f"{get_pwd()}/examples.yaml",
        CONFIG_REMAIN_SEGMENT: 2,
        CONFIG_NO_NEWLINE: 1,
        CONFIG_MUTE: 0,
        CONFIG_PERSONAL_MUTE: 0,
        CONFIG_DEBUG: 0,
        CONFIG_FREQ_PENALTY: 1.0,
        CONFIG_MAX_TOKENS: 200,
        CONFIG_PRESENCE_PENALTY: 0.0,
        CONFIG_TEMPERATURE: 1.0,
        CONFIG_TOP_P: 0.3,
        CONFIG_STOP_SIGN: ["。", "！", "？", "!", "?"],
    }

    @classmethod
    def get_plugin_name(cls) -> str:
        return "Akia"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "make the bot chat like human using rwkv, releasing all the limits"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "Whth"

    def install(self):
        chat_client = ChatOpenAI(
            openai_api_key=SecretStr(self.config_registry.get_config(self.CONFIG_API_KEY)),
            openai_api_base=self.config_registry.get_config(self.CONFIG_API_HOST),
        )
        embeddings = OpenAIEmbeddings(
            openai_api_key=SecretStr(self.config_registry.get_config(self.CONFIG_API_KEY)),
            openai_api_base=self.config_registry.get_config(self.CONFIG_API_HOST),
        )

        def _sync_config():
            chat_client.max_tokens = self.config_registry.get_config(self.CONFIG_MAX_TOKENS)
            chat_client.temperature = self.config_registry.get_config(self.CONFIG_TEMPERATURE)

            chat_client.model_kwargs = {
                "frequency_penalty": self.config_registry.get_config(self.CONFIG_FREQ_PENALTY),
                "presence_penalty": self.config_registry.get_config(self.CONFIG_PRESENCE_PENALTY),
                "top_p": self.config_registry.get_config(self.CONFIG_TOP_P),
            }

        fsc = FewShotsCreator()
        fsc.load_data_file(self.config_registry.get_config(self.CONFIG_EXAMPLES_PATH))

        derived_fs_examples = make_derived_fs_examples(fsc)
        derived_fs_examples.dump_data_file(
            Path(self.config_registry.get_config(self.CONFIG_RETRIEVER_DATA_DIR)) / "derived_fs_examples.yaml"
        )

        self.__lang_chain = None

        @self.receiver(ApplicationLaunch)
        async def _make_chain() -> None:
            if self.__lang_chain:
                return

            # create a prompt template
            prompt_template = ChatPromptTemplate.from_messages(
                [
                    ("system", "接下来你作为哥哥的妹妹mieka和哥哥聊天。"),
                    ("human", "我是mieka的哥哥。"),
                    ("ai", "我是妹妹mieka哟(用手在胸前比出一个心型的手势并眨了一下眼)❤~"),
                    await derived_fs_examples.make_soft_match_few_shot_prompt(embeddings, ["input"]),
                    ("human", "{input}"),
                ]
            )

            # this retriever chain will be used to retrieve documents
            # that will be fed to the chat chain to generate a accurate response.
            self.__lang_chain = prompt_template | chat_client | StrOutputParser()
            print("Loaded chain")

        async def ainvoke(
            client: Runnable,
            message: str,
            stop_at: List[str],
        ) -> str:
            # 调用客户端的ainvoke方法，并等待返回结果
            ans: str = await client.ainvoke(input={"input": message})

            # 根据配置决定是否移除返回结果中的换行符
            ans = ans.replace("\n", "") if self.config_registry.get_config(self.CONFIG_NO_NEWLINE) else ans

            # 如果处于调试模式，直接返回处理后的结果
            if self.config_registry.get_config(self.CONFIG_DEBUG):
                return ans

            # 根据冒号切割
            messed_extraction: List[str] = split_messed_message(ans)
            if len(messed_extraction) > 1:
                return messed_extraction[0]

            # 根据stop_at列表分割答案字符串，并根据配置决定返回多少分割后的段落
            spl_sentences = self._split_sentences(ans, stop_at)
            if len(spl_sentences) > self.config_registry.get_config(self.CONFIG_REMAIN_SEGMENT):
                # 如果分割后的段落超过配置的最大值，打印信息并返回指定数量的段落
                print(f"Split sentences, take {len(spl_sentences)} segments.")
                return "".join(spl_sentences[: self.config_registry.get_config(self.CONFIG_REMAIN_SEGMENT)])
            else:
                # 如果分割后的段落不超过最大值，直接返回所有段落
                return "".join(spl_sentences)

        @self.receiver(
            GroupMessage,
            decorators=[
                MatchRegex(".*?(?i:Mieka).*", full=False),
            ],
        )
        async def group_talk(app: Ariadne, message_event: GroupMessage):
            """
            An asynchronous function that processes group messages.
            Accepts an instance of the Ariadne application and a GroupMessage event as parameters.
            Returns None.
            """

            message = message_event.message_chain
            message_plain = message.get(Plain)
            message_string = "".join(map(str, message_plain))
            print(f"Receive request from {message_event.sender.id}")
            if self.config_registry.get_config(self.CONFIG_MUTE):
                return
            _sync_config()
            print(f"Mute[OFF],Receive:\n {str(message)}")

            ret_message = await ainvoke(
                self.__lang_chain,
                message_string,
                self.config_registry.get_config(self.CONFIG_STOP_SIGN),
            )

            await app.send_message(message_event, ret_message)

        @self.receiver(
            FriendMessage,
        )
        async def personal_talk(app: Ariadne, message_event: FriendMessage):
            """
            A coroutine function to handle personal talk messages from friends.

            Args:
                app (Ariadne): The Ariadne application instance.
                message_event (FriendMessage): The message event from a friend.

            Returns:
                None
            """

            message = message_event.message_chain
            message_plain = message.get(Plain)
            message_string = "".join(map(str, message_plain))
            print(f"Receive request from {message_event.sender.id}")
            if self.config_registry.get_config(self.CONFIG_MUTE) or self.config_registry.get_config(
                self.CONFIG_PERSONAL_MUTE
            ):
                return

            print(f"Mute[OFF],Receive:\n {str(message)}")
            _sync_config()
            ret_message = await ainvoke(
                self.__lang_chain,
                message_string,
                self.config_registry.get_config(self.CONFIG_STOP_SIGN),
            )

            await app.send_message(message_event, ret_message)

        list_configs: Set[str] = {
            self.CONFIG_MUTE,
            self.CONFIG_PERSONAL_MUTE,
            self.CONFIG_DEBUG,
            self.CONFIG_NO_NEWLINE,
            self.CONFIG_FREQ_PENALTY,
            self.CONFIG_MAX_TOKENS,
            self.CONFIG_PRESENCE_PENALTY,
            self.CONFIG_TEMPERATURE,
            self.CONFIG_TOP_P,
            self.CONFIG_STOP_SIGN,
            self.CONFIG_REMAIN_SEGMENT,
        }
        cmd_builder = CmdBuilder(self.config_registry.get_config, self.config_registry.set_config)
        tree = NameSpaceNode(
            **CMD.akia.export(),
            required_permissions=self.required_permission,
            children_node=[
                NameSpaceNode(
                    **CMD.config.export(),
                    children_node=[
                        ExecutableNode(**CMD.list.export(), source=cmd_builder.build_list_out_for(list_configs)),
                        ExecutableNode(**CMD.set.export(), source=cmd_builder.build_group_setter_for(list_configs)),
                    ],
                ),
                ExecutableNode(
                    **CMD.mute.export(),
                    source=cmd_builder.build_setter_for(self.CONFIG_MUTE),
                ),
                ExecutableNode(
                    **CMD.debug.export(),
                    source=cmd_builder.build_setter_for(self.CONFIG_DEBUG),
                ),
                ExecutableNode(**CMD.pmute.export(), source=cmd_builder.build_setter_for(self.CONFIG_PERSONAL_MUTE)),
            ],
        )

        self.root_namespace_node.add_node(tree)

    def _load_documents(self) -> List[Document]:
        data_dir = Path(self.config_registry.get_config(self.CONFIG_RETRIEVER_DATA_DIR))
        data_dir.mkdir(parents=True, exist_ok=True)

        files_with_extension: List[str] = explore_folder(str(data_dir))
        print(f"Load {len(files_with_extension)} files from {data_dir}")
        loaders: List[UnstructuredFileLoader] = [
            UnstructuredFileLoader(
                file_path=file,
                mode="single",
            )
            for file in files_with_extension
        ]
        loaded_docs: List[Document] = []
        for l in loaders:
            loaded_docs.extend(l.load())
        return loaded_docs

    def _split_sentences(self, string: str, stop_at: List[str]) -> List[str]:
        """
        Splits a string into sentences based on the provided stop characters.

        Parameters:
            string (str): The input string to split into sentences.
            stop_at (List[str]): A list of characters to stop at when splitting.

        Returns:
            List[str]: A list of sentences split from the input string.
        """
        # in fo no stop sign in the string

        if all(x not in string for x in stop_at):
            return [string]
        parts = "".join(stop_at)

        regex = f"([{parts}])"

        reg_spl = re.split(regex, string)

        new_sents = []
        for i in range(0, len(reg_spl) - 1, 2):
            sent = reg_spl[i] + reg_spl[i + 1]
            new_sents.append(sent)

        return new_sents


def check_file_unchanged(file_path: str) -> bool:
    """
    Check the hash of the given file and compare it with the file's stem.

    :param file_path: The path of the file to check.
    :type file_path: str
    :return: True if the hash matches the file's stem, False otherwise.
    :rtype: bool
    """
    file_path = Path(file_path)
    with open(file_path, "rb") as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    return file_hash == file_path.stem


def sync_hash_to_stem(file_path: str) -> str:
    """
    rename the file according to its md5 hash and return the new path
    Args:
        file_path:

    Returns:

    """
    file_path = Path(file_path)
    with open(file_path, "rb") as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    new_path = file_path.parent / (file_hash + file_path.suffix)
    file_path.rename(new_path)
    return str(new_path)


def check_and_sync_hash(dir_path: str) -> List[str]:
    """

    Args:
        dir_path:

    Returns:

    """
    files = explore_folder(dir_path)
    updated_files = [f for f in files if not check_file_unchanged(f)]

    sync_files = [sync_hash_to_stem(f) for f in updated_files]

    return sync_files


def split_messed_message(message: str) -> List[str]:
    """
    Especially designed to deal with the extraction from string like "who are you?AI:hello",
     which should be "who are you?"

    A function that takes a message and extracts the initial part of the message before the occurrence of specific punctuation characters.
    The function takes a single parameter `message` of type str and returns a string.
    Args:
        message:

    Returns:

    """
    message = message.replace("\n", "")
    spl = [".", "。", "！", "？", "!", "?", ")", "~", "❤"]
    if all(map(lambda x: x not in message, spl)):
        return [message]
    spl_parts = "".join(spl)

    pat_string = f"(?:[{spl_parts}])([^:：{spl_parts}]+[:：])"
    print(pat_string)
    pat = re.compile(pat_string)
    match = pat.findall(message)
    print(match)
    if match:
        return message.split(match[0])
    else:
        return [message]

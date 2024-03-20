import hashlib
import re
import time
from pathlib import Path
from typing import Dict, List, Any, Set

from graia.ariadne import Ariadne
from graia.ariadne.event.lifecycle import ApplicationLaunch
from graia.ariadne.event.message import GroupMessage, FriendMessage
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.base import MatchRegex
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_community.vectorstores.faiss import FAISS
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr

from modules.shared import AbstractPlugin, EnumCMD, get_pwd, NameSpaceNode, ExecutableNode, CmdBuilder, explore_folder


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
    DefaultConfig: Dict = {
        CONFIG_TEMP_DIR: f"{get_pwd()}/temp",
        CONFIG_API_HOST: "http://localhost:8000",
        CONFIG_API_KEY: "sk-",
        CONFIG_OUTPUT_DIR: f"{get_pwd()}/output",
        CONFIG_RETRIEVER_DATA_DIR: f"{get_pwd()}/data",
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

        def _sync_config():
            chat_client.max_tokens = self.config_registry.get_config(self.CONFIG_MAX_TOKENS)
            chat_client.temperature = self.config_registry.get_config(self.CONFIG_TEMPERATURE)

            chat_client.model_kwargs = {
                "frequency_penalty": self.config_registry.get_config(self.CONFIG_FREQ_PENALTY),
                "presence_penalty": self.config_registry.get_config(self.CONFIG_PRESENCE_PENALTY),
                "top_p": self.config_registry.get_config(self.CONFIG_TOP_P),
            }

        # create a prompt template
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("human", "{context}"),
                ("human", "你是谁呀?"),
                ("ai", "我是你最喜欢的妹妹mieka哟(用手在巨乳上比出一个心型的手势)❤~"),
                ("human", "{input}"),
            ]
        )
        document_chain = create_stuff_documents_chain(chat_client, prompt_template)

        def _make_mini_chain():
            from .presets import MESU_GAKI

            print("Making mini chain")
            mini_chain = ChatPromptTemplate.from_messages(MESU_GAKI) | chat_client | StrOutputParser()
            return mini_chain

        self.__lang_chain = None

        @self.receiver(ApplicationLaunch)
        async def _make_chain() -> None:
            if self.__lang_chain:
                return

            documents = self._load_documents()

            doc_len = list(map(lambda x: len(x.page_content), documents))
            print(f"Loaded {len(documents)} documents from retriever data dir")
            print(f"Average document length: {sum(doc_len) / len(documents)}")
            print(f"Mean sqrt deviation: {sum(map(lambda x: x ** 2, doc_len)) ** 0.5 / len(doc_len)}")

            embeddings = OpenAIEmbeddings(
                openai_api_key=SecretStr(self.config_registry.get_config(self.CONFIG_API_KEY)),
                openai_api_base=self.config_registry.get_config(self.CONFIG_API_HOST),
            )
            print("Loaded embeddings")
            now = time.time()
            # use this embedding model to ingest documents into a vectorstore
            vector: FAISS = await FAISS.afrom_documents(documents, embeddings)

            print(f"Loaded vectorstore, time used: {time.time()-now:.2f}")
            retriever: VectorStoreRetriever = vector.as_retriever()
            print("Loaded retriever")

            # this retriever chain will be used to retrieve documents
            # that will be fed to the chat chain to generate a accurate response.
            self.__lang_chain = create_retrieval_chain(retriever, document_chain)
            print("Loaded chain")

        async def ainvoke(
            client: Runnable,
            message: str,
            stop_at: List[str],
        ) -> str:
            """
            异步读取流式数据，直到遇到指定的停止字符。

            :param client: RunnableSerializable类型的客户端，支持异步流式数据读取。
            :param message: 用于初始化流式数据读取的输入消息。
            :param stop_at: 一个字符串列表，标识应该停止读取数据的字符。

            :return: 从流中读取的字符串。
            """

            astream_it: Dict[str, Any] = await client.ainvoke(input={"input": message})
            if isinstance(astream_it, str):
                ans = astream_it
            elif isinstance(astream_it, dict):
                used_doc = astream_it.get("context")

                print(f"Used doc: {used_doc}")
                ans = astream_it.get("answer")
            else:
                raise Exception(f"Unknown type,{type(astream_it)}")
            if self.config_registry.get_config(self.CONFIG_DEBUG):
                return ans
            spl_sentences = self._split_sentences(ans, stop_at)
            if len(spl_sentences) > 3:
                return "".join(spl_sentences[:3])
            else:
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
                self.__lang_chain or _make_mini_chain(),
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
                self.__lang_chain or _make_mini_chain(),
                message_string,
                self.config_registry.get_config(self.CONFIG_STOP_SIGN),
            )

            await app.send_message(message_event, ret_message)

        list_configs: Set[str] = {
            self.CONFIG_MUTE,
            self.CONFIG_PERSONAL_MUTE,
            self.CONFIG_DEBUG,
            self.CONFIG_FREQ_PENALTY,
            self.CONFIG_MAX_TOKENS,
            self.CONFIG_PRESENCE_PENALTY,
            self.CONFIG_TEMPERATURE,
            self.CONFIG_TOP_P,
            self.CONFIG_STOP_SIGN,
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
        # in fo no stop sign in the string
        if all(map(lambda x: x not in string, stop_at)):
            return [string]
        messed_extraction: List[str] = split_messed_message(string)
        if len(messed_extraction) > 1:
            return messed_extraction
        parts = "".join(stop_at)

        regex = f"([{parts}])"

        reg_spl = re.split(regex, string)

        new_sents = []
        for i in range(0, len(reg_spl) - 1, 2):
            sent = reg_spl[i] + reg_spl[i + 1]
            new_sents.append(sent)
        new_sents = list(filter(lambda x: x != "\n", new_sents))
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

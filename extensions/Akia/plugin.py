import re
from pathlib import Path
from typing import Dict, List, Any

from graia.ariadne import Ariadne
from graia.ariadne.event.lifecycle import ApplicationLaunch
from graia.ariadne.event.message import GroupMessage, FriendMessage
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.base import MatchRegex
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_community.vectorstores.faiss import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import SpacyTextSplitter
from pydantic import SecretStr

from modules.shared import AbstractPlugin, EnumCMD, get_pwd, NameSpaceNode, ExecutableNode, CmdBuilder, explore_folder


class CMD(EnumCMD):
    akia = ["ak", "aki"]
    mute = ["m", "mu", "mut"]
    debug = ["d", "de", "deb"]
    config = ["c", "con", "conf"]
    list = ["l", "li", "ls", "lis"]
    set = ["s", "se", "st"]


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
    DefaultConfig: Dict = {
        CONFIG_API_HOST: "http://localhost:8000",
        CONFIG_API_KEY: "sk-",
        CONFIG_OUTPUT_DIR: f"{get_pwd()}/output",
        CONFIG_RETRIEVER_DATA_DIR: f"{get_pwd()}/data",
        CONFIG_MUTE: 0,
        CONFIG_DEBUG: 0,
        CONFIG_FREQ_PENALTY: 1.0,
        CONFIG_MAX_TOKENS: 200,
        CONFIG_PRESENCE_PENALTY: 0.0,
        CONFIG_TEMPERATURE: 1.0,
        CONFIG_TOP_P: 0.3,
        CONFIG_STOP_SIGN: ["\n", "。", "！", "？", "!", "?"],
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

        _sync_config()
        # create a prompt template
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "告诉你一个故事:{context}"),
                ("system", "你的名字是Mieka,你是哥哥的妹妹."),
                ("ai", "我是Mieka,我是哥哥的妹妹❤。"),
                ("human", "{input}"),
            ]
        )
        document_chain = create_stuff_documents_chain(chat_client, prompt_template)

        loader = self._make_retriever_loader()

        self.__lang_chain = None

        @self.receiver(ApplicationLaunch)
        async def _make_chain() -> None:
            docs = loader.load()
            text_splitter = SpacyTextSplitter(separator="\n", pipeline="zh_core_web_lg")
            documents = text_splitter.split_documents(docs)
            doc_len = list(map(lambda x: len(x.page_content), documents))
            print(f"Loaded {len(documents)} documents from retriever data dir")
            print(f"Average document length: {sum(doc_len) / len(documents)}")
            print(f"Mean sqrt deviation: {sum(map(lambda x: x ** 2, doc_len)) ** 0.5 / len(doc_len)}")

            embeddings = OpenAIEmbeddings(
                openai_api_key=SecretStr(self.config_registry.get_config(self.CONFIG_API_KEY)),
                openai_api_base=self.config_registry.get_config(self.CONFIG_API_HOST),
            )
            # use this embedding model to ingest documents into a vectorstore
            vector = FAISS.from_documents(documents, embeddings)
            retriever: VectorStoreRetriever = vector.as_retriever()

            # First we need a prompt that we can pass into an LLM to generate this search query

            # this retriever chain will be used to retrieve documents
            # that will be fed to the chat chain to generate a accurate response.
            self.__lang_chain = create_retrieval_chain(retriever, document_chain)

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

            ans = astream_it.get("answer")
            if self.config_registry.get_config(self.CONFIG_DEBUG):
                return ans
            return self._split_sentences(ans, stop_at)[0]

        @self.receiver(
            [FriendMessage, GroupMessage],
            decorators=[
                MatchRegex(".*?(?i:Mieka).*", full=False),
            ],
        )
        async def _talk(app: Ariadne, message_event: FriendMessage | GroupMessage):
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

        list_configs = {
            self.CONFIG_MUTE,
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
            ],
        )

        self.root_namespace_node.add_node(tree)

    def _make_retriever_loader(self) -> UnstructuredFileLoader:
        data_dir = Path(self.config_registry.get_config(self.CONFIG_RETRIEVER_DATA_DIR))
        data_dir.mkdir(parents=True, exist_ok=True)

        files_with_extension: List[str] = explore_folder(str(data_dir))
        print(f"Load {len(files_with_extension)} files from {data_dir}")
        retriever = UnstructuredFileLoader(
            file_path=files_with_extension,
            mode="single",
        )
        return retriever

    def _split_sentences(self, string: str, stop_at: List[str]) -> List[str]:
        # in fo no stop sign in the string
        if all(map(lambda x: x not in string, stop_at)):
            return [string]
        parts = "".join(stop_at)

        regex = f"([{parts}])"

        reg_spl = re.split(regex, string)

        new_sents = []
        for i in range(0, len(reg_spl) - 1, 2):
            sent = reg_spl[i] + reg_spl[i + 1]
            new_sents.append(sent)
        new_sents = list(filter(lambda x: x != "\n", new_sents))
        return new_sents

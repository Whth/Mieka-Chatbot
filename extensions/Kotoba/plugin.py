from random import choice, randint
from typing import Dict

import jieba
from graia.ariadne.event.message import GroupMessage, FriendMessage, ActiveGroupMessage, ActiveFriendMessage
from graia.ariadne.message.element import Image
from wordcloud import WordCloud

from modules.shared import AbstractPlugin, get_pwd, NameSpaceNode, ExecutableNode, make_stdout_seq_string
from .recorder import MessageRecorder


class CMD:
    ROOT: str = "kotoba"

    LIST: str = "list"
    DEL: str = "del"
    MAKE: str = "c"
    CLEAN: str = "clear"
    HOT: str = "hot"


class Kotoba(AbstractPlugin):
    CONFIG_DATA_FILE = "data_file"
    CONFIG_CACHE_FILE = "cache_file"
    CONFIG_FONT = "font"
    CONFIG_BLACKLIST = "blacklist"
    DefaultConfig: Dict = {
        CONFIG_DATA_FILE: f"{get_pwd()}/kotoba.json",
        CONFIG_CACHE_FILE: f"{get_pwd()}/kotoba.png",
        CONFIG_FONT: f"{get_pwd()}/得意黑 TTF.ttf",
        CONFIG_BLACKLIST: [
            "我",
            "你",
            "他",
            "她",
            "它",
            "它们",
            "他们",
            "她们",
            "你们",
            "我们",
            "的",
            "地",
            "得",
            "了",
            "着",
            "过",
            "和",
            "与",
            "跟",
            "或",
            "或者",
            "而",
            "而且",
            "之",
            "其",
            "也",
            "还",
            "又",
            "就",
            "便",
            "虽",
            "尽管",
            "但",
            "然而",
            "所",
            "所以",
            "若",
            "如果",
            "因",
            "由于",
            "为",
            "为了",
            "用",
            "以",
            "在",
            "于",
            "由",
            "自",
            "向",
            "往",
            "对",
            "对于",
            "与",
            "同",
            "及",
            "以及",
            "将",
            "把",
            "被",
            "受",
            "比",
            "较",
            "从",
            "自从",
            "到",
            "至",
            "除",
            "除了",
            "各",
            "每",
            "某",
            "某个",
            "几",
            "多少",
            ".",
            "!",
            "?",
            ";",
            ":",
            '"',
            "'",
            "‘",
            "’",
            "[",
            "]",
            "<",
            ">",
            "(",
            ")",
            "—",
            ",",
            "...",
            "/",
            "、",
            "。",
            "！",
            "？",
            "；",
            ":",
            "“",
            "”",
            "‘",
            "’",
            "【",
            "】",
            "《",
            "》",
            "（",
            "）",
            "——",
            "、",
            "@",
            "#",
        ],
    }

    @classmethod
    def get_plugin_name(cls) -> str:
        return "Kotoba"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "kotoba that provides message persistent service and word cloud generation service"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "Whth"

    def install(self):
        recorder = MessageRecorder(save_file_path=self.config_registry.get_config(self.CONFIG_DATA_FILE))

        generator: WordCloud = WordCloud(
            width=800,
            height=400,
            background_color="white",
            font_path=self.config_registry.get_config(self.CONFIG_FONT),
            max_words=10000,
        )

        self.receiver([GroupMessage, FriendMessage, ActiveFriendMessage, ActiveGroupMessage])(
            recorder.make_listener(dense_save=True)
        )

        def _list_recorder_data(index: int = None, message_count: int = 5) -> str:
            """
            Retrieves a list of recorder data.

            Args:
                index (int, optional): The index of the data to retrieve. Defaults to None.
                message_count (int, optional): The number of messages to retrieve. Defaults to 5.

            Returns:
                str: The retrieved recorder data as a string.
            """
            if isinstance(index, int):
                key = list(recorder.data_base.container.keys())[index]

                return f"{key}:\n" + make_stdout_seq_string(
                    recorder.data_base.container.get(key)[-message_count:], sort=False
                )
            else:
                temp = [f"{k}<=RecordedSize:{len(v)}" for k, v in recorder.data_base.container.items()]
                return make_stdout_seq_string(temp, sort=False)

        def _make_wordcloud(index: int = None) -> Image:
            """
            Generates a word cloud image based on the text data stored in the `recorder.data_base.container`.

            Args:
                index (int, optional): The index of the key in the `recorder.data_base.container` dictionary.
                    If provided, the word cloud will be generated based on the text data associated with that key.
                    If not provided, the word cloud will be generated based on all the text data in the dictionary.
                    Defaults to None.

            Returns:
                Image: The generated word cloud image.

            Note:
                - The text data is processed by removing newline characters and replacing them with spaces.
                - The word cloud is generated using the `jieba` library for Chinese word segmentation.
                - Words with a frequency less than 3 are excluded from the word cloud.
                - The font size of each word in the word cloud is proportional to its frequency, multiplied by a scaling factor of 10.
                - The word cloud image is saved to a file specified by the `self.config_registry.get_config(self.CONFIG_CACHE_FILE)` method.

            """

            # Combine the text data based on the provided index or all text data if index is not provided

            if isinstance(index, int):
                key = list(recorder.data_base.container.keys())[index]
                print(f"Generating word cloud for {key}")
                temp_string = " ".join(recorder.data_base.container.get(key))
            else:
                temp_string = " ".join([" ".join(v) for v in recorder.data_base.container.values()])

            # Perform Chinese word segmentation and count word frequencies
            cut_list = jieba.cut(temp_string.replace("\n", " "), cut_all=False)
            word_freq = {}
            for word in cut_list:
                if word not in word_freq:
                    word_freq[word] = 0
                word_freq[word] += 1

            # Exclude words with frequency less than 3 and generate font sizes based on word frequencies
            font_sizes = {}
            black_list = set(self.config_registry.get_config(self.CONFIG_BLACKLIST))
            for word, freq in word_freq.items():
                if word in black_list or freq < 3:
                    continue
                font_sizes[word] = freq * 10

            # Generate the word cloud image and save it to a file
            cachefile_path = self.config_registry.get_config(self.CONFIG_CACHE_FILE)
            generator.generate_from_frequencies(font_sizes).to_file(cachefile_path)

            # Return the generated word cloud image
            return Image(path=cachefile_path)

        def _clean():
            """
            Cleans the database container by removing all items and saves the changes.

            Returns:
                str: A message indicating the number of items that were cleaned.
            """
            sizes = list(map(len, recorder.data_base.container.values()))
            print(sizes)

            recorder.data_base.container.clear()
            recorder.save()
            return f"Cleaned {sum(sizes)} items"

        def _delete(index: int):
            """
            Deletes an element from the database at the specified index.

            Args:
                index (int): The index of the element to delete.

            Returns:
                None
            """
            key = list(recorder.data_base.container.keys())[index]
            recorder.del_data(key)

        def _hot(sentence: str):
            """
            Generates a list of tokens from a given sentence by performing tokenization using jieba.cut.

            Args:
                sentence (str): The input sentence to tokenize.

            Returns:
                str: The concatenation of tokens generated from the sentence.
            """
            if not sentence:
                return

            hot_words = ["😍", "🥵", "🥰", "🤤", "...", "...", "..."]
            tokens = list(jieba.cut(sentence))
            for hot_w in [choice(hot_words) for _ in range(int(len(tokens) / 2.2))]:
                tokens.insert(randint(0, len(tokens) - 1), hot_w)
            return "".join(tokens)

        tree = NameSpaceNode(
            name=CMD.ROOT,
            help_message=self.get_plugin_description(),
            required_permissions=self.required_permission,
            children_node=[
                ExecutableNode(name=CMD.LIST, help_message=_list_recorder_data.__doc__, source=_list_recorder_data),
                ExecutableNode(name=CMD.MAKE, help_message=_make_wordcloud.__doc__, source=_make_wordcloud),
                ExecutableNode(name=CMD.CLEAN, help_message=_clean.__doc__, source=_clean),
                ExecutableNode(name=CMD.DEL, help_message=_delete.__doc__, source=_delete),
                ExecutableNode(name=CMD.HOT, help_message=_hot.__doc__, source=_hot),
            ],
        )

        self.root_namespace_node.add_node(tree)

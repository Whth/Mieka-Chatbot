import re
from pathlib import Path
from typing import List, Dict, Type, Iterator, Tuple

import yaml
from langchain_community.vectorstores.faiss import FAISS
from langchain_core.embeddings import Embeddings
from langchain_core.example_selectors import MaxMarginalRelevanceExampleSelector, BaseExampleSelector
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotPromptWithTemplates,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate,
    FewShotChatMessagePromptTemplate,
)
from langchain_core.vectorstores import VectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI


class FewShotsCreator:
    def __init__(self, input_key: str = "fs_input", output_key: str = "fs_output"):
        self._data_obj: List[Dict[str, str]] = []
        self._input_key: str = input_key
        self._output_key: str = output_key

    @property
    def input_key(self) -> str:
        return self._input_key

    @property
    def output_key(self) -> str:
        return self._output_key

    def load_data_file(self, file_path: Path | str, merge_load: bool = False):
        """
        Load data from a file into the class, optionally merging with existing data.

        Parameters:
            file_path (Path|str): The path to the file to load data from.
            merge_load (bool): Whether to merge the loaded data with existing data. Default is False.
        """
        file_path = Path(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            data_obj = yaml.safe_load(f)
            if not self.validate_data_obj(data_obj):
                raise ValueError("The data object is not valid.")
            if merge_load:
                self._data_obj.extend(data_obj)
            else:
                self._data_obj = data_obj
        print(f"Loaded {len(self._data_obj)} examples from {file_path}")

    def dump_data_file(self, file_path: Path | str):
        """
        A function to dump the data object into a specified file path using YAML format.

        Parameters:
        file_path (Path|str): The file path where the data will be dumped.

        Returns:
        None
        """

        file_path = Path(file_path)
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(self._data_obj, f, allow_unicode=True)

    def validate_data_obj(self, data_obj: List[Dict[str, str]]) -> bool:
        """
        Validate the data object.

        Args:
            data_obj (List[Dict[str, str]]): The data object to be validated.

        Returns:
            bool: True if the data object is valid, False otherwise.
        """
        if not isinstance(data_obj, list):
            return False
        for item in data_obj:
            if not isinstance(item, dict):
                return False
            if self._input_key not in item or self._output_key not in item:
                return False
        return True

    def add_example(self, example: Dict[str, str]):
        if not self.validate_data_obj([example]):
            raise ValueError("The data object is not valid.")
        self._data_obj.append(example)

    def create_hard_match_few_shot_prompt(self) -> FewShotChatMessagePromptTemplate:
        """
        Create a few-shot prompt from the loaded data.

        Args:

        Returns:
            FewShotPromptWithTemplates: A few-shot prompt with templates.
        """
        few_shot_prompt = FewShotChatMessagePromptTemplate(
            examples=self._data_obj,
            example_prompt=self.make_fs_prompt_template(),
        )

        return few_shot_prompt

    async def make_soft_match_few_shot_prompt(
        self, embeddings: Embeddings, input_vars: List[str], k: int = 2, vectorstore_cls: Type[VectorStore] = FAISS
    ) -> FewShotChatMessagePromptTemplate:
        """
        Creates a soft match few shot prompt for generating chat messages.

        Args:
            embeddings (Embeddings): The embeddings used to measure semantic similarity.
            input_vars (List[str]): The list of input variables.
            k (int, optional): The number of examples to produce. Defaults to 1.
            vectorstore_cls (Type[VectorStore], optional): The VectorStore class used to store the embeddings and do a similarity search. Defaults to FAISS.

        Returns:
            FewShotChatMessagePromptTemplate: The created few shot chat message prompt.
        """
        example_selector = await MaxMarginalRelevanceExampleSelector.afrom_examples(
            # This is the list of examples available to select from.
            self._data_obj,
            # This is the embedding class used to produce embeddings which are used to measure semantic similarity.
            embeddings=embeddings,
            # This is the VectorStore class that is used to store the embeddings and do a similarity search over.
            vectorstore_cls=vectorstore_cls,
            # This is the number of examples to produce.
            k=k,
            input_keys=input_vars,
        )

        prompt = FewShotChatMessagePromptTemplate(
            example_selector=example_selector,
            example_prompt=(
                HumanMessagePromptTemplate.from_template(f"{{{self._input_key}}}")
                + AIMessagePromptTemplate.from_template(f"{{{self._output_key}}}")
            ),
            input_variables=input_vars,
        )

        return prompt

    def make_example(self, input_val: str, output_val: str) -> Dict[str, str]:
        """
        A function that creates a dictionary with input and output strings.

        Parameters:
            input_val (str): The input string to be stored in the dictionary.
            output_val (str): The output string to be stored in the dictionary.

        Returns:
            Dict[str, str]: A dictionary containing the input and output strings.
        """
        return {self._input_key: input_val, self._output_key: output_val}

    def make_fs_prompt_template(self) -> ChatPromptTemplate:
        """
        A function that generates a ChatPromptTemplate using input and output keys.

        Parameters:
            self: The object instance.

        Returns:
            ChatPromptTemplate: The generated ChatPromptTemplate.
        """

        return ChatPromptTemplate.from_messages(
            [("human", f"{{{self._input_key}}}"), ("ai", f"{{{self._output_key}}}")]
        )

    def inject_examples_data(self, fs_template: FewShotChatMessagePromptTemplate):
        """
        A description of the entire function, its parameters, and its return types.
        """
        selector: BaseExampleSelector = fs_template.example_selector

        for example in self._data_obj:
            selector.add_example(example)

    def iter(self) -> Iterator[Tuple[str, str]]:
        for example in self._data_obj:
            yield example[self._input_key], example[self._output_key]


def remove_bracketed_content(string: str) -> str:
    """
    Remove the bracketed content from a string.

    Parameters:
        string (str): The string to remove the brackets from.

    Returns:
        str: The string with the brackets removed.
    """
    return re.sub(r"\([^)]*\)", "", string)


def make_derived_fs_examples(fs_creator: FewShotsCreator) -> FewShotsCreator:
    """

    Args:
        fs_creator:

    Returns:

    """
    ret = FewShotsCreator(input_key=fs_creator.input_key, output_key=fs_creator.output_key)

    for input_val, output_val in fs_creator.iter():
        input_set = {input_val}
        output_set = {output_val}
        input_set.add(remove_bracketed_content(input_val))
        output_set.add(remove_bracketed_content(output_val))
        for inp in input_set:
            for oup in output_set:
                ret.add_example(fs_creator.make_example(inp, oup))

    return ret


def merge_fs_creator(fscs: List[FewShotsCreator]) -> FewShotsCreator:
    """
    A function that merges a list of FewShotsCreator objects into a single FewShotsCreator object if all input and output keys are the same.

    Parameters:
    - fscs: List of FewShotsCreator objects to be merged.

    Returns:
    - Merged FewShotsCreator object.
    """
    # check all the input and output keys are the same
    if not all((fsc.input_key == fscs[0].input_key and fsc.output_key == fscs[0].output_key) for fsc in fscs):
        raise ValueError("The input and output keys are not the same.")
    ret_fsc = FewShotsCreator(input_key=fscs[0].input_key, output_key=fscs[0].output_key)
    for fsc_to_merge in fscs:
        for input_val, output_val in fsc_to_merge.iter():
            ret_fsc.add_example(ret_fsc.make_example(input_val, output_val))
    return ret_fsc


if __name__ == "__main__":
    fs_creator = FewShotsCreator()
    fs_creator.load_data_file("examples.yaml")
    pack = {"openai_api_key": "sk-", "openai_api_base": "http://192.168.0.198:8000"}
    embeddings = OpenAIEmbeddings(**pack)
    llm = ChatOpenAI(**pack, max_tokens=200)
    fst = fs_creator.make_soft_match_few_shot_prompt(embeddings, input_vars=["input"])
    final_prompt = (
        AIMessagePromptTemplate.from_template("妹妹mieka登场啦❤❤~~")
        + fst
        + HumanMessagePromptTemplate.from_template("{input}")
    )

    chain = final_prompt | llm

    print(chain.invoke({"input": "你是谁?"}))
    print(chain.invoke({"input": "你叫什么名字?"}))
    print(chain.invoke({"input": "给我做一个自我介绍"}))

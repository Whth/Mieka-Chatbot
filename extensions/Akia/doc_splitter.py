import pathlib
import shutil
import time
from pathlib import Path
from typing import List

from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_core.documents import Document
from langchain_text_splitters import SentenceTransformersTokenTextSplitter

from modules.shared import explore_folder


def split_docs(input: str, output: str):
    """
    分割文档函数
    参数:
    - input: 输入路径，字符串，指向需要处理的文档数据目录
    - output: 输出路径，字符串，指定处理结果存储的目录
    功能:
    1. 从输入路径加载文档
    2. 将文档分割成更小的单元（句子或短语）
    3. 将分割后的文档保存到指定的输出目录中，每个分割单元作为单独的文本文件
    """

    # 初始化输入输出目录
    data_dir = Path(input)
    output_dir = pathlib.Path(output)
    # 清空输出目录
    shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 扫描输入目录，获取所有文件扩展名
    files_with_extension: List[str] = explore_folder(str(data_dir))
    # 文档加载器
    retriever = UnstructuredFileLoader(
        file_path=files_with_extension,
        mode="single",
    )
    time_stamp = time.time()
    # 加载文档
    docs: List[Document] = retriever.load()

    # 打印加载文档的时间和统计信息
    print(
        f"Loaded {len(docs)} documents from {data_dir} \n"
        f"\ttakes {(time.time() - time_stamp):.2f} seconds\n"
        f"\tave_loadtime: {(time.time() - time_stamp) / len(docs):.4f}"
    )
    time_stamp = time.time()
    # 文本分割器初始化
    text_splitter = SentenceTransformersTokenTextSplitter(
        chunk_overlap=12, tokens_per_chunk=128, model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    )
    # 分割文档
    documents = text_splitter.split_documents(docs)

    # 打印分割文档的时间和统计信息
    print(
        f"Splitting documents into {len(documents)} chunks\n"
        f"\ttakes {(time.time() - time_stamp):.2f} seconds\n"
        f"\tave_loadtime: {(time.time() - time_stamp) / len(documents):.4f}"
    )
    print("--------------------------------------")
    print(f"Writing document {output_dir}")
    # 保存分割后的文档
    for i, doc_ in enumerate(documents):
        with open(f"{output_dir}/{i}.txt", "w", encoding="utf-8") as f:
            f.write(doc_.page_content)


if __name__ == "__main__":
    quality = "./removed/high_quality"
    splitted = "./data/splitted"

    split_docs(quality, splitted)

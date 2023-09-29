import random


def remove_blank_lines(filename) -> None:
    """
    Removes blank lines from the given file.

    Args:
        filename (str): The path of the file to remove blank lines from.

    Returns:
        None
    """
    with open(filename, "r", encoding="utf-8") as file:
        lines = file.readlines()

    # 去除空行
    lines = [line.strip() for line in lines if line.strip()]

    with open(filename, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))


def get_paragraph(file_path, paragraph_length) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        novel = f.read()
        paragraphs = novel.split("\n")
        start = random.randint(0, len(paragraphs) - paragraph_length)
        paragraphs = paragraphs[start : start + paragraph_length]
    return "\n".join(paragraphs)

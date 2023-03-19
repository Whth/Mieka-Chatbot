import json
import os
import random
import re

from dynamic_prompt.config import wd_dir


def extract_wild_card_fname(root_path: str = './', suffix: str = '.txt', grammar_style: bool = False,
                            make_card_path_dict: bool = False):
    """
    search the wildcard in root path
    :param make_card_path_dict:
    :param grammar_style:
    :param root_path:
    :param suffix:
    :return:
    """
    card_list = []
    card_path_list = []
    sign = '__'
    search_stack = [root_path]
    while len(search_stack) > 0:
        search_dir = search_stack.pop()
        for f in os.listdir(search_dir):
            f_path = f'{search_dir}/{f}'
            if os.path.isdir(f_path):
                search_stack.append(f_path)
            if f_path.endswith(suffix):
                card_path_list.append(f_path)
                card_list.append(f.rstrip(suffix))
    if grammar_style:
        for i, card in enumerate(card_list):
            card_list[i] = f'{sign}{card}{sign}'
    if make_card_path_dict:
        # use card_list and card_path_list as key and value
        card_path_dict = {}
        for i in range(len(card_list)):
            card_path_dict[card_list[i]] = card_path_list[i]
        return card_path_dict
    return card_list


def remove_duplicates(lst):
    """
    Remove duplicates from a given list.

    Args:
        lst (list): A list to remove duplicates from.

    Returns:
        list: A new list with duplicates removed.
    """
    return list(set(lst))


def wd_interpreter(string: str, sign: str = '__', deduplicate: bool = True):
    """

    :param deduplicate:
    :param string:
    :param sign:
    :return:
    """
    pattern_str = f'({sign}.*?{sign}?)'
    pattern = re.compile(pattern=pattern_str)
    all_matched = re.findall(pattern, string)
    if deduplicate:
        all_matched = remove_duplicates(all_matched)
    return all_matched


def wd_convertor(string: str, wd_root: str = wd_dir):
    result = ''
    wd_dict = extract_wild_card_fname(wd_root, make_card_path_dict=True, grammar_style=True)
    temp = string
    for key, value in wd_dict.items():
        pass


def random_return_card_content(card_path: str, strength: float = 1.0) -> str:
    """
    :param card_path:
    :param strength:
    :return:
    """
    result = ''
    assert os.path.exists(card_path), 'card not exists'
    with open(card_path, mode='r') as card:
        lines = card.readlines()
        selected_line: str = random.choice(lines)
        selected_line = selected_line.rstrip()
        if strength == 1:
            result = selected_line
        else:
            prompt_tuples = selected_line.split(',')
            for prompt in prompt_tuples:
                result += f'{prompt}:{strength}'
    return result


test_str = '__hi__'
test_str2 = '__ hi__,__f__ __f__'
print(wd_interpreter(test_str))
print(wd_interpreter(test_str2))

if __name__ == '__main__':
    wd_root = 'G:\Games\StableDiffusion-WebUI\extensions\sd-dynamic-prompts\wildcards'
    save_dir = '../../Conversations_Extraction/wd_extracted'

    wd_dir_list = [
        rf"{wd_root}/devilkkw\body-1",
        rf"{wd_root}/devilkkw\body-2",
        rf"{wd_root}/devilkkw\clothes",
        rf"{wd_root}/devilkkw\colors",
        rf"{wd_root}/devilkkw\emoji",
        rf"{wd_root}/devilkkw\gesture",
        rf"{wd_root}/devilkkw\pose",
        rf"{wd_root}/devilkkw\background"
    ]
    wd_dict = {

    }

    for wd in wd_dir_list:
        wd_dict[wd.split('\\')[-1]] = extract_wild_card_fname(wd, grammar_style=True)

    print(wd_dict)
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    with open(f'{save_dir}/wd.json', 'w+') as f:
        json.dump(wd_dict, f, indent=4)

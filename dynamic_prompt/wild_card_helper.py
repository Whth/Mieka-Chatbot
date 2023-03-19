import hashlib
import json
import os
import random
import re

from dynamic_prompt.config import wd_dir
from dynamic_prompt.config import wd_presets


def extract_wild_card_fname(root_path: str = './', suffix: str = '.txt', grammar_style: bool = False,
                            make_card_path_dict: bool = False) -> list[str] or dict[str:str]:
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


def wd_interpreter(string: str, sign: str = '__', deduplicate: bool = True, match_strength: bool = False) -> list:
    """

    :param match_strength:
    :param deduplicate:
    :param string:
    :param sign:
    :return:
    """
    pattern_str = f'({sign}.*?{sign})'
    pattern = re.compile(pattern=pattern_str)
    all_matched = re.findall(pattern, string)
    if match_strength:
        # TODO: seems if multiple same wd with different strength,latter one will be overwritten by the first one
        pass
    if deduplicate:
        return list(set(all_matched))

    return all_matched


def wd_convertor(string: str, wd_root: str = wd_dir, sign: str = '__', bad_wd_remove: bool = True) -> str:
    """

    :param bad_wd_remove:
    :param sign:
    :param string:
    :param wd_root:
    :return:
    """

    wd_dict: dict = extract_wild_card_fname(wd_root, make_card_path_dict=True, grammar_style=True)
    cards = wd_interpreter(string=string, sign=sign)
    for card in cards:
        if card in wd_dict:
            string = string.replace(card, random_return_card_content(wd_dict.get(card)))
        else:

            if bad_wd_remove:
                string = string.replace(card, '')

    return string


def random_return_card_content(card_path: str, strength: float = 1.0, append_comma: bool = False) -> str:
    """
    :param append_comma:
    :param card_path:
    :param strength:
    :return:
    """
    result = ''
    assert os.path.exists(card_path), 'card not exists'
    spliter = ',' if append_comma else ''
    with open(card_path, mode='r', encoding='utf-8') as card:
        lines = card.readlines()
        selected_line: str = random.choice(lines)
        selected_line = selected_line.rstrip()
        if strength == 1:
            result = selected_line + spliter
        else:
            prompt_tuples = selected_line.split(',')
            for prompt in prompt_tuples:
                result += f'{prompt}:{strength}{spliter}'
    return result


# test_str = '__hi__,__size__ breasts'
# test_str2 = '__ hi__,__f__ __f__'
# print(wd_interpreter(test_str))
# print(wd_interpreter(test_str2))
# print(wd_convertor(test_str))


def compute_hash(lst: list):
    """
    Compute hash of a list of strings.

    Args:
        lst (list): A list of strings to compute the hash value for.

    Returns:
        str: A hash value of the given list as a 6-characters-long string.
    """
    joined_str = ''.join(lst)
    hash_obj = hashlib.sha256(joined_str.encode())
    hex_digest = hash_obj.hexdigest()
    six_characters_hash = hex_digest[:6]
    return six_characters_hash


def make_wd_preset(card_dirs: list[str], save_dir: str):
    wd_dict = {}
    for wd in card_dirs:
        wd_dict[re.split(pattern=r'\\|/', string=wd)[-1]] = extract_wild_card_fname(wd, grammar_style=True)
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    with open(f'{save_dir}/wd-{compute_hash(list(wd_dict.keys()))}.json', 'w+') as f:
        json.dump(wd_dict, f, indent=4)


if __name__ == '__main__':
    save_dir = wd_presets

    wd_dir_list = [
        rf"{wd_dir}/devilkkw\body-1",
        rf"{wd_dir}/devilkkw\body-2",
        rf"{wd_dir}/devilkkw\clothes",
        rf"{wd_dir}/devilkkw\colors",
        rf"{wd_dir}/devilkkw\emoji",
        rf"{wd_dir}/devilkkw\gesture",
        rf"{wd_dir}/devilkkw\pose",
        rf"{wd_dir}/devilkkw\background",
        rf'{wd_dir}/jumbo\appearance',
        rf'{wd_dir}/nai',
        rf'{wd_dir}/nsp/nsp-adj',
        rf'{wd_dir}/nsp/nsp-body',
        rf'{wd_dir}/nsp/nsp-fantasy',
        rf'{wd_dir}/nsp/nsp-noun',
        rf'{wd_dir}/devilkkw/attire',
    ]
    make_wd_preset(wd_dir_list, save_dir)

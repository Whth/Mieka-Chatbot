import json
import os
import random
import re
import time

from graia.ariadne.app import Ariadne
from graia.ariadne.entry import config
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, At, Image
from graia.ariadne.message.parser.base import MentionMe
from graia.ariadne.model import Member, Group, Friend

from sdDev.SD import sd_darw, sd_diff, deAssembly
import requests
import datetime
from baidu_translater.translater import Translater

trans = Translater()


def load_parm():
    global response_list, fastResponseList, app, SILENT_RATE, REWARD_RATE

    with open('config.json', encoding='utf-8', mode='r') as f:
        # TODO:增加更多有趣的语料
        word_dict = json.load(f)
        response_list = word_dict.get('cute')
        fastResponseList = word_dict.get('cute_fast_respond')
        print(f'Loaded respond List:{len(response_list)}|fastResponseList:{len(fastResponseList)}')

    with open('Bots.json', mode='r') as f:
        # TODO：多挂载几个机器人
        botInfo = json.load(f)
        app = Ariadne(
            config(
                verify_key=botInfo.get('verify_key'),  # 填入 VerifyKey
                account=botInfo.get('account'),  # 你的机器人的 qq 号
            ),
        )
    SILENT_RATE = 0.2
    REWARD_RATE = 0.9


load_parm()


def download_image(url: str, save_dir: str):
    """
    从给定的url下载图片
    :param save_dir:
    :param url: 图片的url
    :return: 下载图片的路径
    """
    img_name = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    print(f'downloading image on: {url}')
    response = requests.get(url)
    if response.status_code == 200:
        if not os.path.exists(save_dir):
            os.makedirs(f'{save_dir}')
        path = f'{save_dir}/{img_name}.png'
        with open(path, 'wb') as f:
            f.write(response.content)
        print(f'downloaded net image,save at: {path}')
        return path
    return None


def NPL_reFormat(natural_sentence: str, split_keyword: str = None):
    """

    :param split_keyword:
    :param natural_sentence:
    :return:
    """
    if split_keyword:
        word_pattern = split_keyword
    else:
        word_pattern = '要|画个|画一个|来一个|来个|给我'
    prompts = re.split(pattern=word_pattern, string=natural_sentence)
    print(prompts)
    if len(prompts) < 2:
        return ''
    else:
        return trans.translate('en', prompts[-1])


async def groupDiffusion(app: Ariadne, group: Group, member: Member, chain: MessageChain,
                         neg_prompts: str, pos_prompts: str):
    """

    :param app:
    :param member:
    :param group:
    :param chain:
    :param neg_prompts:
    :param pos_prompts:
    :return:
    """
    use_reward: bool = False
    if Image in chain:
        print('using img2img')
        # 如果包含图片则使用img2img
        img_path = download_image(chain[Image, 1][0].url, save_dir='./group_temp')
        generated_path = sd_diff(init_file_path=img_path, positive_prompt=pos_prompts, negative_prompt=neg_prompts)
    else:
        print('using txt2img')
        if random.random() < REWARD_RATE and use_reward:

            generated_path = [sd_darw(positive_prompt=pos_prompts, negative_prompt=neg_prompts)] * 2
        else:
            generated_path = sd_darw(positive_prompt=pos_prompts, negative_prompt=neg_prompts)
    await app.send_message(group, At(member) + Plain(random.choice(response_list)) + Image(
        path=generated_path))
    # 实际上 MessageChain(...) 有没有 "[]" 都没关系


@app.broadcast.receiver("GroupMessage", decorators=[MentionMe()])
async def friend_message_listener(app: Ariadne, member: Member, group: Group, chain: MessageChain = MentionMe(False)):
    """
    快速响应群at
    :param app:
    :param member:
    :param group:
    :param chain:
    :return:
    """
    reFormatted = NPL_reFormat(str(chain))
    if reFormatted == '':

        pos_prompts, neg_prompts = deAssembly(str(chain))
    else:
        # 自然语言只有正向
        pos_prompts, neg_prompts = reFormatted, ''
    await groupDiffusion(app, group, member, chain, neg_prompts, pos_prompts)


@app.broadcast.receiver("GroupMessage")
async def group_fast_feed(app: Ariadne, group: Group, chain: MessageChain):
    if random.random() < SILENT_RATE or '+' not in chain:
        return
    time.sleep(7)

    await app.send_message(group, Plain(random.choice(fastResponseList)))


@app.broadcast.receiver("GroupMessage")
async def quiet_listener(app: Ariadne, member: Member, group: Group, chain: MessageChain):
    if '+' not in str(chain):
        return
    pos_prompts, neg_prompts = deAssembly(str(chain))
    await groupDiffusion(app, group, member, chain, neg_prompts, pos_prompts)


@app.broadcast.receiver("FriendMessage")
async def fast_feed_friend(app: Ariadne, friend: Friend, chain: MessageChain):
    if '+' not in str(chain) and 'mika' not in str(chain):
        return
    time.sleep(7)
    await app.send_message(friend, Plain(random.choice(fastResponseList)))


@app.broadcast.receiver("FriendMessage")
async def img_gen_friend(app: Ariadne, friend: Friend, chain: MessageChain):
    """

    :param app:
    :param friend:
    :param chain:
    :return:
    """
    use_reward: bool = False
    dear_name = 'mika'
    if '+' not in str(chain) and dear_name not in str(chain):
        return
    if 'mika' in str(chain):
        pos_prompts, neg_prompts = NPL_reFormat(str(chain), split_keyword=dear_name), ''
    else:
        pos_prompts, neg_prompts = deAssembly(str(chain))

    if Image in chain:
        print('using img2img')
        # 如果包含图片则使用img2img
        img_path = download_image(chain[Image, 1][0].url, save_dir='./friend_temp')
        generated_path = sd_diff(init_file_path=img_path, positive_prompt=pos_prompts, negative_prompt=neg_prompts)
    else:
        print('using txt2img')
        if random.random() < REWARD_RATE and use_reward:
            generated_path = [sd_darw(positive_prompt=pos_prompts, negative_prompt=neg_prompts)] * 2
        else:
            generated_path = sd_darw(positive_prompt=pos_prompts, negative_prompt=neg_prompts)
    await app.send_message(friend,
                           Plain(random.choice(response_list)) + Image(path=generated_path))
    # 实际上 MessageChain(...) 有没有 "[]" 都没关系


app.launch_blocking()

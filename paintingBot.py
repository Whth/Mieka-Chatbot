import datetime
import json
import os
import random
import subprocess
import time

import requests
from graia.ariadne.app import Ariadne
from graia.ariadne.entry import config
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, At, Image
from graia.ariadne.message.parser.base import MentionMe
from graia.ariadne.model import Member, Group, Friend
from graia.scheduler import GraiaScheduler, timers

from sdDev.SD import sd_draw, sd_diff, deAssembly, npl_reformat

global finishResponseList, fastResponseList, agreeResponseList, disagreeResponseList, goodMorning
global rewardResponseList, masterList
global groups_list
global app, SILENT_RATE, REWARD_RATE, AGREED_RATE


def load_parm():
    global finishResponseList, fastResponseList, agreeResponseList, disagreeResponseList, goodMorning
    global rewardResponseList, masterList
    global groups_list
    global app, SILENT_RATE, REWARD_RATE, AGREED_RATE
    with open('config.json', encoding='utf-8', mode='r') as f:
        # TODO:增加更多有趣的语料
        word_dict = json.load(f)
        finishResponseList = word_dict.get('cute')
        fastResponseList = word_dict.get('cute_fast_respond')
        agreeResponseList = word_dict.get('agree')
        disagreeResponseList = word_dict.get('disagree')
        rewardResponseList = word_dict.get('reward')
        goodMorning = word_dict.get("goodMorning")
        groups_list = word_dict.get("groups")
        masterList = word_dict.get('masterSan')
        print(f'Loaded: \n'
              f'\tfinishResponseList:{len(finishResponseList)}\n'
              f'\tfastResponseList:{len(fastResponseList)}\n'
              f'\tagreeResponseList:{len(agreeResponseList)}\n'
              f'\tdisagreeResponseList:{len(disagreeResponseList)}\n'
              f'\tgoodMorningList:{len(goodMorning)}\n'
              f'\tGroup list: {groups_list}\n'
              f'\tMaster List: {len(masterList)}\n')
        # TODO:增加语料的有效判断

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
    REWARD_RATE = 0.1
    AGREED_RATE = 0.65
    # FIXME:reward picture clash,because Image use only one path


def check_mcl_online(auto=True):
    try:
        requests.get('http://127.0.0.1:8080')
    except:
        mcl_name = "D:\mirai-cli\mcl.cmd"
        mcl_dir = "D:\mirai-cli"

        subprocess.Popen("cmd.exe /c" + mcl_name, cwd=mcl_dir)


load_parm()

# check_diffusion_online()
check_mcl_online()


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


async def groupDiffusion(app: Ariadne, group: Group, member: Member, chain: MessageChain,
                         neg_prompts: str, pos_prompts: str, use_korea_lora: bool = True, use_reward: bool = True):
    """

    :param app:
    :param member:
    :param group:
    :param chain:
    :param neg_prompts:
    :param pos_prompts:
    :return:
    """
    if Image in chain:
        print('using img2img')
        # 如果包含图片则使用img2img
        img_path = download_image(chain[Image, 1][0].url, save_dir='./group_temp')
        generated_path = sd_diff(init_file_path=img_path, positive_prompt=pos_prompts, negative_prompt=neg_prompts)
        await app.send_message(group, At(member) + Plain(random.choice(finishResponseList)) + Image(
            path=generated_path))
    else:
        print('using txt2img')
        generated_path = sd_draw(positive_prompt=pos_prompts, negative_prompt=neg_prompts)
        await app.send_message(group, At(member) + Plain(random.choice(finishResponseList)) + Image(
            path=generated_path))
        if random.random() < REWARD_RATE and use_reward:
            print(f'with REWARD_RATE: {REWARD_RATE}|REWARDED')
            generated_path_reward = sd_draw(positive_prompt=pos_prompts, negative_prompt=neg_prompts)
            await app.send_message(group, At(member) + Plain(random.choice(rewardResponseList)) + Image(
                path=generated_path_reward))


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
    reFormatted = npl_reformat(str(chain))
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
async def group_I_think(app: Ariadne, group: Group, chain: MessageChain):
    if "我想" in str(chain) or "我觉得" in str(chain) or "是不是" in str(chain) or "该不该" in str(chain):
        time.sleep(7)
        if random.random() < AGREED_RATE:
            print(f"Agree: {chain}")
            await app.send_message(group, Plain(random.choice(agreeResponseList)))

        else:
            print(f"Disagree: {chain}")
            await app.send_message(group, Plain(random.choice(disagreeResponseList)))


@app.broadcast.receiver("GroupMessage")
async def quiet_listener_group(app: Ariadne, member: Member, group: Group, chain: MessageChain):
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
    MIN_PIXEL = 446
    MAX_PIXEL = 1020
    use_reward: bool = True
    dear_name = 'mika'
    max_batch_size = 20
    pos_prompts, neg_prompts, batch_size = '', '', 1
    use_fr = False

    if '+' not in str(chain) and dear_name not in str(chain):
        return
    if 'mika' in str(chain):
        pos_prompts, batch_size = npl_reformat(str(chain), split_keyword=dear_name, specify_batch_size=True)
    else:
        pos_prompts, neg_prompts, batch_size = deAssembly(str(chain), specify_batch_size=True)
    if '#' in str(chain):
        use_fr = True
    if Image in chain:
        print('using img2img')
        # 如果包含图片则使用img2img
        img_path = download_image(chain[Image, 1][0].url, save_dir='./friend_temp')
        generated_path = sd_diff(init_file_path=img_path, positive_prompt=pos_prompts, negative_prompt=neg_prompts)
        await app.send_message(friend,
                               Plain(random.choice(finishResponseList)) + Image(path=generated_path))
    else:
        print('using txt2img')
        batch_size = max_batch_size if batch_size > max_batch_size else batch_size
        print(f'going with [{batch_size}] pictures')
        for _ in range(batch_size):
            size = [random.randint(MIN_PIXEL, MAX_PIXEL), random.randint(MIN_PIXEL, MAX_PIXEL)]
            generated_path = sd_draw(positive_prompt=pos_prompts, negative_prompt=neg_prompts, safe_mode=False,
                                     face_restore=use_fr, size=size)
            await app.send_message(friend, Plain(random.choice(finishResponseList)) + Image(
                path=generated_path))

        if random.random() < REWARD_RATE and use_reward:
            print(f'with REWARD_RATE: {REWARD_RATE}|REWARDED')
            generated_path_reward = sd_draw(positive_prompt=pos_prompts, negative_prompt=neg_prompts, size=size)
            await app.send_message(friend, Plain(random.choice(rewardResponseList)) + Image(
                path=generated_path_reward))


# <editor-fold desc="Schedules">
scheduler = Ariadne.create(GraiaScheduler)


@scheduler.schedule(timers.crontabify('0 7 * * * 0'))
async def good_morning(channel: Ariadne = app):
    """
    good morning func
    :param channel:
    :return:
    """
    max_delay_seconds = 3600
    prompt = 'pink hair girl:1.4,blue eyes,student uniform:1.3,standing:1.3,landscape:1.5,blue sky,morning,' \
             'on the street:1.2,hello!,hi,wave hands,greeting,good morning,tie,collar'
    time.sleep(random.randint(0, max_delay_seconds))
    generated_path = sd_draw(positive_prompt=prompt, size=[576, 768])
    await channel.send_group_message(groups_list[1],
                                     Plain(random.choice(goodMorning)) + Image(path=generated_path))


def get_random_file(folder):
    """

    :param folder:
    :return:
    """
    files = os.listdir(folder)
    index = random.randint(0, len(files) - 1)
    return os.path.join(folder, files[index])


@scheduler.schedule(timers.crontabify('0 6 * * * *'))
async def random_emoji(channel: Ariadne = app):
    """
    random send a gif  in a day
    :param channel:
    :return:
    """
    max_delay = 12 * 60 * 60
    time.sleep(random.randint(1, max_delay))
    gif_dir_path = './gifs'
    await channel.send_group_message(groups_list[1], Image(path=get_random_file(gif_dir_path)))


# </editor-fold>
@scheduler.schedule(timers.every_custom_minutes(69))
async def live(channel: Ariadne = app):
    prompt = 'huge breast neko girl,loli:1.4,red hair:1.4,purple eyes:1.4,full body cloth,tie,standing,grin'
    if random.random() < 0.3:
        prompt += 'blush naked,climax,sweat drop,wet cloth'
    generated_path = sd_draw(positive_prompt=prompt, size=[576, 832], safe_mode=False)
    await channel.send_friend_message(2191133626,
                                      Plain(random.choice(masterList)) + Image(path=generated_path))


app.launch_blocking()

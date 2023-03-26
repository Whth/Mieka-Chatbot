import datetime
import json
import os
import random
import re
import subprocess
import time

import requests
from graia.ariadne.app import Ariadne
from graia.ariadne.entry import config
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.ariadne.message.parser.base import MentionMe, ContainKeyword
from graia.ariadne.model import Member, Group, Friend
from graia.scheduler import GraiaScheduler, timers

from sdDev.SD import sd_draw, sd_diff, deAssembly, npl_reformat

global finishResponseList, fastResponseList, agreeResponseList, disagreeResponseList, goodMorning
global rewardResponseList, masterList, eroList
global groups_list
global app, SILENT_RATE, REWARD_RATE, AGREED_RATE

global scheduler_config


def load_parm():
    global finishResponseList, fastResponseList, agreeResponseList, disagreeResponseList, goodMorning
    global rewardResponseList, masterList, eroList
    global groups_list
    global app, SILENT_RATE, REWARD_RATE, AGREED_RATE
    global scheduler_config
    with open('chat_dict.json', encoding='utf-8', mode='r') as f:
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
        eroList = word_dict.get('erotic')
        print(f'Loaded: \n'
              f'\tfinishResponseList:{len(finishResponseList)}\n'
              f'\tfastResponseList:{len(fastResponseList)}\n'
              f'\tagreeResponseList:{len(agreeResponseList)}\n'
              f'\tdisagreeResponseList:{len(disagreeResponseList)}\n'
              f'\tgoodMorningList:{len(goodMorning)}\n'
              f'\tGroup list: {groups_list}\n'
              f'\tMaster List: {len(masterList)}\n'
              f'\tErotic list: {len(eroList)}\n')
        # TODO:增加语料的有效判断

    with open('Bots.json', mode='r') as f:
        botInfo = json.load(f)
        app = Ariadne(
            config(
                verify_key=botInfo.get('verify_key'),  # 填入 VerifyKey
                account=botInfo.get('account')[1],  # 你的机器人的 qq 号
            ),
        )

    with open('sch_config.json', mode='r+') as f:
        scheduler_config = json.loads(f.read())
        f.seek(0)
        scheduler_config['live_enabled'] = False
        scheduler_config['echi_enabled'] = False
        json.dump(scheduler_config, f, indent=4)
        f.close()
    SILENT_RATE = 0.2
    REWARD_RATE = 0.1
    AGREED_RATE = 0.65


def check_mcl_online(auto=True):
    try:
        requests.get('http://127.0.0.1:8080')
    except:
        mcl_name = "D:\mirai-cli\mcl.cmd"
        mcl_dir = "D:\mirai-cli"

        subprocess.Popen("cmd.exe /c" + mcl_name, cwd=mcl_dir)


def message_constructor(string: str or list[str], img: str or list[str], random_string: bool = True) -> MessageChain:
    """

    :param random_string:
    :param string:
    :param img:
    :return:
    """
    chain = MessageChain('')
    if isinstance(string, list) and random_string:
        chain = Plain(random.choice(string))
    elif (isinstance(string, list) and random_string is False) or isinstance(string, str):
        chain = MessageChain(string)

    if isinstance(img, list):
        for i in img:
            chain += Image(path=i)
    elif isinstance(img, str):
        chain += Image(path=img)

    return chain


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
                         neg_prompts: str, pos_prompts: str, use_reward: bool = True,
                         batch_size: int = 1, use_doll_lora: bool = True, safe_mode: bool = True,
                         use_body_lora: bool = False):
    """

    :param safe_mode:
    :param use_reward:
    :param use_body_lora:
    :param use_doll_lora:
    :param batch_size:
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
        img_path = download_image(chain[Image, 1][0].url, save_dir='./friend_temp')
        generated_path = sd_diff(init_file_path=img_path, positive_prompt=pos_prompts, negative_prompt=neg_prompts,
                                 use_control_net=False)

        await app.send_message(group, message_constructor(finishResponseList, generated_path))
    else:
        print('using txt2img')
        print(f'going with [{batch_size}] pictures')
        size = [542, 864]
        if pos_prompts != '' and 'hair' not in pos_prompts:
            categories = ['hair']
            pos_prompts += get_random_prompts(categories=categories)
        for _ in range(batch_size):
            generated_path = sd_draw(positive_prompt=pos_prompts, negative_prompt=neg_prompts, safe_mode=safe_mode,
                                     size=size, use_doll_lora=use_doll_lora, use_body_lora=use_body_lora)

            await app.send_message(group, message_constructor(finishResponseList, generated_path))

        if random.random() < REWARD_RATE and use_reward:
            print(f'with REWARD_RATE: {REWARD_RATE}|REWARDED')
            size = [542, 864]
            generated_path_reward = sd_draw(positive_prompt=pos_prompts, negative_prompt=neg_prompts,
                                            safe_mode=safe_mode,
                                            size=size, use_doll_lora=use_doll_lora, use_body_lora=use_body_lora)
            await app.send_message(group, message_constructor(rewardResponseList, generated_path_reward))


@app.broadcast.receiver("GroupMessage", decorators=[MentionMe()])
async def img_gen_group_atme(app: Ariadne, member: Member, group: Group, chain: MessageChain = MentionMe(False)):
    """
    快速响应群at
    :param app:
    :param member:
    :param group:
    :param chain:
    :return:
    """

    reFormatted, batch_size = npl_reformat(str(chain), specify_batch_size=True)
    if reFormatted == '':
        return reFormatted
    print(f'npl decrypt{reFormatted}')

    pos_prompts, neg_prompts = reFormatted, ''
    if batch_size > 7:
        batch_size = 7
    await groupDiffusion(app, group, member, chain, neg_prompts, pos_prompts, batch_size=batch_size,
                         use_doll_lora=False,
                         safe_mode=False, use_body_lora=False, )


@app.broadcast.receiver("GroupMessage")
async def img_gen_group_quiet(app: Ariadne, member: Member, group: Group, chain: MessageChain):
    """

    :param app:
    :param member:
    :param group:
    :param chain:
    :return:
    """
    if '+' not in str(chain):
        return
    pos_prompts, neg_prompts, batch_size = deAssembly(str(chain), specify_batch_size=True)
    if batch_size > 7:
        batch_size = 7
    await groupDiffusion(app, group, member, chain, neg_prompts, pos_prompts, batch_size=batch_size,
                         use_doll_lora=False,
                         safe_mode=True, use_body_lora=False)


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
    max_batch_size = 100
    pos_prompts, neg_prompts, batch_size = '', '', 1
    use_fr = False
    use_doll_lora = True if '*' in str(chain) else False

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
        generated_path = sd_diff(init_file_path=img_path, positive_prompt=pos_prompts, negative_prompt=neg_prompts,
                                 use_doll_lora=use_doll_lora, use_control_net=True)

        await app.send_message(friend, message_constructor(finishResponseList, generated_path))
    else:
        print('using txt2img')
        batch_size = max_batch_size if batch_size > max_batch_size else batch_size
        print(f'going with [{batch_size}] pictures')
        for _ in range(batch_size):
            while True:
                size = [random.randint(MIN_PIXEL, MAX_PIXEL), random.randint(MIN_PIXEL, MAX_PIXEL)]
                if (size[0] / size[1]) < 0.8:
                    break
            generated_path = sd_draw(positive_prompt=pos_prompts, negative_prompt=neg_prompts, safe_mode=False,
                                     face_restore=use_fr, size=size, use_doll_lora=use_doll_lora)
            await app.send_message(friend, message_constructor(finishResponseList, generated_path))

        if random.random() < REWARD_RATE and use_reward:
            print(f'with REWARD_RATE: {REWARD_RATE}|REWARDED')
            size = [random.randint(MIN_PIXEL, MAX_PIXEL), random.randint(MIN_PIXEL, MAX_PIXEL)]
            generated_path_reward = sd_draw(positive_prompt=pos_prompts, negative_prompt=neg_prompts, size=size,
                                            use_doll_lora=use_doll_lora)
            await app.send_message(friend, message_constructor(rewardResponseList, generated_path_reward))


@app.broadcast.receiver("GroupMessage")
async def group_fast_feed(app: Ariadne, group: Group, chain: MessageChain):
    if random.random() < SILENT_RATE or '+' not in chain:
        return
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


@app.broadcast.receiver("FriendMessage")
async def fast_feed_friend(app: Ariadne, friend: Friend, chain: MessageChain):
    if '+' not in str(chain) and 'mika' not in str(chain):
        return
    await app.send_message(friend, Plain(random.choice(fastResponseList)))


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

    await channel.send_group_message(groups_list[0], message_constructor(goodMorning, generated_path))


def get_random_file(folder):
    """

    :param folder:
    :return:
    """
    from file_mannager.fileMannager import explore_folder
    files_list = explore_folder(folder)
    return random.choice(files_list)


@app.broadcast.receiver("GroupMessage", decorators=[ContainKeyword(keyword='mk')])
async def random_emoji(group: Group, chain: MessageChain, channel: Ariadne = app, ):
    """
    random send a gif  in a day
    :param group:
    :param chain:
    :param channel:
    :return:
    """

    gif_dir_path = r'N:\CloudDownloaded\01 GIF格式4700个'
    await channel.send_message(group, Image(path=get_random_file(gif_dir_path)))


# </editor-fold>
@scheduler.schedule(timers.every_custom_minutes(1))
async def live(channel: Ariadne = app):
    global scheduler_config
    with open('sch_config.json', mode='r') as f:
        scheduler_config = json.load(f)
        f.close()
    if scheduler_config.get('live_enabled'):

        live_max_time = scheduler_config.get('max_time')
        live_interval = scheduler_config.get('interval')
        live_times = int(live_max_time / live_interval) + 1
        print(f'live started interval: [{live_interval}]|max_time: [{live_max_time}]|live_times: [{live_times}]')
        for _ in range(live_times):

            with open('sch_config.json', mode='r') as f:
                scheduler_config = json.load(f)
                f.close()
            if not scheduler_config.get('live_enabled'):
                break
            categories = ['hair', 'sfw_wd']
            additional_prompt = get_random_prompts(categories)
            prompt = 'large long breasts,sexy,headdress,1girl,' \
                     f'{additional_prompt},' \
                     f'collar:1.3,cleavage,navel,loose coat,wide hips,exposed shoulder skin' \
                     f',upper body ,close up,blush,pink' \
                     'tie:1.3,open cloth,high panties,thigh highs,fat thighs,standing,feeling'
            if random.random() < 0.3:
                prompt += 'blush, nake,climax,sweaty,wet cloth'
            generated_path = sd_draw(positive_prompt=prompt, size=[576, 832], safe_mode=False, use_doll_lora=False,
                                     face_restore=False, use_body_lora=True, use_honey_lora=True)
            for master_account in scheduler_config.get('masters'):
                await channel.send_friend_message(master_account, message_constructor(masterList, generated_path))
            time.sleep(live_interval * 60)

        print('live end')
        with open('sch_config.json', mode='r+') as f:
            scheduler_config = json.loads(f.read())
            f.seek(0)
            scheduler_config['live_enabled'] = False
            json.dump(scheduler_config, f, indent=4)
            f.close()


# TODO:简化特定组合prompt包装
@scheduler.schedule(timers.every_custom_minutes(1))
async def echi(channel: Ariadne = app):
    """

    :param channel:
    :return:
    """
    global scheduler_config
    with open('sch_config.json', mode='r') as f:
        scheduler_config = json.load(f)
        f.close()
    if scheduler_config.get('echi_enabled'):

        live_max_time = scheduler_config.get('max_time')
        live_interval = scheduler_config.get('interval')
        live_times = int(live_max_time / live_interval) + 1
        print(f'echi started interval: [{live_interval}]|max_time: [{live_max_time}]|live_times: [{live_times}]')
        for _ in range(live_times):

            with open('sch_config.json', mode='r') as f:
                scheduler_config = json.load(f)
                f.close()
            if not scheduler_config.get('echi_enabled'):
                break
            categories = ['hair', 'sex_wd']
            additional_prompt = get_random_prompts(categories, emphasize_multiplier=1.1)
            prompt = '1girl:1.2,solo' \
                     f'{additional_prompt},'

            if random.random() < 0.3:
                prompt += 'nake:1.3,climax,sweaty:1.2,steam'
            generated_path = sd_draw(positive_prompt=prompt, size=[576, 832], safe_mode=False, use_doll_lora=False,
                                     face_restore=False, use_body_lora=False, use_echi_lora=True, use_ero_TI=True)
            for master_account in scheduler_config.get('masters'):
                await channel.send_friend_message(master_account, message_constructor(eroList, generated_path))
            time.sleep(live_interval * 60)

        print('echi end')
        with open('sch_config.json', mode='r+') as f:
            scheduler_config = json.loads(f.read())
            f.seek(0)
            scheduler_config['echi_enabled'] = False
            json.dump(scheduler_config, f, indent=4)
            f.close()


def get_random_prompts(categories: list[str], emphasize_multiplier: float = 1.4, append_comma: bool = True) -> str:
    prompts = ''
    with open('prompts_dict.json', mode='r') as f:
        prompt_dict = json.load(f)
    spliter = ',' if append_comma else ''
    for category in categories:

        prompts_set_dict: dict = prompt_dict.get(category)

        for set_name, set_content in prompts_set_dict.items():
            prompt = random.choice(set_content)
            print(f'[{set_name}] use [{prompt}]')
            prompts += f'{prompt}:{emphasize_multiplier}{spliter}'
    print(f'result prompts: {prompts}')
    return prompts


@app.broadcast.receiver('FriendMessage')
async def check_key(chain: MessageChain):
    """
    receiving cmd from message
    :param chain:
    :return:
    """
    keywords = ['live', 'echi']
    enabled_regfix = '_enabled'
    start_keyword = 'start'
    end_keyword = 'end'
    if '#' in chain:
        print('received cmd: ' + chain)
    for keyword in keywords:
        enabled = True if re.match(f'#{keyword} {start_keyword}', str(chain)) else None
        if enabled is None:
            enabled = False if re.match(f'#{keyword} {end_keyword}', str(chain)) else None
        if enabled is not None:
            print(f"Change [{keyword}{enabled_regfix}] key to [{enabled}]")
            with open("sch_config.json", mode='w+') as f:
                scheduler_config[f'{keyword}{enabled_regfix}'] = enabled
                json.dump(scheduler_config, f, indent=4)
                f.close()


app.launch_blocking()

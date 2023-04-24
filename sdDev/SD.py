import base64
import hashlib
import io
import math
import os.path
import random
import re
import sys
from random import uniform

import requests
from PIL import Image, PngImagePlugin
from slugify import slugify

from dynamic_prompt.wild_card_helper import wd_convertor

sys.path.append('..')
from baidu_translater.translater import Translater

trans = Translater()

samplers_list = [
    "Euler a", "LMS", "DPM++ SDE", "LMS Karras", "DPM2 a Karras", "DPM++ 2M Karras", "DPM++ SDE Karras", "DDIM",
    "PLMS", 'UniPC'
]
url = "http://localhost:7860"
# url = 'http://172.17.32.1:7680'
start_method_name = "webui-user.bat"
method_dir = r'G:\Games\StableDiffusion-WebUI'


def deAssembly(message: str, specify_batch_size: bool = False):
    """

    :param specify_batch_size:
    :param message:
    :return:
    """

    if message == "":
        return '', ''
    pos_pattern = '(\+(.*?)\+)?'
    pos_prompt = re.findall(pattern=pos_pattern, string=message)
    for i in pos_prompt:
        if i[0] != '':
            pos_prompt = i[1]
    print(f'pos: {pos_prompt}')
    neg_pattern = '(\-(.*?)\-)?'
    neg_prompt = re.findall(pattern=neg_pattern, string=message)
    for i in neg_prompt:
        if i[0] != '':
            neg_prompt = i[1]
    print(f'neg: {neg_prompt}')

    if specify_batch_size:
        batch_size_pattern = '(\d+(p|P))?'
        temp = re.findall(pattern=batch_size_pattern, string=message)
        for match in temp:
            if match[0] != '':
                batch_size = int(match[0].strip(match[1]))
                return pos_prompt, neg_prompt, batch_size
        return pos_prompt, neg_prompt, 1  # default

    return pos_prompt, neg_prompt,


def rename_image_with_hash(image_path):
    """
    对指定路径的图片文件名后面加一串长度为6的图片内容的哈希值，重命名文件并返回重命名后的图片路径
    :param image_path: 图片路径
    :return: 重命名后的图片路径
    """
    # 获取图片文件名
    image_name = os.path.basename(image_path)
    # 获取图片文件名前缀
    image_name_prefix = os.path.splitext(image_name)[0]
    # 获取图片文件名后缀
    image_name_suffix = os.path.splitext(image_name)[1]
    # 读取图片文件
    with open(image_path, 'rb') as f:
        image_content = f.read()
    # 计算图片文件内容的哈希值
    image_hash = hashlib.md5(image_content).hexdigest()[:6]
    # 重命名图片文件
    new_image_name = image_name_prefix + '_' + image_hash + image_name_suffix
    # 获取图片文件所在目录
    image_dir = os.path.dirname(image_path)
    # 生成重命名后的路径并重命名
    new_image_path = os.path.join(image_dir, new_image_name)
    os.rename(image_path, new_image_path)
    # 返回重命名后的图片路径
    return new_image_path


def sd_draw(positive_prompt: str = None, negative_prompt: str = None, steps: int = 19, size: list = [512, 768],
            use_sampler: str or int = 'UniPC', config_scale: float = 7 + random.random(),
            output_dir='./output',
            use_doll_lora: bool = False, safe_mode: bool = True, face_restore: bool = False,
            use_body_lora: bool = False, use_ero_TI: bool = False, use_honey_lora: bool = False,
            use_echi_lora: bool = False, use_wd: bool = True) -> list[str]:
    """
    SD Ai drawing txt2img sd_api function
    :type positive_prompt: object
    :param use_honey_lora:
    :param use_ero_TI:
    :param use_body_lora:
    :param safe_mode:
    :param face_restore:
    :param use_doll_lora:
    :param size:
    :param output_dir:
    :param positive_prompt:
    :param negative_prompt:
    :param steps:
    :param use_sampler:
    :param config_scale:
    :return:
    """

    if type(use_sampler) == str and use_sampler in samplers_list:
        usedSampler = use_sampler
    elif type(use_sampler) == int and 0 <= use_sampler < len(samplers_list):
        usedSampler = samplers_list[use_sampler]
    else:
        usedSampler = 'DPM++ SDE Karras'

    if steps > 30 or steps < 0:
        steps = 20

    if config_scale > 11 or config_scale < 5:
        config_scale = 7.0

    if type(positive_prompt) != str or not positive_prompt.strip():
        positive_prompt = 'pink hair:1.2,hair pin:1.2,girl,student uniform:1.4,uniform,uniform,collar:1.3,' \
                          'white stocking:1.3,tie:1.3,on the street,unhappy,medium breasts,' \
                          'upper body,watery eyes,ponytails,twintails,hairpin,beautiful eyes,delicate eys, ' \
                          'luscious ,close up'
        safe_word = ',sfw:1.1' if safe_mode else ''

        positive_prompt = positive_prompt + safe_word
    if type(negative_prompt) != str or not negative_prompt.strip():
        negative_prompt = 'eyeshadow,eye pouches:1.3,nipple,zoom out:1.4'
        safe_word = ',nsfw:1.3' if safe_mode else ''

        negative_prompt = negative_prompt + safe_word
    if use_doll_lora:
        doll_lora_min = 0.06
        doll_lora_normal_max = 0.22
        doll_lora_emphasis_max = 0.86
        doll_lora = f'<lora:japaneseDollLikeness_v10:{uniform(doll_lora_min, doll_lora_normal_max)}>' \
                    f' <lora:koreanDollLikeness_v10:{uniform(doll_lora_min, doll_lora_emphasis_max)}> ' \
                    f'<lora:taiwanDollLikeness_v10:{uniform(doll_lora_min, doll_lora_normal_max)}> '
        print('use doll lora')
        positive_prompt += doll_lora
    if use_honey_lora:
        honey_lora_max = 0.9
        honey_lora_min = 0.65
        honey_lora_list = [f'<lora:HinaIAmYoung22_zny10:{uniform(honey_lora_min, honey_lora_max)}>',
                           f' <lora:saikaKawakita_saikaV20:{uniform(honey_lora_min, honey_lora_max)}>',
                           f'<lora:momo_V10:{uniform(honey_lora_min, honey_lora_max)}>',
                           f'<lora:irene_60:{uniform(honey_lora_min, honey_lora_max)}>']
        print('use honey lora')
        positive_prompt += random.choice(honey_lora_list)
    if use_body_lora:
        body_lora_max = 0.5
        body_lora_min = 0.06
        body_lora = f'<lora:hyperbreasts_v5Lora:{uniform(body_lora_min, body_lora_max)}>, ' \
                    f'<lora:hugeAssAndBoobs_v1:{uniform(body_lora_min, body_lora_max)}>'
        positive_prompt += body_lora
        print(f'using body lora {body_lora}')
    if use_echi_lora:
        echi_lora_min = 0.75
        echi_lora_max = 0.92
        echi_lora_list = ['<lora:Anus_Peek:0.87>',
                          '<lora:breastfeedingHandjob_v10:0.87>',
                          '<lora:breastsOnGlass_v10:0.87>',
                          '<lora:closed_Pussy:0.87>',
                          '<lora:grabbingOwnAss_v1Pruned:0.87>',
                          '<lora:ing_trembling:0.87>',
                          '<lora:jackopose:0.87>',
                          '<lora:kirt_in_mouth_32r32d1e:0.87>',
                          '<lora:lMissionary:0.87>',
                          '<lora:mez:0.87>',
                          '<lora:povImminentPenetration_ipv1:0.87>',
                          '<lora:self_Breast_Suck:0.87>',
                          '<lora:shirtliftALORAFor_shirtliftv1:0.87>',
                          '<lora:skirtliftTheAstonishing_skirtliftv1:0.87>']
        echi_lora: str = random.choice(echi_lora_list)
        echi_lora.replace('0.87', f'{uniform(echi_lora_min, echi_lora_max)}')
        positive_prompt += echi_lora
        print(f'using echi lora {echi_lora}')
    styles = [
        "inte fix"

    ]

    if use_ero_TI:
        styles.append("ero")
    if use_wd:
        print('using wd')
        positive_prompt = wd_convertor(positive_prompt)
    payload = {
        "enable_hr": True,
        "denoising_strength": 0.53,
        "hr_scale": 1.2,
        "prompt": positive_prompt,
        "negative_prompt": negative_prompt,
        "sampler_name": usedSampler,
        "steps": steps,
        "subseed": -1,
        "subseed_strength": 0.90,
        "restore_faces": face_restore,
        "cfg_scale": config_scale,
        "width": size[0],
        "height": size[1],
        "styles": styles,

    }

    print(payload)
    response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)
    r = response.json()
    img_base64_list = r['images']
    saved_path_with_hash = single_task(img_base64_list, output_dir)
    return saved_path_with_hash


def sd_diff(init_file_path: str, positive_prompt: str = '', negative_prompt: str = '', steps: int = 15,
            use_sampler: str or int = "UniPC", denoising_strength: float = 0.74, config_scale: float = 7,
            output_dir: str = './output', fit_original_size: bool = True, use_doll_lora: bool = True,
            safe_mode: bool = False, use_control_net: bool = False) -> list[str]:
    """
    SD Ai drawing img2img sd_api function
    :param use_control_net:
    :param use_doll_lora:
    :param safe_mode:
    :param fit_original_size:
    :param output_dir:
    :param init_file_path:
    :param denoising_strength:
    :param positive_prompt:
    :param negative_prompt:
    :param steps:
    :param use_sampler:
    :param config_scale:
    :return:
    """
    request_socket = f'{url}/sdapi/v1/img2img'
    max_resolution = 512 * 1020
    size = [512, 768]
    if fit_original_size:
        p = get_image_ratio(init_file_path)
        size[1] = int(math.sqrt(max_resolution / p))
        size[0] = int(size[1] * p)

    if type(use_sampler) == str and use_sampler in samplers_list:
        usedSampler = use_sampler
    elif type(use_sampler) == int and 0 <= use_sampler < len(samplers_list):
        usedSampler = samplers_list[use_sampler]
    else:
        usedSampler = 'DPM++ SDE Karras'

    if steps is not int or steps > 32 or steps < 0:
        steps = 22

    if config_scale is not float or config_scale > 9 or config_scale < 5:
        config_scale = 7.0

    if type(positive_prompt) != str or not positive_prompt.strip():
        positive_prompt = 'super cute,loli girl,sfw:1.4'
    if type(negative_prompt) != str or not negative_prompt.strip():
        negative_prompt = 'EasyNegative,'

    if use_doll_lora:
        doll_lora_min = 0.08
        doll_lora_normal_max = 0.35
        doll_lora_emphasis_max = 0.8
        doll_lora = f'<lora:japaneseDollLikeness_v10:{uniform(doll_lora_min, doll_lora_normal_max)}>' \
                    f' <lora:koreanDollLikeness_v10:{uniform(doll_lora_min, doll_lora_emphasis_max)}> ' \
                    f'<lora:taiwanDollLikeness_v10:{uniform(doll_lora_min, doll_lora_normal_max)}> ' \
                    f'<lora:HinaIAmYoung22_zny10:0.06>'
        print(f'use doll lora')
        positive_prompt += doll_lora
    if not safe_mode:
        body_lora_max = 0.43
        body_lora_min = 0.06
        body_lora = f'<lora:hyperbreasts_v5Lora:{uniform(body_lora_min, body_lora_max)}>, ' \
                    f'<lora:hugeAssAndBoobs_v1:{uniform(body_lora_min, body_lora_max)}>'
        positive_prompt += body_lora

    payload = {
        "init_images": [

        ],
        "denoising_strength": denoising_strength,
        "prompt": positive_prompt,
        "negative_prompt": negative_prompt,
        "sampler_name": usedSampler,
        "subseed": -1,
        "subseed_strength": 0.90,
        "steps": steps,
        "cfg_scale": config_scale,
        "width": size[0],
        "height": size[1],
    }
    b64 = png_to_base64(init_file_path)

    print(f'going with [{init_file_path}]|prompt: {positive_prompt}')

    if use_control_net:
        # well, fixed using openpose
        print('using control net')
        control_net_kwargs = {"controlnet_units":
            [
                {
                    "module": "openpose",
                    "model": "control_sd15_openpose [fef5e48e]",
                }
            ]}
        control_net_kwargs = {'alwayson_scripts':
            {'ControlNet':
                {'args': [
                    {
                        "module": "openpose",
                        "model": "control_sd15_openpose [fef5e48e]",
                    }]
                }
            }
        }
        control_net_kwargs = {}
        # merge to payload
        payload.update(control_net_kwargs)
    print(f'{payload}')
    payload['init_images'] = [b64]
    response = requests.post(url=request_socket, json=payload)

    r = response.json()

    img_base64_list = r['images']
    saved_path_with_hash = single_task(img_base64_list, output_dir)
    return saved_path_with_hash


def png_to_base64(file_path):
    """

    :param file_path:
    :return:
    """
    assert file_path, 'file_path not valid'
    with open(file_path, 'rb') as f:
        data = f.read()
        return base64.b64encode(data).decode()


def get_image_ratio(image_path):
    """
    获取图片长宽比
    :param image_path: 图片路径
    :return: 图片长宽比
    """
    from PIL import Image
    img = Image.open(image_path)
    width, height = img.size
    return width / height


def single_task(img_base64_list: list[str], output_dir: str) -> list[str]:
    """

    :param img_base64_list:
    :param output_dir:
    :return:
    """
    output_img_path = []
    # TODO: there is a problem dealing with multiple images delivery
    print(f'receiving: [{len(img_base64_list)}] pics')
    for i in img_base64_list:
        image = Image.open(io.BytesIO(base64.b64decode(i.split(",", 1)[0])))

        png_payload = {
            "image": "data:image/png;base64," + i
        }
        response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)
        req_pnginfo = response2.json().get("info")
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("parameters", req_pnginfo)
        if len(req_pnginfo) > 34:
            label = slugify(req_pnginfo[0:34])
        else:
            label = slugify(req_pnginfo)

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        saved_path = f'{output_dir}/{label}.png'
        image.save(saved_path, pnginfo=pnginfo)
        saved_path_with_hash = rename_image_with_hash(saved_path)
        print(f'Saved at {saved_path_with_hash}')
        output_img_path.append(saved_path_with_hash)
    return output_img_path


def npl_reformat(natural_sentence: str, split_keyword: str = None, specify_batch_size: bool = False,
                 null_check: bool = True) -> object:
    """

    :param null_check:
    :return:
    :param specify_batch_size:
    :param split_keyword:
    :param natural_sentence:
    :return:
    """
    if null_check and natural_sentence == '':
        return ''

    batch_size = 1  # default
    if natural_sentence == split_keyword:
        return ''
    if split_keyword:
        word_pattern = split_keyword
    else:
        word_pattern = '(要|画个|画一个|来一个|来一碗|来个|给我|画)?'
    prompts = re.split(pattern=word_pattern, string=natural_sentence, maxsplit=1)

    if prompts[1] is None:
        return '', (batch_size if specify_batch_size else None)
    if specify_batch_size:
        batch_size_pattern = '(\d+(p|P))?'
        temp = re.findall(pattern=batch_size_pattern, string=natural_sentence)
        for match in temp:
            if match[0] != '':
                batch_size = int(match[0].strip(match[1]))
    print(f'splits: {prompts}')
    print(f'batch size: [{batch_size}]')
    print(prompts)
    if len(prompts) < 2:
        return '', (batch_size if specify_batch_size else None)
    else:
        return trans.translate('en', prompts[-1]), (batch_size if specify_batch_size else None)


if __name__ == '__main__':
    str = '+huge breasts+-not cute+wide hips+'
    # print(deAssembly(str))
    # print(sd_diff('./output/huge breasts.png'))

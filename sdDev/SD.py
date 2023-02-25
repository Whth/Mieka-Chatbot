import base64
import hashlib
import io
import os.path
import re
import sys

import requests
from PIL import Image, PngImagePlugin
from slugify import slugify

sys.path.append('..')
from baidu_translater.translater import Translater

# create API client with default sampler, steps.

# sd_api = webuiapi.WebUIApi(host='127.0.0.1', port=7860, sampler='DPM++ 2M Karras', steps=22)

trans = Translater()

samplers_list = [
    "Euler a", "LMS", "DPM++ SDE", "LMS Karras", "DPM2 a Karras", "DPM++ 2M Karras", "DPM++ SDE Karras", "DDIM",
    "PLMS"
]
url = "http://127.0.0.1:7860"
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
        temp = re.findall(pattern=batch_size_pattern, string=message)[0]
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


def sd_draw(positive_prompt: str = None, negative_prompt: str = None, steps: int = 22, size: list = [512, 768],
            use_sampler: str or int = 'DPM++ SDE Karras', config_scale: float = 7.2, output_dir='./output',
            use_korea_lora: bool = False, safe_mode: bool = True, face_restore: bool = False):
    """
    SD Ai drawing txt2img sd_api function
    :param safe_mode:
    :param face_restore:
    :param use_korea_lora:
    :param size:
    :param output_dir:
    :param positive_prompt:
    :param negative_prompt:
    :param steps:
    :param use_sampler:
    :param config_scale:
    :return:
    """
    korea_cmd = '<lora:koreanDollLikeness_v10:0.90>'

    if type(use_sampler) == str and use_sampler in samplers_list:
        usedSampler = use_sampler
    elif type(use_sampler) == int and 0 <= use_sampler < len(samplers_list):
        usedSampler = samplers_list[use_sampler]
    else:
        usedSampler = 'DPM++ SDE Karras'

    if steps is not int or steps > 30 or steps < 0:
        steps = 22

    if config_scale > 11 or config_scale < 5:
        config_scale = 7.0

    if type(positive_prompt) != str or not positive_prompt.strip():
        positive_prompt = 'pink hair:1.2,hair pin:1.2,girl,student uniform:1.4,collar:1.3,delicate and ' \
                          'shiny skin,white stocking:1.3,tie:1.3,on the street,unhappy,medium breasts,' \
                          'large breasts:0.3,watery eyes,beautiful eyes,delicate eys, luscious, ,high resolution,  ' \
                          '( best quality, ultra-detailed), (best illumination, best shadow, an extremely delicate ' \
                          'and beautiful), finely detail, depth of field, (shine), (airbrush), (sketch), ' \
                          '((three-dimensional)), perfect lighting,sun,sunny,masterpiece:1.4'
        safe_word = 'sfw:1.5' if safe_mode else ''

        positive_prompt = positive_prompt + safe_word
    if type(negative_prompt) != str or not negative_prompt.strip():
        negative_prompt = 'eyeshadow,eye pouches:1.3'
        safe_word = 'nsfw:1.3' if safe_mode else ''

        negative_prompt = negative_prompt + safe_word

    payload = {
        "prompt": positive_prompt + korea_cmd if use_korea_lora else positive_prompt,
        "negative_prompt": negative_prompt,
        "sampler_name": usedSampler,
        "steps": steps,
        "subseed": -1,
        "subseed_strength": 0.90,
        "restore_faces": face_restore,
        "cfg_scale": config_scale,
        "width": size[0],
        "height": size[1],
        "styles": [
            "inte fix",
        ]
    }
    print(payload)
    response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)
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


def sd_diff(init_file_path: str, positive_prompt: str = '', negative_prompt: str = '', steps: int = 22,
            use_sampler: str or int = "DDIM", denoising_strength: float = 0.7, config_scale: float = 7.5,
            output_dir: str = './output'):
    """
    SD Ai drawing img2img sd_api function
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
        positive_prompt = 'super cute neko,perfect lighting,sfw:1.4'
    if type(negative_prompt) != str or not negative_prompt.strip():
        negative_prompt = 'lowres, text, error, missing arms, missing legs, missing fingers, extra digit, ' \
                          'fewer digits, cropped, worst quality, low quality, jpeg artifacts, signature, watermark, ' \
                          'out of frame, extra fingers, mutated hands, (poorly drawn hands), (poorly drawn face), ' \
                          '(mutation), (deformed breasts), (ugly), blurry, (bad anatomy), (bad proportions), ' \
                          '(extra limbs), cloned face, flat color, monochrome, limited palette, skimpy, ' \
                          'nukige, cleavage, center opening, absolute cleavage, pornographic, erotic, eroge, hentai, ' \
                          'nsfw:1.2, ecchi, futanari, shota, shotacon loli, lolicon, bad-artist, bad-hands-5, ' \
                          'bad_quality,(EasyNegative), claws, umbrella, lowres, bad-artist, bad-hands-5,claws, ' \
                          'zoom out,'
    b64 = png_to_base64(init_file_path)

    payload = {
        "init_images": [
            b64
        ],
        "denoising_strength": denoising_strength,
        "prompt": positive_prompt,
        "negative_prompt": negative_prompt,
        "sampler_name": usedSampler,
        "subseed": -1,
        "subseed_strength": 0.90,
        "steps": steps,
        "cfg_scale": config_scale,
        "width": 512,
        "height": 768,
    }
    print(f'going with [{init_file_path}]|prompt: {positive_prompt}')
    print(f'{payload}')
    response = requests.post(url=f'{url}/sdapi/v1/img2img', json=payload)
    r = response.json()
    img_base64_list = r['images']
    saved_path_with_hash = single_task(img_base64_list, output_dir)
    return saved_path_with_hash


def single_task(img_base64_list: list[str], output_dir: str):
    """

    :param img_base64_list:
    :param output_dir:
    :return:
    """
    output_img_path = []
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
    if len(output_img_path) == 1:
        return output_img_path[0]

    return output_img_path


def npl_reformat(natural_sentence: str, split_keyword: str = None, specify_batch_size: bool = False) -> object:
    """

    :return:
    :param specify_batch_size:
    :param split_keyword:
    :param natural_sentence:
    :return:
    """
    batch_size = 1  # default
    if natural_sentence == split_keyword:
        return ''
    if split_keyword:
        word_pattern = split_keyword
    else:
        word_pattern = '(要|画个|画一个|来一个|来一碗|来个|给我|画)?'
    prompts = re.split(pattern=word_pattern, string=natural_sentence)
    if specify_batch_size:
        batch_size_pattern = '(\d+(p|P))?'
        temp = re.findall(pattern=batch_size_pattern, string=natural_sentence)
        for match in temp:
            if match[0] != '':
                batch_size = int(match[0].strip(match[1]))

    print(f'using NPL')
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

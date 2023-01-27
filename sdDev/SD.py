import sys

from paintingBot import trans

sys.path.append('.')
import os.path
import re
import requests
import io
import base64
from PIL import Image, PngImagePlugin
import base64

samplers_list = [
    "Euler a", "LMS", "DPM++ SDE", "LMS Karras", "DPM2 a Karras", "DPM++ 2M Karras", "DPM++ SDE Karras", "DDIM",
    "PLMS"
]
url = "http://127.0.0.1:7860"


def deAssembly(message: str):
    pos_pattern = '\+(.*?)\+'
    pos_prompt = ''
    for sec in re.findall(pattern=pos_pattern, string=message):
        pos_prompt += ' ' + sec

    neg_pattern = '\-(.*?)\-'
    neg_prompt = ''
    for sec in re.findall(pattern=neg_pattern, string=message):
        neg_prompt += ' ' + sec

    return pos_prompt, neg_prompt


def sd_darw(positive_prompt: str = None, negative_prompt: str = None, steps: int = 22,
            use_sampler: str or int = 'DPM++ SDE Karras', config_scale: float = 7.0, output_dir='./output'):
    """
    SD Ai drawing txt2img api function
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

    if steps is not int or steps > 30 or steps < 0:
        steps = 22

    if config_scale is not float or config_scale > 11 or config_scale < 5:
        config_scale = 7.0

    if type(positive_prompt) != str or not positive_prompt:
        positive_prompt = 'super cute neko,perfect lighting,sfw:1.4'
    if type(negative_prompt) != str or not negative_prompt:
        negative_prompt = '(worst quality, low quality:1.4),fix:0.8,exposed nipple,nsfw:1.4'

    payload = {
        "prompt": positive_prompt,
        "negative_prompt": negative_prompt,
        "sampler_name": usedSampler,
        "steps": steps,
        "cfg_scale": config_scale,
        "width": 512,
        "height": 768,
    }
    print(payload)
    response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)
    r = response.json()
    for i in r['images']:
        image = Image.open(io.BytesIO(base64.b64decode(i.split(",", 1)[0])))

        png_payload = {
            "image": "data:image/png;base64," + i
        }
        response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)

        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("parameters", response2.json().get("info"))
        if len(positive_prompt) > 34:
            label = positive_prompt[0:34]
        else:
            label = positive_prompt

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        saved_path = f'{output_dir}/{label}.png'
        print(f'Saved at {saved_path}')
        image.save(saved_path, pnginfo=pnginfo)
        return saved_path


def png_to_base64(file_path, log=False):
    assert file_path, 'file_path not valid'
    with open(file_path, 'rb') as f:
        data = f.read()
        return base64.b64encode(data).decode()


def sd_diff(init_file_path: str, positive_prompt: str = '', negative_prompt: str = '', steps: int = 22,
            use_sampler: str or int = "DDIM", denoising_strength: float = 0.7, config_scale: float = 7.0,
            output_dir: str = './output'):
    """
    SD Ai drawing img2img api function
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
        usedSampler = 'DDIM'

    if steps is not int or steps > 32 or steps < 0:
        steps = 22

    if config_scale is not float or config_scale > 9 or config_scale < 5:
        config_scale = 7.0

    if type(positive_prompt) != str or not positive_prompt:
        positive_prompt = 'super cute neko,perfect lighting,sfw:1.4'
    if type(negative_prompt) != str or not negative_prompt:
        negative_prompt = '(worst quality, low quality:1.4),fix:0.8,exposed nipple,nsfw:1.4'
    b64 = png_to_base64(init_file_path)

    payload = {
        "init_images": [
            b64
        ],
        "denoising_strength": denoising_strength,
        "prompt": positive_prompt,
        "negative_prompt": negative_prompt,
        "sampler_name": usedSampler,
        "steps": steps,
        "cfg_scale": config_scale,
        "width": 512,
        "height": 768,
    }
    print(f'going with [{init_file_path}]|prompt: {positive_prompt}')
    response = requests.post(url=f'{url}/sdapi/v1/img2img', json=payload)
    r = response.json()
    for i in r['images']:
        image = Image.open(io.BytesIO(base64.b64decode(i.split(",", 1)[0])))

        png_payload = {
            "image": "data:image/png;base64," + i
        }
        response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)

        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("parameters", response2.json().get("info"))
        if len(positive_prompt) > 34:
            label = positive_prompt[0:34]
        else:
            label = positive_prompt

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        saved_path = f'{output_dir}/{label}.png'
        print(f'Saved at {saved_path}')
        image.save(saved_path, pnginfo=pnginfo)
        return saved_path


if __name__ == '__main__':
    str = '+huge breasts+-not cute+wide hips+'
    # print(deAssembly(str))
    # print(sd_diff('./output/huge breasts.png'))


def NPL_reFormat(natural_sentence: str, split_keyword: str = None):
    """

    :param split_keyword:
    :param natural_sentence:
    :return:
    """
    if split_keyword:
        word_pattern = split_keyword
    else:
        word_pattern = '要|画个|画一个|来一个|来一碗|来个|给我'
    prompts = re.split(pattern=word_pattern, string=natural_sentence)
    print(prompts)
    if len(prompts) < 2:
        return ''
    else:
        return trans.translate('en', prompts[-1])

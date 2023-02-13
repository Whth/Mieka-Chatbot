import hashlib
import sys
import os.path
import re
import requests
import io
from PIL import Image, PngImagePlugin
import base64
from slugify import slugify

sys.path.append('..')
from baidu_translater.translater import Translater

trans = Translater()

samplers_list = [
    "Euler a", "LMS", "DPM++ SDE", "LMS Karras", "DPM2 a Karras", "DPM++ 2M Karras", "DPM++ SDE Karras", "DDIM",
    "PLMS"
]
url = "http://127.0.0.1:7860"


def deAssembly(message: str):
    """

    :param message:
    :return:
    """
    if message == "":
        return '', ''
    pos_pattern = '\+(.*?)\+'
    pos_prompt = ''
    for sec in re.findall(pattern=pos_pattern, string=message):
        pos_prompt += ' ' + sec

    neg_pattern = '\-(.*?)\-'
    neg_prompt = ''
    for sec in re.findall(pattern=neg_pattern, string=message):
        neg_prompt += ' ' + sec

    return pos_prompt, neg_prompt


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


def sd_draw(positive_prompt: str = None, negative_prompt: str = None, steps: int = 22,size:list=[512,768],
            use_sampler: str or int = 'DPM++ SDE Karras', config_scale: float = 7.2, output_dir='./output'):
    """
    SD Ai drawing txt2img api function
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

    if steps is not int or steps > 30 or steps < 0:
        steps = 22

    if config_scale is not float or config_scale > 11 or config_scale < 5:
        config_scale = 7.0

    if type(positive_prompt) != str or not positive_prompt.strip():
        positive_prompt = 'pink hair,hair pin,girl,student uniform,tank cloth,collar,stylish' \
                          ',white stocking,tie,hair behind ear,sfw:1.4,on the street,unhappy'
    if type(negative_prompt) != str or not negative_prompt.strip():
        negative_prompt = 'nsfw:1.2, EasyNegative,bad-hands-5,claws,zoom out,'

    payload = {
        "prompt": positive_prompt,
        "negative_prompt": negative_prompt,
        "sampler_name": usedSampler,
        "steps": steps,
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
    for i in r['images']:
        image = Image.open(io.BytesIO(base64.b64decode(i.split(",", 1)[0])))

        png_payload = {
            "image": "data:image/png;base64," + i
        }
        response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)

        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("parameters", response2.json().get("info"))
        if len(positive_prompt) > 34:
            # prevent bad path prompts
            label = slugify(positive_prompt[0:34])
        else:
            label = slugify(positive_prompt)

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        saved_path = f'{output_dir}/{label}.png'

        image.save(saved_path, pnginfo=pnginfo)
        saved_path_with_hash = rename_image_with_hash(saved_path)
        print(f'Saved at {saved_path_with_hash}')
        return saved_path_with_hash


def png_to_base64(file_path, log=False):
    assert file_path, 'file_path not valid'
    with open(file_path, 'rb') as f:
        data = f.read()
        return base64.b64encode(data).decode()


def sd_diff(init_file_path: str, positive_prompt: str = '', negative_prompt: str = '', steps: int = 22,
            use_sampler: str or int = "DDIM", denoising_strength: float = 0.7, config_scale: float = 7.5,
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
        "steps": steps,
        "cfg_scale": config_scale,
        "width": 512,
        "height": 768,
    }
    print(f'going with [{init_file_path}]|prompt: {positive_prompt}')
    print(f'{payload}')
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
            label = slugify(positive_prompt[0:34])
        else:
            label = slugify(positive_prompt)

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        saved_path = f'{output_dir}/{str(label)}.png'
        image.save(saved_path, pnginfo=pnginfo)
        saved_path_with_hash = rename_image_with_hash(saved_path)
        print(f'Saved at {saved_path_with_hash}')
        return saved_path_with_hash


def NPL_Reformat(natural_sentence: str, split_keyword: str = None):
    """

    :param split_keyword:
    :param natural_sentence:
    :return:
    """
    if natural_sentence == split_keyword:
        return ''
    if split_keyword:
        word_pattern = split_keyword
    else:
        word_pattern = '要|画个|画一个|来一个|来一碗|来个|给我|画'
    prompts = re.split(pattern=word_pattern, string=natural_sentence)
    print(prompts)
    if len(prompts) < 2:
        return ''
    else:
        return trans.translate('en', prompts[-1])


if __name__ == '__main__':
    str = '+huge breasts+-not cute+wide hips+'
    # print(deAssembly(str))
    # print(sd_diff('./output/huge breasts.png'))

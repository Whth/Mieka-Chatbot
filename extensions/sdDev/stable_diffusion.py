# TODO use fatory mode,build config,
import base64
import io
import os.path
from typing import NamedTuple, List, Dict

import aiohttp
import requests
from PIL import Image, PngImagePlugin
from slugify import slugify

from extensions.sdDev.api import (
    API_PNG_INFO,
    API_TXT2IMG,
    API_IMG2IMG,
    INIT_IMAGES_KEY,
    IMAGE_KEY,
    IMAGES_KEY,
    PNG_INFO_KEY,
)
from modules.file_manager import rename_image_with_hash, img_to_base64

DEFAULT_NEGATIVE_PROMPT = "loathed,low resolution,porn,NSFW,strange shaped finger,cropped,panties visible"

DEFAULT_POSITIVE_PROMPT = (
    "modern art,student uniform,white shirt,short blue skirt,white tights,joshi,JK,1girl:1.2,solo,upper body,"
    "shy,extremely cute,lovely,"
    "beautiful,expressionless,cool girl,medium breasts,"
    "thighs,thin torso,masterpiece,wonderful art,high resolution,hair ornament,strips,body curve,hair,SFW:1.3,"
)


class DiffusionParser(NamedTuple):
    """
    use to parse config
    """

    prompt: str = DEFAULT_POSITIVE_PROMPT
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT
    styles: List[str] = []
    seed: int = -1
    sampler_name: str = "UniPC"
    steps: int = 18
    cfg_scale: float = 6.9
    width: int = 512
    height: int = 768

    enable_hr: bool = False


class HiResParser(NamedTuple):
    """
    use to parse hires config
    """

    denoising_strength: float = 0.69
    hr_scale: float = 1.3
    hr_upscaler: str = "Latent"
    # hr_checkpoint_name: string
    # hr_sampler_name: string
    # hr_prompt:
    # hr_negative_prompt:


class ControlNetParser(NamedTuple):
    """
    containing control net parsers
    """

    enabled: bool = False
    image: str = ""
    module: str = ""
    model: str = ""
    weight: float = 1.0
    guidance: float = 1.0
    guidance_start: float = 0.0
    guidance_end: float = 1.0
    guess_mode: bool = False


class StableDiffusionApp(object):
    """
    class that implements the basic diffusion api
    """

    def __init__(self, host_url: str):
        self._host_url = host_url

    async def txt2img(
        self,
        output_dir: str,
        diffusion_parameters: DiffusionParser = DiffusionParser(),
        HiRes_parameters: HiResParser = HiResParser(),
    ) -> List[str]:
        """
        Converts text to image and saves the generated images to the specified output directory.

        Args:
            output_dir (str): The directory where the generated images will be saved.
            diffusion_parameters (DiffusionParser, optional): An optional instance of the DiffusionParser class
                that contains the diffusion parameters.
            HiRes_parameters (HiResParser, optional): An optional instance of the HiResParser class that contains
                the Hi-Res parameters. Defaults to HiResParser().

        Returns:
            List[str]: A list of image filenames that were saved.

        """

        pay_load: Dict = {}
        pay_load.update(diffusion_parameters._asdict())
        if diffusion_parameters.enable_hr:
            pay_load.update(HiRes_parameters._asdict())

        async with aiohttp.ClientSession() as session:
            response = await session.post(f"{self._host_url}/{API_TXT2IMG}", json=pay_load)
            response_payload: Dict = await response.json()

        img_base64: List[str] = extract_png_from_payload(response_payload)

        return save_base64_img_with_hash(img_base64_list=img_base64, output_dir=output_dir, host_url=self._host_url)

    async def img2img(
        self, image_path: str, output_dir: str, diffusion_parameters: DiffusionParser = DiffusionParser()
    ) -> List[str]:
        """
        Converts image to image and saves the generated images to the specified output directory.
        Args:
            diffusion_parameters ():
            image_path ():
            output_dir ():

        Returns:

        """

        pay_load: Dict = {}
        pay_load.update(diffusion_parameters._asdict())

        png_pay_load: Dict = {INIT_IMAGES_KEY: [img_to_base64(image_path)]}
        pay_load.update(png_pay_load)

        async with aiohttp.ClientSession() as session:
            response = await session.post(f"{self._host_url}/{API_IMG2IMG}", json=pay_load)
            response_payload: Dict = await response.json()
        img_base64: List[str] = extract_png_from_payload(response_payload)

        return save_base64_img_with_hash(img_base64_list=img_base64, output_dir=output_dir, host_url=self._host_url)


def extract_png_from_payload(payload: Dict) -> List[str]:
    """
    Should extract a list of png encoded of base64

    Args:
        payload (Dict): the response payload

    Returns:

    """
    # TODO this function may not as necessary
    if IMAGES_KEY not in payload:
        raise KeyError(f"{IMAGES_KEY} not found in payload")
    img_base64 = payload.get(IMAGES_KEY)
    return img_base64


def save_base64_img_with_hash(
    img_base64_list: List[str], output_dir: str, host_url: str, max_file_name_length: int = 34
) -> List[str]:
    """
    Process a list of base64-encoded images and save them as PNG files in the specified output directory.

    :param img_base64_list: A list of base64-encoded images.
    :param output_dir: The directory where the output images will be saved.
    :param host_url: The URL of the host where the API is running.
    :param max_file_name_length: The maximum length of the file name.
    :return: A list of paths to the saved images.
    """

    output_img_paths: List[str] = []

    for img_base64 in img_base64_list:
        # Decode the base64-encoded image

        # Make a POST request to get PNG info
        response = requests.post(url=f"{host_url}/{API_PNG_INFO}", json={IMAGE_KEY: img_base64})

        req_png_info = response.json().get(PNG_INFO_KEY)

        # Create a label for the saved image
        label = slugify(
            req_png_info[:max_file_name_length] if len(req_png_info) > max_file_name_length else req_png_info
        )

        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        # Save the image with the PNG info
        saved_path = f"{output_dir}/{label}.png"
        png_info = PngImagePlugin.PngInfo()
        png_info.add_text("parameters", req_png_info)
        image = Image.open(io.BytesIO(base64.b64decode(img_base64)))
        image.save(saved_path, pnginfo=png_info)

        # Rename the saved image with a hash
        saved_path_with_hash = rename_image_with_hash(saved_path)

        # Add the path to the list of output image paths
        output_img_paths.append(saved_path_with_hash)

    return output_img_paths


def get_image_ratio(image_path):
    """
    获取图片长宽比
    :param image_path: 图片路径
    :return: 图片长宽比
    """

    img = Image.open(image_path)
    width, height = img.size
    return width / height

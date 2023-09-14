from typing import NamedTuple, Dict, List

import aiohttp

from .api import API_CONTROLNET_MODEL_LIST, API_CONTROLNET_MODULE_LIST, API_CONTROLNET_DETECT, CONTROLNET_KEY, ARGS_KEY


class ControlNetUnit(NamedTuple):
    """
    containing control net parsers
    detailed api wiki see
    https://github.com/Mikubill/sd-webui-controlnet/wiki/API#integrating-sdapiv12img
    """

    input_image: str
    module: str
    model: str
    resize_mode: int = 1
    """
    resize_mode : how to resize the input image so as to fit the output resolution of the generation. defaults to "Scale to Fit (Inner Fit)". Accepted values:
    0 or "Just Resize" : simply resize the image to the target width/height
    1 or "Scale to Fit (Inner Fit)" : scale and crop to fit smallest dimension. preserves proportions.
    2 or "Envelope (Outer Fit)" : scale to fit largest dimension. preserves proportions.
    """
    processor_res: int = 64
    weight: float = 1.0
    guidance: float = 1.0
    guidance_start: float = 0.0
    guidance_end: float = 1.0
    control_mode: int = 0
    """
    control_mode : see the related issue for usage. defaults to 0. Accepted values:
    0 or "Balanced" : balanced, no preference between prompt and control model
    1 or "My prompt is more important" : the prompt has more impact than the model
    2 or "ControlNet is more important" : the controlnet model has more impact than the prompt
    """


class Controlnet(object):
    @staticmethod
    async def __async_get(url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

    @staticmethod
    async def __async_post(url: str, payload: Dict):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                return await response.json()

    def __init__(self, host_url: str):
        self._host_url = host_url

    async def get_model_list(self) -> Dict:
        return await self.__async_get(f"{self._host_url}/{API_CONTROLNET_MODEL_LIST}")

    async def get_module_list(self) -> Dict:
        return await self.__async_get(f"{self._host_url}/{API_CONTROLNET_MODULE_LIST}")

    async def detect(self, payload: Dict) -> Dict:
        return await self.__async_post(f"{self._host_url}/{API_CONTROLNET_DETECT}", payload=payload)


def make_payload(units: List[ControlNetUnit]) -> Dict:
    unit_seq: List[Dict] = []
    for unit in units:
        unit: ControlNetUnit
        unit_seq.append(unit._asdict())
    return {CONTROLNET_KEY: {ARGS_KEY: unit_seq}}

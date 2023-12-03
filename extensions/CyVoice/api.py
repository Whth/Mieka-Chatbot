import re
from typing import Dict, List

from aiohttp import ClientSession
from pydantic import BaseModel

from modules.shared import get_pwd

TIMEOUT = 30


class CVData(BaseModel):
    text: str
    id: int
    format: str
    lang: str
    length: float
    noise: float
    noisew: float
    max: int


class VITS(object):
    __API_VOICE_APP_KEY_WORD: str = "voice"
    __API_REQUEST_SPEAKERS_KEY_WORD: str = "speakers"
    base: str = "http://127.0.0.1:23456"

    @classmethod
    async def voice_speakers(cls) -> str:
        """
        Fetches the voice speakers data from the API and returns a formatted string.

        Returns:
            str: The formatted string containing the voice speakers data.
        """
        # Replace with the actual base URL of the API

        url = f"{cls.base}/{cls.__API_VOICE_APP_KEY_WORD}/{cls.__API_REQUEST_SPEAKERS_KEY_WORD}"
        # Construct the URL for fetching voice speakers data

        async with ClientSession() as session:
            async with session.get(url=url, timeout=TIMEOUT) as response:
                json: Dict[str, List[Dict[str]]] = await response.json()  # Fetch the JSON response

        for model_type in json:
            temp_string = f"{model_type}:\n\n"  # Add the model type to the string
            for speakers in json[model_type]:
                temp_string += (
                    f" ID: {speakers.get('id'):<4}|{speakers.get('name')}\n"  # Add the speaker details to the string
                )
                yield temp_string

    @classmethod
    async def get_voice_speakers(cls):
        speaker_names: List[str] = []
        url = f"{cls.base}/{cls.__API_VOICE_APP_KEY_WORD}/{cls.__API_REQUEST_SPEAKERS_KEY_WORD}"
        # Construct the URL for fetching voice speakers data

        async with ClientSession() as session:
            async with session.get(url=url, timeout=TIMEOUT) as response:
                json: Dict[str, List[Dict[str]]] = await response.json()  # Fetch the JSON response

        for model_type in json:
            for speakers in json[model_type]:
                speaker_names.append(speakers.get("name"))

        return speaker_names  # Return the formatted string containing the voice speakers data

    # 语音合成 voice vits

    @classmethod
    async def voice_vits(
        cls,
        text,
        cv_id=0,
        file_format="wav",
        lang="auto",
        length=1.0,
        noise=0.667,
        noise_w=0.8,
        max_seg_length=50,
        save_dir=get_pwd(),
    ) -> str:
        """
        Asynchronous method that generates a voice file using the Voice API.

        Args:
            text (str): The text that will be used to generate the voice file.
            cv_id (int, optional): The ID of the CV. Defaults to 0.
            file_format (str, optional): The format of the voice file. Defaults to "wav".
            lang (str, optional): The language of the voice. Defaults to "auto".
            length (int, optional): The length of the voice file in seconds. Defaults to 1.
            noise (float, optional): The level of noise to be added to the voice file. Defaults to 0.667.
            noise_w (float, optional): The level of noise weight to be added to the voice file. Defaults to 0.8.
            max_seg_length (int, optional): The maximum temperature. Defaults to 50.
            save_dir (str, optional): The directory where the voice file will be saved.
                Defaults to the current working directory.

        Examples:
            >>> VITS.voice_vits(text="hello world", cv_id=0, file_format="wav", lang="auto", length=1, noise=0.667, noise_w=0.8, max_seg_length=50, save_dir=get_pwd())

        Returns:
            str: The path of the saved voice file.
        """
        # Prepare the request body
        cvdata = CVData(
            text=text,
            id=cv_id,
            format=file_format,
            lang=lang,
            length=length,
            noise=noise,
            noisew=noise_w,
            max=max_seg_length,
        )
        # Construct the API endpoint URL
        url = f"{cls.base}/{cls.__API_VOICE_APP_KEY_WORD}"

        # Send the POST request to the API and get the response
        async with ClientSession() as session:
            async with session.post(url=url, json=cvdata.dict(), timeout=TIMEOUT) as response:
                # Extract the filename from the response headers
                fname = re.findall("filename=(.+)", response.headers["Content-Disposition"])[0]

                # Create the path where the voice file will be saved
                path = f"{save_dir}/{fname}"

                # Save the voice file
                with open(path, "wb") as f:
                    f.write(await response.read())

        return path

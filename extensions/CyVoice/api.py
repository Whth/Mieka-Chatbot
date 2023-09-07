import os
import random
import re
import string
from typing import Dict, List

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

__API_REQUEST_SPEAKERS_KEY_WORD = "speakers"
__API_REQUEST_VITS_KEY_WORD = "vits"
__API_REQUEST_READ_TEXT_KEY_WORD = "text"
__API_REQUEST_CV_INDEX_KEY_WORD = "id"
abs_path = os.path.dirname(__file__)
base = "http://127.0.0.1:23456"


def voice_speakers() -> str:
    """
    Fetches the voice speakers data from the API and returns a formatted string.

    Returns:
        str: The formatted string containing the voice speakers data.
    """
    # Replace with the actual base URL of the API

    url = f"{base}/voice/speakers"  # Construct the URL for fetching voice speakers data
    temp_string: str = ""

    json: Dict[str, List[Dict[str]]] = requests.get(url=url).json()  # Fetch the JSON response

    for model_type in json:
        temp_string += f"{model_type}:\n\n"  # Add the model type to the string
        for speakers in json[model_type]:
            temp_string += (
                f" ID: {speakers.get('id'):<4}|{speakers.get('name')}\n"  # Add the speaker details to the string
            )
        temp_string += "-----------------\n"  # Add a separator after each model type

    return temp_string  # Return the formatted string containing the voice speakers data


def get_voice_speakers():
    speaker_names: List[str] = []
    url = f"{base}/voice/speakers"  # Construct the URL for fetching voice speakers data
    json: Dict[str, List[Dict[str]]] = requests.get(url=url).json()  # Fetch the JSON response

    for model_type in json:
        for speakers in json[model_type]:
            speaker_names.append(speakers.get("name"))

    return speaker_names  # Return the formatted string containing the voice speakers data


# 语音合成 voice vits


def voice_vits(
    text, id=0, format="wav", lang="auto", length=1, noise=0.667, noisew=0.8, max=50, save_dir=os.path.dirname(__file__)
):
    """
    Sends a text to the voice conversion API and saves the resulting audio file.

    Args:
        text (str): The text to convert to speech.
        id (int, optional): The ID of the audio file. Defaults to 0.
        format (str, optional): The format of the audio file. Defaults to "wav".
        lang (str, optional): The language of the text. Defaults to "auto".
        length (float, optional): The length of the audio file in seconds. Defaults to 1.
        noise (float, optional): The amount of noise to add to the audio. Defaults to 0.667.
        noisew (float, optional): The intensity of the added noise. Defaults to 0.8.
        max (int, optional): The maximum number of characters in the text. Defaults to 50.

    Returns:
        str: The path to the saved audio file.
    """
    # Prepare the fields and boundary for the multipart form data
    fields = {
        "text": text,
        "id": str(id),
        "format": format,
        "lang": lang,
        "length": str(length),
        "noise": str(noise),
        "noisew": str(noisew),
        "max": str(max),
    }
    boundary = "----VoiceConversionFormBoundary" + "".join(random.sample(string.ascii_letters + string.digits, 16))

    # Create the multipart encoder and set the headers
    m = MultipartEncoder(fields=fields, boundary=boundary)
    headers = {"Content-Type": m.content_type}

    # Make the API request, response is raw binary
    url = f"{base}/voice"
    res = requests.post(url=url, data=m, headers=headers)

    # Extract the file name from the response headers
    fname = re.findall("filename=(.+)", res.headers["Content-Disposition"])[0]
    path = f"{save_dir}/{fname}"

    # Save the audio file
    with open(path, "wb") as f:
        f.write(res.content)

    return path


# print(voice_speakers())
# voice_vits("あなたのことが好きです")

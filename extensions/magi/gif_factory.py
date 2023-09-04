import os.path
from typing import Sequence, List

import PIL.Image as Image


class GifFactory(object):
    """
    create gif
    """

    @staticmethod
    def from_img_sequence(img_sequence: Sequence[Image.Image], save_path: str, duration: float):
        """
        Save a sequence of images as an animated GIF.

        Args:
            img_sequence (Sequence[Image.Image]): The sequence of images to save.
            save_path (str): The path to save the animated GIF.
            duration (float): The duration (in seconds) to display each frame.

        Returns:
            None
        """
        # Create the directory if it doesn't exist
        if not os.path.exists(os.path.dirname(save_path)):
            os.makedirs(os.path.dirname(save_path))

        # Save the images as an animated GIF
        img_sequence[0].save(save_path, save_all=True, append_images=img_sequence, duration=duration)

    @staticmethod
    def append_jpg_to_gif(
        jpg_path: str, jpg_count: int, gif_path: str, gif_count: int, output_path: str, duration: float
    ):
        """
        Appends a specified number of JPEG frames to a GIF file and saves it to the output path with the specified duration.

        Args:
            jpg_path (str): The path to the JPEG file.
            jpg_count (int): The number of JPEG frames to append.
            gif_path (str): The path to the GIF file.
            gif_count (int): The number of times to repeat the GIF frames.
            output_path (str): The path to save the output GIF file.
            duration (float): The duration of each frame in the output GIF file.

        Returns:
            None
        """
        gif_frames = GifFactory.extract_frames_from_gif(gif_path) * gif_count
        jpg_frames = [Image.open(jpg_path)] * jpg_count
        GifFactory.from_img_sequence(jpg_frames + gif_frames, output_path, duration)

    @staticmethod
    def extract_frames_from_gif(gif_path: str) -> List[Image.Image]:
        """
        Extracts frames from a GIF file.

        Args:
            gif_path (str): The path to the GIF file.

        Returns:
            List[Image.Image]: A list of Image objects representing the frames of the GIF.
        """
        frames: List[Image.Image] = []
        gif_file = Image.open(gif_path)
        for frame_index in range(gif_file.n_frames):
            gif_file.seek(frame_index)
            frames.append(gif_file.copy())
        return frames

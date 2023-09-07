import os
import random
import string

from modules.plugin_base import AbstractPlugin

__all__ = ["HeartBeat"]


class HeartBeat(AbstractPlugin):
    CONFIG_HEART_BEAT_INTERVAL = "HeartBeatInterval"

    def _get_config_parent_dir(self) -> str:
        return os.path.abspath(os.path.dirname(__file__))

    @classmethod
    def get_plugin_name(cls) -> str:
        return "HeartBeat"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "beats the heart by sending message periodically"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(self.CONFIG_HEART_BEAT_INTERVAL, 40)

    def install(self):
        self.__register_all_config()
        self._config_registry.load_config()
        from graia.scheduler import GraiaScheduler, timers
        from datetime import datetime

        ariadne_app = self._ariadne_app
        scheduler: GraiaScheduler = ariadne_app.create(GraiaScheduler)

        @scheduler.schedule(
            timer=timers.every_custom_minutes(self._config_registry.get_config(self.CONFIG_HEART_BEAT_INTERVAL))
        )
        async def heart_beat():
            """
            Asynchronous function that sends a heart beat message.

            This function is decorated with `@scheduler.schedule` and is scheduled to run at a specific interval defined by the value returned by `self._config_registry.get_config(self.CONFIG_HEART_BEAT_INTERVAL)`.

            Parameters:
                None.

            Returns:
                None.
            """
            await ariadne_app.send_friend_message(
                ariadne_app.account,
                message=f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
                f"HEART BEAT\n"
                f"CODE: {generate_random_string(10)}",
            )


def generate_random_string(length: int) -> str:
    """
    Generate a random string of a specified length.

    Parameters:
        length (int): The desired length of the random string.

    Returns:
        str: A random string consisting of letters from the ASCII alphabet.
    """
    letters = string.ascii_letters
    return "".join(random.choice(letters) for _ in range(length))

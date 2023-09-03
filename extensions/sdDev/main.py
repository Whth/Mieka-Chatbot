import os

from modules.plugin_base import AbstractPlugin

__all__ = ["StableDiffusionPlugin"]


class StableDiffusionPlugin(AbstractPlugin):
    OUTPUT_PATH = "output"
    TXT2IMG_PATH = f"{OUTPUT_PATH}/txt2img"
    IMG2IMG_PATH = f"{OUTPUT_PATH}/img2img"
    IMG_TEMP_PATH = "temp"

    CONFIG_DETECTED_KEYWORD = "detected_keyword"
    CONFIG_SD_HOST = "sd_host"

    def _get_config_parent_dir(self) -> str:
        return os.path.abspath(os.path.dirname(__file__))

    @classmethod
    def get_plugin_name(cls) -> str:
        return "stable_diffusion"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "stable diffusion plugin"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(self.CONFIG_DETECTED_KEYWORD, "+")
        self._config_registry.register_config(self.CONFIG_SD_HOST, "http://localhost:7860")

    def install(self):
        self.__register_all_config()

        # from .SD import sd_draw,sd_diff
        #
        # async def groupDiffusion(
        #         app: Ariadne,
        #         group: Group,
        #         chain: MessageChain,
        #         neg_prompts: str,
        #         pos_prompts: str,
        #         use_reward: bool = True,
        #         batch_size: int = 1,
        #         use_doll_lora: bool = True,
        #         safe_mode: bool = True,
        #         use_body_lora: bool = False,
        # ):
        #     """
        #
        #     :param safe_mode:
        #     :param use_reward:
        #     :param use_body_lora:
        #     :param use_doll_lora:
        #     :param batch_size:
        #     :param app:
        #     :param member:
        #     :param group:
        #     :param chain:
        #     :param neg_prompts:
        #     :param pos_prompts:
        #     :return:
        #     """
        #
        #     if Image in chain:
        #         print("using img2img")
        #         # 如果包含图片则使用img2img
        #         img_path = download_image(chain[Image, 1][0].url, save_dir="./friend_temp")
        #         generated_path = sd_diff(
        #             init_file_path=img_path,
        #             positive_prompt=pos_prompts,
        #             negative_prompt=neg_prompts,
        #             use_control_net=False,
        #         )
        #
        #         await app.send_message(group, message_constructor(finishResponseList, generated_path))
        #     else:
        #         print("using txt2img")
        #         print(f"going with [{batch_size}] pictures")
        #         size = [542, 864]
        #         if pos_prompts != "" and "hair" not in pos_prompts:
        #             categories = ["hair"]
        #             pos_prompts += get_random_prompts(categories=categories)
        #         for _ in range(batch_size):
        #             generated_path = sd_draw(
        #                 positive_prompt=pos_prompts,
        #                 negative_prompt=neg_prompts,
        #                 safe_mode=safe_mode,
        #                 size=size,
        #                 use_doll_lora=use_doll_lora,
        #                 use_body_lora=use_body_lora,
        #             )
        #
        #             await app.send_message(group, message_constructor(finishResponseList, generated_path))
        #
        #         if random.random() < REWARD_RATE and use_reward:
        #             print(f"with REWARD_RATE: {REWARD_RATE}|REWARDED")
        #             size = [542, 864]
        #             generated_path_reward = sd_draw(
        #                 positive_prompt=pos_prompts,
        #                 negative_prompt=neg_prompts,
        #                 safe_mode=safe_mode,
        #                 size=size,
        #                 use_doll_lora=use_doll_lora,
        #                 use_body_lora=use_body_lora,
        #             )
        #             await app.send_message(group, message_constructor(rewardResponseList, generated_path_reward))

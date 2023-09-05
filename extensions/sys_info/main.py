import os

from modules.plugin_base import AbstractPlugin

__all__ = ["SysInfo"]


class SysInfo(AbstractPlugin):
    CONFIG_DETECTED_KEYWORD = "detected_keyword"

    def _get_config_parent_dir(self) -> str:
        return os.path.abspath(os.path.dirname(__file__))

    @classmethod
    def get_plugin_name(cls) -> str:
        return "System Info"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "plugin plugin that allow some hardware info interrogating operations"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(self.CONFIG_DETECTED_KEYWORD, "sys info")

    def install(self):
        from graia.ariadne.message.parser.base import ContainKeyword, MentionMe
        from graia.ariadne.model import Group
        import psutil
        from .util import get_gpu_info

        self.__register_all_config()
        self._config_registry.load_config()
        ariadne_app = self._ariadne_app
        bord_cast = ariadne_app.broadcast

        @bord_cast.receiver(
            "GroupMessage",
            decorators=[
                MentionMe(),
                ContainKeyword(keyword=self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD)),
            ],
        )
        async def get_sys_info(group: Group):
            """
            This function is a receiver for the "GroupMessage" event. It retrieves system information including CPU, memory, disk, and GPU information and sends it as a message to the specified group.

            Parameters:
                group (Group): The group to send the system information message to.

            Returns:
                None
            """
            # 获取CPU信息

            cpu_info_str = (
                f"CPU信息：\n"
                f"\t物理核心数：{psutil.cpu_count()}\n"
                f"\t逻辑核心数：{psutil.cpu_count(True)}\n"
                f"\tCPU频率：{psutil.cpu_freq().max} MHz\n"
                f"\t占用率: {psutil.cpu_percent()}%"
            )

            # 获取内存信息
            mem_info = psutil.virtual_memory()
            mem_info_str = (
                f"内存信息：\n"
                f"\t总内存：{mem_info.total / 1024 / 1024 / 1024:.2f} GB\n"
                f"\t已使用内存：{mem_info.used / 1024 / 1024 / 1024:.2f} GB\n"
                f"\t可用内存：{mem_info.available / 1024 / 1024 / 1024:.2f} GB\n"
                f"\t内存使用率：{mem_info.percent}%"
            )

            # 获取磁盘信息
            disk_info = psutil.disk_usage("/")
            disk_info_str = (
                f"磁盘信息：\n"
                f"\t总磁盘空间：{disk_info.total / 1024 / 1024 / 1024:.2f} GB\n"
                f"\t已使用磁盘空间：{disk_info.used / 1024 / 1024 / 1024:.2f} GB\n"
                f"\t可用磁盘空间：{disk_info.free / 1024 / 1024 / 1024:.2f} GB\n"
                f"\t磁盘使用率：{disk_info.percent}%"
            )

            # 合并为一个字符串
            hardware_info = f"{cpu_info_str}\n\n{mem_info_str}\n\n{disk_info_str}\n\n{get_gpu_info()}"

            await ariadne_app.send_message(group, message=hardware_info)

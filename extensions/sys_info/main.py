import os

from modules.plugin_base import AbstractPlugin

__all__ = ["SysInfo"]


class SysInfo(AbstractPlugin):
    __INFO_CMD = "info"
    __INFO_CPU_CMD = "cpu"
    __INFO_GPU_CMD = "gpu"
    __INFO_MEM_CMD = "mem"
    __INFO_DISK_CMD = "disk"
    __INFO_ALL_CMD = "all"

    __SYS_HELP = "help"
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
        self._config_registry.register_config(self.CONFIG_DETECTED_KEYWORD, "sys")

    def install(self):
        from graia.ariadne.message.chain import MessageChain
        from graia.ariadne.message.parser.base import DetectPrefix
        from graia.ariadne.model import Group

        from .util import get_gpu_info, get_mem_info, get_cpu_info, get_all_info, get_disk_info
        from modules.config_utils import ConfigClient

        self.__register_all_config()
        self._config_registry.load_config()

        def get_all_cmd_info() -> str:
            temp_string = "Available CMD:\n"
            for cmd in ConfigClient.all_available_cmd():
                temp_string += f"\t{cmd}\n"
            return temp_string

        tree = {
            self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD): {
                self.__INFO_CMD: {
                    self.__INFO_CPU_CMD: get_cpu_info,
                    self.__INFO_MEM_CMD: get_mem_info,
                    self.__INFO_DISK_CMD: get_disk_info,
                    self.__INFO_GPU_CMD: get_gpu_info,
                    self.__INFO_ALL_CMD: get_all_info,
                },
                self.__SYS_HELP: get_all_cmd_info,
            }
        }
        client = ConfigClient(tree)

        ariadne_app = self._ariadne_app
        bord_cast = ariadne_app.broadcast

        @bord_cast.receiver(
            "GroupMessage",
            decorators=[
                DetectPrefix(prefix=self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD)),
            ],
        )
        async def sys_client(group: Group, message: MessageChain):
            output_string = client.interpret(str(message))

            await ariadne_app.send_message(group, message=output_string)

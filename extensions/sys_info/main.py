import os

from modules.plugin_base import AbstractPlugin

__all__ = ["SysInfo"]


class SysInfo(AbstractPlugin):
    __INFO_CPU_CMD = "cpu"
    __INFO_GPU_CMD = "gpu"
    __INFO_MEM_CMD = "mem"
    __INFO_DISK_CMD = "disk"
    __INFO_ALL_CMD = "all"

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
        from .util import get_gpu_info, get_mem_info, get_cpu_info, get_all_info, get_disk_info
        from modules.cmd import NameSpaceNode, ExecutableNode

        self.__register_all_config()
        self._config_registry.load_config()

        tree = NameSpaceNode(
            name=self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD),
            help_message="system status monitor,allow some hardware info interrogating operations",
            children_node=[
                ExecutableNode(name=self.__INFO_CPU_CMD, help_message="get cpu info", source=get_cpu_info),
                ExecutableNode(name=self.__INFO_MEM_CMD, help_message="get memory info", source=get_mem_info),
                ExecutableNode(name=self.__INFO_DISK_CMD, help_message="get disk info", source=get_disk_info),
                ExecutableNode(name=self.__INFO_GPU_CMD, help_message="get gpu info", source=get_gpu_info),
                ExecutableNode(name=self.__INFO_ALL_CMD, help_message="get all info", source=get_all_info),
            ],
        )

        self._root_namespace_node.add_node(tree, [])

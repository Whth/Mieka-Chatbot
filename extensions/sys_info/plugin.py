import os

from modules.plugin_base import AbstractPlugin


class SysInfo(AbstractPlugin):
    __INFO_CPU_CMD = "cpu"
    __INFO_GPU_CMD = "gpu"
    __INFO_MEM_CMD = "mem"
    __INFO_DISK_CMD = "disk"
    __INFO_ALL_CMD = "all"

    CONFIG_DETECTED_KEYWORD = "detected_keyword"

    DefaultConfig = {CONFIG_DETECTED_KEYWORD: "sys"}

    @classmethod
    def _get_config_dir(cls) -> str:
        return os.path.abspath(os.path.dirname(__file__))

    @classmethod
    def get_plugin_name(cls) -> str:
        return "SystemInfo"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "system status monitor,allow some hardware info interrogating operations"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def install(self):
        from .util import get_gpu_info, get_mem_info, get_cpu_info, get_all_info, get_disk_info
        from modules.cmd import NameSpaceNode, ExecutableNode, RequiredPermission

        from modules.auth.resources import required_perm_generator
        from modules.auth.permissions import Permission, PermissionCode

        su_perm = Permission(id=PermissionCode.SuperPermission.value, name=f"{self.get_plugin_name()}")
        req_perm: RequiredPermission = required_perm_generator(
            target_resource_name=self.get_plugin_name(), super_permissions=[su_perm]
        )
        self._auth_manager.add_perm_from_req(req_perm)
        tree = NameSpaceNode(
            name=self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD),
            help_message=self.get_plugin_description(),
            children_node=[
                ExecutableNode(name=self.__INFO_CPU_CMD, help_message="get cpu info", source=get_cpu_info),
                ExecutableNode(name=self.__INFO_MEM_CMD, help_message="get memory info", source=get_mem_info),
                ExecutableNode(name=self.__INFO_DISK_CMD, help_message="get disk info", source=get_disk_info),
                ExecutableNode(name=self.__INFO_GPU_CMD, help_message="get gpu info", source=get_gpu_info),
                ExecutableNode(name=self.__INFO_ALL_CMD, help_message="get all info", source=get_all_info),
            ],
            required_permissions=req_perm,
        )

        self._root_namespace_node.add_node(tree, [])

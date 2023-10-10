import os

from modules.plugin_base import AbstractPlugin

__all__ = ["BaiduTranslater"]


class BaiduTranslater(AbstractPlugin):
    CONFIG_APP_ID = "app_id"
    CONFIG_APP_KEY = "app_key"
    CONFIG_API_URL = "api_url"

    translater = None

    CONFIG_TRANSLATE_KEYWORD = "TranslateKeyword"

    def _get_config_parent_dir(self) -> str:
        return os.path.abspath(os.path.dirname(__file__))

    @classmethod
    def get_plugin_name(cls) -> str:
        return "BaiduTranslater"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "A translation plugin using baidu api"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.2"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(self.CONFIG_APP_ID, "replace with baidu translate app_id")
        self._config_registry.register_config(self.CONFIG_APP_KEY, "replace with baidu translate app_key")
        self._config_registry.register_config(self.CONFIG_API_URL, "http://api.fanyi.baidu.com/api/trans/vip/translate")
        self._config_registry.register_config(self.CONFIG_TRANSLATE_KEYWORD, "trans")

    def install(self):
        from .translater import Translater
        from modules.cmd import RequiredPermission, ExecutableNode
        from modules.auth.resources import required_perm_generator
        from modules.auth.permissions import Permission, PermissionCode

        self.__register_all_config()
        self._config_registry.load_config()
        self.translater = Translater(
            appid=self._config_registry.get_config(self.CONFIG_APP_ID),
            appkey=self._config_registry.get_config(self.CONFIG_APP_KEY),
            url=self._config_registry.get_config(self.CONFIG_API_URL),
        )

        def _trans_partial(to_lang: str, query: str) -> str:
            return f"翻译结果:\n\t{self.translater.translate(to_lang, query)}"

        su_perm = Permission(id=PermissionCode.SuperPermission.value, name=f"{self.get_plugin_name()}")
        req_perm: RequiredPermission = required_perm_generator(
            target_resource_name=self.get_plugin_name(), super_permissions=[su_perm]
        )
        tree = ExecutableNode(
            name=self._config_registry.get_config(self.CONFIG_TRANSLATE_KEYWORD),
            help_message=self.get_plugin_description(),
            source=_trans_partial,
            required_permissions=req_perm,
        )

        self._root_namespace_node.add_node(tree)

    def translate(self, to_lang: str, query: str, from_lang: str = "auto"):
        """
        Wrapper for baidu translates
        Args:
            to_lang ():
            query ():
            from_lang ():

        Returns:

        """
        return self.translater.translate(to_lang, query, from_lang)

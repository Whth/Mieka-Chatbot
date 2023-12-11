from typing import Dict

from modules.shared import AbstractPlugin, EnumCMD, NameSpaceNode, ExecutableNode
from .value_conversion import Worth


class CMD(EnumCMD):
    ecnomi = ["ec", "ecno"]
    npv = ["n", "pw"]


class Ecno(AbstractPlugin):
    CONFIG_INDEX_RATE = "i"

    DefaultConfig: Dict = {CONFIG_INDEX_RATE: 0.1}

    @classmethod
    def get_plugin_name(cls) -> str:
        return "Ecno"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "Economical Calculator"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "Whth"

    def install(self):
        def _npv_calc(*args: float) -> str:
            """
            Calculate the net present value (NPV) based on the given cash flow arguments.

            Args:
                *args (float): The cash flow arguments.

            Returns:
                float: The net present value.


            Raises:
                None
            """
            print(f"Received arguments: {args}")
            args = map(float, args)
            worth_seq: list[Worth] = [Worth(value=arg, sequential_index=i) for i, arg in enumerate(args)]
            index_rate: float = self.config_registry.get_config(self.CONFIG_INDEX_RATE)
            stdout = f"Index Rate={index_rate:.2%}\n"

            NPV = Worth.sum_up(worth_seq, index_rate).value

            stdout += f"NPV={NPV:.2f}"
            return stdout

        self.root_namespace_node.add_node(
            NameSpaceNode(
                **CMD.ecnomi.export(),
                help_message=self.get_plugin_description(),
                required_permissions=self.required_permission,
                children_node=[
                    ExecutableNode(
                        **CMD.npv.export(),
                        source=_npv_calc,
                    )
                ],
            )
        )

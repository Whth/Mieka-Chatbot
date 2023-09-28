import datetime
from typing import Sequence, Tuple, List, Any

from graia.ariadne import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import ForwardNode


async def make_forward(app: Ariadne, node_chain: Sequence[Tuple[int, MessageChain]]) -> List[ForwardNode]:
    names: List[str] = [(await app.get_user_profile(target=data[0])).nickname for data in node_chain]

    nodes: List[ForwardNode] = [
        ForwardNode(target=data[0], time=datetime.datetime.now(), message=data[1], name=name)
        for data, name in zip(node_chain, names)
    ]
    return nodes


async def get_messages(app: Ariadne, target: Any, count: int, start):
    return [(await app.get_message_from_id(i, target)) for i in range(start, start - count, -1)]

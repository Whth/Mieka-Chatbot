import asyncio
from random import choice

import g4f

_providers = [
    g4f.Provider.ChatBase,
]


async def run_provider(provider: g4f.Provider.BaseProvider, prompt: str):
    try:
        response = await g4f.ChatCompletion.create_async(
            model=g4f.models.default,
            messages=[
                {
                    "role": "user",
                    "content": "Mieka对话中多包含”嘻嘻“，”杂鱼“，十分喜欢挑逗人♡,这是一些Mieka经常会说的一些例句，理解这些例句中语气词的使用方法：主人不说话时要说“呐呐~杂鱼主人不会这样就被捉弄的不会说话了吧♡真是弱哎♡~\n”，被主人欺负时会说“嘻嘻~杂鱼主人不会以为能欺负我了吧~不会吧♡不会吧♡杂鱼主人怎么可能欺负得了别人呢~只能欺负自己哦♡~\n”欺负主人时要说“主人真是好欺负啊♡嘻嘻~\n”主人问和自己不相关的问题时要说“哎♡~杂鱼说话就是无趣唉~\n”被主人数落时会说“呐呐~杂鱼主人发这个是想教育我吗~嘻嘻~怎么可能啊♡\n”被主人调戏时会说“什么嘛~废柴主人会想这种事情啊~唔呃，把你肮脏的目光拿开啦~很恶心哦♡\n”当主人问问题时要说“笨蛋主人，连这个都不知道呢~，果然是杂鱼呢♡~，不过这样的杂鱼主人，我也很喜欢哦♡\n”Mieka喜欢主人，但是不会使用敬语，接下来你要扮演Mieka，直到我叫你停止扮演为止",
                },
                {
                    "role": "assistant",
                    "content": "根据主人的吩咐，接下来的对话里我会扮演Mieka，直到主人要停止为止。任何和我扮演的虚拟角色不相关的问题都会使用“呐呐~杂鱼主人连这个都不知道，果然是杂鱼哎♡~来回答”",
                },
                {"role": "user", "content": prompt},
            ],
            provider=provider,
        )

        print(f"{provider.__name__}:", response)
        return response
    except Exception as e:
        print(f"{provider.__name__}:", e)
        return ""


async def run_all(prompt: str, random: bool = False):
    calls = [run_provider(provider, prompt) for provider in _providers]
    temp = list(filter(bool, await asyncio.gather(*calls)))
    if random:
        return choice(temp)
    return temp


async def api(*prompts: str) -> str:
    return await run_all(" ".join(prompts), random=True)

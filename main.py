from graia.ariadne.app import Ariadne
from graia.ariadne.entry import config
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.base import MentionMe
from graia.ariadne.model import Friend, Member, Group

from GPT27 import GPT
from baidu_translater.translater import Translater

talker = GPT()
trans = Translater()
verify_key = "INITKEYr54dfbov"
app = Ariadne(
    config(
        verify_key=verify_key,  # 填入 VerifyKey
        account=1801719211,  # 你的机器人的 qq 号
    ),
)


@app.broadcast.receiver("GroupMessage", decorators=[MentionMe()])
async def friend_message_listener(app: Ariadne, member: Member, group: Group, chain: MessageChain):
    feedback = talker.talk(trans.translate('en', str(chain)))
    await app.send_message(group, MessageChain([Plain(trans.translate('zh', feedback))]))
    # 实际上 MessageChain(...) 有没有 "[]" 都没关系


app.launch_blocking()

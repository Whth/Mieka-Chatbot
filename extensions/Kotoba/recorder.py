import pathlib
from typing import TypeAlias, Any, Union

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, ActiveFriendMessage, ActiveGroupMessage
from pydantic import BaseModel, Field

from modules.shared import PersistentDict

AccountID: TypeAlias = int | str


class MessageRecorder(BaseModel):
    class Config:
        validate_assignment = True
        allow_mutation = False

    data_base: PersistentDict = Field(default_factory=PersistentDict, const=True)
    save_file_path: str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        pathlib.Path(self.save_file_path).parent.mkdir(parents=True, exist_ok=True)
        self.load()

    def add_data(self, key: AccountID, value: Any):
        key = str(key)
        if key in self.data_base.container:
            self.data_base.container.get(key).append(str(value))
        else:
            self.data_base.container[key] = [str(value)]

    def del_data(self, key: AccountID):
        key = str(key)
        if key in self.data_base.container:
            self.data_base.container.pop(key)

    def save(self):
        self.data_base.save(self.save_file_path)

    def load(self):
        if pathlib.Path(self.save_file_path).exists() and not self.data_base.load(self.save_file_path):
            pathlib.Path(self.save_file_path).unlink()

    def make_listener(self, dense_save: bool = False):
        async def listener(
            app: Ariadne, msg_event: Union[GroupMessage, FriendMessage, ActiveFriendMessage, ActiveGroupMessage]
        ):
            if isinstance(msg_event, GroupMessage):
                self.add_data(msg_event.sender.group.id, msg_event.message_chain)
            elif isinstance(msg_event, FriendMessage):
                self.add_data(msg_event.sender.id, msg_event.message_chain)
            elif isinstance(msg_event, ActiveGroupMessage):
                self.add_data(msg_event.subject.id, msg_event.message_chain)
                self.add_data(app.account, msg_event.message_chain)
            elif isinstance(msg_event, ActiveFriendMessage):
                self.add_data(app.account, msg_event.message_chain)
            if dense_save:
                self.save()

        return listener

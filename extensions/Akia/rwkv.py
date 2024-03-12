from typing import List

API_V1 = (
    "/api/oai/v1/models",
    "/api/oai/v1/chat/completions",
    "/api/oai/v1/completions",
    "/api/oai/v1/embeddings",
)
API_NORMAL = (
    "/api/oai/models",
    "/api/oai/chat/completions",
    "/api/oai/completions",
    "/api/oai/embeddings",
)

from pydantic import BaseModel


class NameGroup(BaseModel):
    name: str
    identifier_group: List[int]

    def add_menber(self, identifier: int):
        self.identifier_group.append(identifier)
        self.identifier_group = list(set(self.identifier_group))

    def __contains__(self, item) -> bool:
        return item in self.identifier_group


class NameBook(BaseModel):
    name_group: list[NameGroup]


kas1 = NameGroup(name="张三", identifier_group=[1, 2, 3])
kas2 = NameGroup(name="李四", identifier_group=[4, 5, 6])

namebook = NameBook(name_group=[kas1, kas2])


print()
b = NameBook.parse_obj(namebook.dict())
print(b.json())

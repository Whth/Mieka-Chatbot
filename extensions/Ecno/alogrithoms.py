from pydantic import BaseModel


class Value(BaseModel):
    value: float

    def to_present(self, interest_rate: float, years: int) -> float:
    def to_addon(self, interest_rate: float, years: int) -> float:
        return

    def to_future(self, interest_rate: float, years: int) ->float:
        return

    def to_gradient(self, interest_rate: float, years: int) ->float:
        return

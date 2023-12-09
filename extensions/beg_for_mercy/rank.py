import asyncio
import pathlib
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Set, TypeAlias, Tuple, Optional, List

import matplotlib.pyplot as plt
from graia.ariadne import Ariadne
from graia.ariadne.model import Profile
from matplotlib.font_manager import FontProperties
from pydantic import Field, BaseModel

OccurrenceDict: TypeAlias = Dict[str, int]
UserAccount: TypeAlias = int
UserName: TypeAlias = str

RankerInfo: TypeAlias = Tuple[UserAccount, UserName]
RankerDataPair: TypeAlias = Tuple[RankerInfo, int]
RankerDataPack: TypeAlias = OrderedDict[RankerInfo, int]


class ProfanityRank(BaseModel):
    class Config:
        validate_assignment = True

    profanities: Set[str] = Field(default_factory=set, allow_mutation=False)
    records: Dict[UserAccount, OccurrenceDict] = Field(default_factory=dict, allow_mutation=False)

    def check_message(self, message: str) -> OccurrenceDict:
        """
        Counts the occurrences of profanities in a given message and returns a dictionary
        with the profanities as keys and the number of occurrences as values.

        Parameters:
            message (str): The message to check for profanities.

        Returns:
            OccurrenceDict: A dictionary with the profanities as keys and the number of
            occurrences as values.
        Examples:
            >>> ProfanityRank().check_message("fuck you, I hate you!")
            {'fuck': 1}
        """
        result = {}
        for profanity in self.profanities:
            count = message.count(profanity)
            if count == 0:
                continue
            result[profanity] = count
        return result

    def update_records(self, user_id: UserAccount, message: str) -> bool:
        """
        Update the records for a given user with a new message.

        Parameters:
            user_id (UserAccount): The ID of the user account.
            message (str): The message to be added to the records.

        Returns:
            None
        """
        check_message = self.check_message(message)
        if user_id in self.records:
            self.records[user_id] = merge_occurrence_dicts(self.records[user_id], check_message)
        else:
            self.records[user_id] = check_message
        return bool(check_message)

    async def get_rankers(self, app: Ariadne) -> RankerDataPack:
        """
        Returns a dictionary of user accounts and their ranks.

        Returns:
            OrderDict[str, int]: A dictionary of user accounts and their ranks.

        Examples:
            >>> ProfanityRank().get_rankers()
            {'user1': 3, 'user2': 1}
        """

        sorted_data = OrderedDict(sorted(self.records.items(), key=lambda x: sum(x[1].values()), reverse=True))
        user_profiles: Tuple[Profile, ...] = await asyncio.gather(
            *[app.get_user_profile(user_id) for user_id in sorted_data]
        )

        temp = {
            (user_data[0], user_profile.nickname): sum(user_data[1].values())
            for user_data, user_profile in zip(sorted_data.items(), user_profiles)
        }

        return OrderedDict(temp.items())

    def save(self, path: str | Path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.json(ensure_ascii=False, indent=2))


def merge_occurrence_dicts(*dicts: OccurrenceDict) -> OccurrenceDict:
    """
    Merge multiple occurrence dictionaries into a single dictionary.

    Args:
        *dicts (OccurrenceDict): Multiple occurrence dictionaries to merge.

    Returns:
        OccurrenceDict: A merged occurrence dictionary.

    Description:
        This function takes in multiple occurrence dictionaries and merges them into a single dictionary. The occurrence dictionaries are represented as key-value pairs, where the key represents an occurrence and the value represents the count of that occurrence.

        Parameters:
            *dicts (OccurrenceDict): Variable number of occurrence dictionaries to merge.

        Returns:
            OccurrenceDict: A merged occurrence dictionary containing the combined occurrences from all the input dictionaries.

        Example:

            >>> merge_occurrence_dicts({'apple': 3, 'banana': 2}, {'banana': 1, 'orange': 5})
            {'apple': 3, 'banana': 3, 'orange': 5}

    """
    result: OccurrenceDict = {}
    for d in dicts:
        for key, value in d.items():
            if key in result:
                # add the value to the existing key
                result[key] += value
            else:
                # create a new key
                result[key] = value
    return result


def make_string_from_ranker(index: int, ranker: RankerDataPair) -> str:
    return f"[{index}]: <{ranker[0][0]}-{ranker[0][1]}>\n" f"\t NG-Word检测次数: {ranker[1]}"


def create_ranker_broad(
    ranker_data: RankerDataPack, save_path: str | Path, font_file: Optional[str] = None, max_size: int = 10
):
    # 创建一个画布
    plt.figure(facecolor="lightgray", dpi=100, figsize=(8, int(1.5 * max_size)))

    # 设置背景颜色
    plt.axis("off")

    # 设置字体和颜色
    font = FontProperties(fname=font_file, size=14)

    ranker_data: List[RankerDataPair] = list(ranker_data.items())[:max_size]
    indent = 0
    seeker = 1
    ranker_index = 1
    if ranker_data:
        first_ranker = ranker_data.pop(0)
        first_ranker_txt = plt.text(
            indent, seeker, make_string_from_ranker(ranker_index, first_ranker), fontproperties=font, color="red"
        )
        first_ranker_txt.set_fontsize(50)
        seeker -= 0.12
        ranker_index += 1
    if ranker_data:
        second_ranker = ranker_data.pop(0)
        second_ranker_txt = plt.text(
            indent, seeker, make_string_from_ranker(ranker_index, second_ranker), fontproperties=font, color="purple"
        )
        second_ranker_txt.set_fontsize(40)
        seeker -= 0.11
        ranker_index += 1
    if ranker_data:
        third_ranker = ranker_data.pop(0)
        third_ranker_txt = plt.text(
            indent, seeker, make_string_from_ranker(ranker_index, third_ranker), fontproperties=font, color="green"
        )
        third_ranker_txt.set_fontsize(30)
        seeker -= 0.105
        ranker_index += 1
    if ranker_data:
        step_len = seeker / len(ranker_data)
        for ranker in ranker_data:
            ranker_txt = plt.text(
                indent, seeker, make_string_from_ranker(ranker_index, ranker), fontproperties=font, color="yellow"
            )
            ranker_txt.set_fontsize(20)
            seeker -= step_len
            ranker_index += 1
    plt.tight_layout()
    pathlib.Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    # 显示画布
    plt.savefig(save_path)

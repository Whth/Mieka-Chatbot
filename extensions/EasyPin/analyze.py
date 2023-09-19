import re
from datetime import datetime, timedelta
from typing import Callable, List, Optional, Sequence, Any, Union

pattern = re.compile(r"^((\d+)月(\d+)[天日]|(\d+)\.(\d+))?(\d+)[点.:：](\d+)?分?$")


"|早上|晚上|中午"

Procedure = Callable[[str], str]


class Preprocessor(object):
    def __init__(self, procedures: Optional[Sequence[Procedure]] = None):
        self._procedures: List[Procedure] = []
        self._procedures.extend(procedures) if procedures else None

    def process(self, string: str) -> str:
        for procedure in self._procedures:
            string = procedure(string)
        return string

    def register_procedure(self, procedure: Procedure) -> None:
        self._procedures.append(procedure)


def chinese_to_arabic(string) -> int:
    """
    Converts a Chinese number string to an Arabic number.

    Args:
        string (str): The Chinese number string to be converted.

    Returns:
        int: The converted Arabic number.
    """
    string = string.strip()

    # Define a mapping of Chinese characters to their corresponding numeric values
    num_map = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}

    # Define a mapping of Chinese characters representing units to their corresponding values
    unit_map = {"十": 10, "百": 100, "千": 1000, "万": 10000, "亿": 100000000}

    result = 0
    temp = 0

    # Iterate through each character in the Chinese number string
    for char in string:
        if char in num_map:
            temp = num_map[char]
        elif char in unit_map:
            if char == "十" and temp == 0:
                temp = 1
            result += temp * unit_map[char]
            temp = 0

    result += temp
    return result


def replace_chinese_numbers(string) -> str:
    """
    Replaces Chinese numbers in a string with their Arabic equivalents.

    Args:
        string (str): The input string.

    Returns:
        str: The string with Chinese numbers replaced by their Arabic equivalents.
    """
    pattern = r"[零一二三四五六七八九十百千万亿]+"  # pattern to match Chinese numbers
    matches = re.findall(pattern, string)  # find all matches of Chinese numbers in the string

    for match in matches:
        # convert the Chinese number to Arabic number
        arabic_num = chinese_to_arabic(match)
        # replace the Chinese number with the Arabic number in the string
        string = string.replace(match, str(arabic_num))

    return string


def convert_relative_to_abs(string: str) -> str:
    """
    Converts a relative month string to an absolute month string.

    Args:
        string: The input string containing the relative month.

    Returns:
        The input string with the relative month replaced by the absolute month.
    """

    # Define the names of time units
    hour_names = ["个小时", "小时", "钟", "时"]
    min_names = ["分", "分钟"]
    day_names = ["天", "日"]
    month_names = ["个月"]

    # Define prepositions used for matching
    prepositions = ["后", "之后"]

    # Create regular expressions patterns for matching relative month offsets, absolute month names,
    # and variations of month names
    hour_name_reg = "|".join(hour_names)
    min_name_reg = "|".join(min_names)
    day_name_reg = "|".join(day_names)
    month_name_reg = "|".join(month_names)
    reg_exp = rf"(\d+)(?:({min_name_reg})|({hour_name_reg})|({day_name_reg})|({month_name_reg}))(?:{prepositions})"
    # Find all matches in the input string using the regular expression pattern
    matches = re.findall(pattern=reg_exp, string=string)

    # If no matches are found, return the original input string
    if not matches:
        return string
    print(matches)
    # Extract the groups from the first match
    groups: Sequence[Union[str, Any]] = matches[0]
    offset = int(groups[0])

    # Calculate the absolute values for month, day, hour, and minute
    abs_month = datetime.today().month + offset if groups[4] else datetime.today().month
    abs_day = datetime.today().day + offset if groups[3] else datetime.today().day
    abs_hour = datetime.today().hour + offset if groups[2] else datetime.today().hour
    abs_min = datetime.today().minute + offset if groups[1] else datetime.today().minute

    # Replace the matched relative month string with the absolute month string
    return re.sub(
        pattern=reg_exp,
        repl=f"{abs_month}月{abs_day}日{abs_hour}点{abs_min}分",
        string=string,
        count=1,
    )


def convert_relative_day_to_abs(string: str) -> str:
    """
    Converts a relative day string to an absolute day string.

    Args:
        string: The input string containing the relative day.

    Returns:
        The input string with the relative day replaced by the absolute day.

    Example:
        >>> convert_relative_day_to_abs("今天是明天")
        '9.19是明天'
    """

    # Map of weekdays in Chinese characters to their corresponding numerical value
    day_map = {"今": 0, "本": 0, "明": 1, "后": 2, "大后": 3}

    # List of variations of week names
    day_names = ["日", "天"]

    # Create regular expressions patterns for matching "this week" matches, "next week" matches,
    # week names, and weekdays

    day_name_reg = "|".join(day_names)
    day_reg = "|".join(day_map.keys())

    reg_exp = f"({day_reg})(?:{day_name_reg})"

    # Find all matches in the date string using the regular expression pattern
    matches = re.findall(pattern=reg_exp, string=string)

    # If no matches are found, return the original date string
    if not all(matches):
        return string

    # Extract the groups from the first match
    groups: Sequence[Union[str, Any]] = matches[0]

    # Get the numerical value of the weekday from the map
    offset = day_map[groups[0]]
    today = datetime.today().date()
    # Calculate the absolute date by adding the offset and the difference between the weekday
    # and the current weekday to the current date
    abs_date = today + timedelta(days=offset)

    # Replace the matched relative date string with the absolute date string
    return re.sub(
        pattern=reg_exp,
        repl=f"{abs_date.month}.{abs_date.day}",
        string=string,
        count=1,
    )


def convert_relative_month_to_abs(string: str) -> str:
    """
    Converts a relative month string to an absolute month string.

    Args:
        string: The input string containing the relative month.

    Returns:
        The input string with the relative month replaced by the absolute month.

    """
    # Map of relative month offsets in Chinese characters to their corresponding numerical value
    relative_month_offset_map = {"这个": 0, "本": 0, "下": 1, "下个": 1}

    # List of variations of month names
    month_names = ["月", "月份"]

    # Create regular expressions patterns for matching relative month offsets, absolute month names,
    # and variations of month names
    offset_reg = "|".join(relative_month_offset_map.keys())

    name_reg = "|".join(month_names)
    reg_exp = f"(?:({offset_reg}))(?:{name_reg})"

    # Find all matches in the input string using the regular expression pattern
    matches = re.findall(pattern=reg_exp, string=string)

    # If no matches are found, return the original input string
    if not all(matches):
        return string

    # Extract the groups from the first match
    groups: Sequence[Union[str, Any]] = matches[0]
    print(groups)
    # Get the numerical value of the relative month offset from the map
    offset = relative_month_offset_map.get(groups[0], 0)
    # Calculate the absolute month by adding the offset and the difference between the month
    # and the current month to the current month
    abs_month = datetime.today().month + offset

    # Replace the matched relative month string with the absolute month string
    return re.sub(
        pattern=reg_exp,
        repl=f"{abs_month}月",
        string=string,
        count=1,
    )


def convert_relative_weekday_to_absolute(string: str) -> str:
    """
    Converts a relative date string to an absolute date string.

    Args:
        string (str): The relative date string to convert.

    Returns:
        str: The converted absolute date string.
    """

    # Map of weekdays in Chinese characters to their corresponding numerical value
    weekday_map = {"末": 5, "一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6}

    # List of variations of "this week" matches
    this_week_matches = ["本", "本个", "这个", "现在这个"]

    # List of variations of "next week" matches
    next_week_matches = ["下", "下个", "接下来的"]

    # List of variations of week names
    week_names = ["周", "星期"]

    # Create regular expressions patterns for matching "this week" matches, "next week" matches,
    # week names, and weekdays
    this_week_reg = "|".join(this_week_matches)
    next_week_reg = "|".join(next_week_matches)
    week_name_reg = "|".join(week_names)
    weekday_reg = "|".join(weekday_map.keys())

    reg_exp = f"(?:({this_week_reg})|({next_week_reg}))?(?:{week_name_reg})({weekday_reg})"

    # Find all matches in the date string using the regular expression pattern
    matches = re.findall(pattern=reg_exp, string=string)

    # If no matches are found, return the original date string
    if not all(matches):
        return string

    # Extract the groups from the first match
    groups: Sequence[Union[str, Any]] = matches[0]

    offset = 0
    # If a match for "next week" is found, add 7 days to the offset
    if groups[1]:
        offset += 7

    # Get the numerical value of the weekday from the map
    weekday = weekday_map[groups[-1]]
    today = datetime.today().date()
    # Calculate the absolute date by adding the offset and the difference between the weekday
    # and the current weekday to the current date
    abs_date = today + timedelta(days=offset + weekday - today.weekday())

    # Replace the matched relative date string with the absolute date string
    return re.sub(
        pattern=reg_exp,
        repl=f"{abs_date.month}.{abs_date.day}",
        string=string,
        count=1,
    )


test_strings = [
    "本月1日上午9点",
    "下个月3日下午2点半",
    "10.30",
    "本周五晚上8点",
    "明天下午3点15分",
    "中午12点",
    "晚上7点半",
    "下午4点整",
    "早上10点20分",
    "这个星期三下午5点",
]

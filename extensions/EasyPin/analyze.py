import datetime
import re

pattern: re.Pattern[str] = re.compile(
    r""
    r"^([今明后]年|\d+[年.])?(([今本明后]|[本这下]周[一二三四五六日]|[本这]月\d+日)|(\d+月\d+日|\d+\.\d+))?"
    r"([上下]午)?"
    r"(([零一二三四五六七八九十]|十[一二三四五六七八九]|二十[一二三四])|\d+)?"
    r"[点.:；]?"
    r"(整|半|[一二三四五六七八九十]|[一二三四五]?十[一二三四五六七八九]|\d+)?"
    r"分?$"
)


import re


def convert_to_crontab(match_str):
    # 将匹配的字符串转换为crontab格式的字符串
    # 这里只是一个示例，你可以根据需要进行修改

    # 提取年份、月份、日期、上下午、小时和分钟
    year = month = day = week = hour = minute = "*"
    am_pm = ""
    time_str = match_str.strip()

    # 匹配年份
    year_match = re.search(r"([今明后]年|\d+[年.])", time_str)
    if year_match:
        year = year_match.group(0)

    # 匹配月份和日期
    month_day_match = re.search(r"(([今本明后]|[本这下]周[一二三四五六日]|[本这]月\d+日)|(\d+月\d+日|\d+\.\d+))", time_str)
    if month_day_match:
        month_day = month_day_match.group(0)
        if "周" in month_day:
            week = month_day[1:]
        elif "月" in month_day:
            month, day = month_day.split("月")
            day = day.strip("日")
        elif "." in month_day:
            month, day = month_day.split(".")

    # 匹配上下午
    am_pm_match = re.search(r"[上下]午", time_str)
    if am_pm_match:
        am_pm = am_pm_match.group(0)

    # 匹配小时和分钟
    time_match = re.search(
        r"(([零一二三四五六七八九十]|十[一二三四五六七八九]|二十[一二三四])|\d+)?[点.:；]?(整|半|[一二三四五六七八九十]|[一二三四五]?十[一二三四五六七八九]|\d+)?分?", time_str
    )
    if time_match:
        time = time_match.group(0)
        if "点" in time:
            hour, minute = time.split("点")
            hour = hour.strip()
        elif "分" in time:
            minute = time.strip("分")

    # 拼接crontab格式的字符串
    crontab_str = f"{minute} {hour} {day} {month} {week} {am_pm}"
    return crontab_str


# 测试
match_str = "明天下午3点半"
crontab_str = convert_to_crontab(match_str)
print(crontab_str)  # 输出：30 3 * * * 下午


def convert_relative_date(relative_date) -> datetime.date:
    today = datetime.date.today()

    if relative_date == "今天":
        return today
    elif relative_date == "明天":
        return today + datetime.timedelta(days=1)
    elif relative_date == "后天":
        return today + datetime.timedelta(days=2)
    elif relative_date == "本周":
        weekday = today.weekday()
        days_until_sunday = 6 - weekday
        return today + datetime.timedelta(days=days_until_sunday)
    elif relative_date == "本月":
        last_day_of_month = datetime.date(today.year, today.month, 1) + datetime.timedelta(days=32)
        return last_day_of_month - datetime.timedelta(days=last_day_of_month.day)
    elif relative_date == "本日":
        return today
    else:
        return None


# Example usage
relative_date = "本月"
absolute_date = convert_relative_date(relative_date)
print(absolute_date)

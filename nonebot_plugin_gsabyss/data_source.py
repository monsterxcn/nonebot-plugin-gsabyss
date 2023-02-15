import json
import asyncio
from time import time
from io import BytesIO
from pathlib import Path
from re import sub, findall
from calendar import monthrange
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Tuple, Union, Literal, Optional

from PIL import Image
from nonebot.log import logger
from httpx import AsyncClient, stream
from nonebot import require, get_driver
from pydantic.error_wrappers import ValidationError

from .config import plugin_config
from .models.akasha import AkashaAbyssData

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler  # noqa: E402

DL_DIR = plugin_config.gsabyss_dir
"""本地缓存目录。默认 `data/gsabyss`"""

HHW_CACHE = DL_DIR / "abyss_hhw.json"
"""Honey Hunter World 深渊解析数据文件"""

TZ = timezone(timedelta(hours=8))
"""上海时区"""

driver = get_driver()


def download_init_res(file_name: str) -> Path:
    """阿里云 OSS 初始化资源下载，不会重复下载已存在的文件"""

    save_path = DL_DIR / file_name
    if not save_path.exists():
        logger.info(f"正在下载初始化资源 {file_name}")
        with stream(
            "GET", f"https://cdn.monsterx.cn/bot/gsabyss/{file_name}", verify=False
        ) as r:
            with open(save_path, "wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)

    return save_path


async def download_pic(
    url: str, dir: str = "", rename: str = "", retry: int = 3
) -> Optional[Path]:
    """图片资源下载。使用 Pillow 保存

    * ``param url: str`` 图片 URL
    * ``param dir: str = ""`` 下载目标文件夹
    * ``param rename: str = ""`` 图片重命名。默认保存为 ``.png``
    * ``param retry: int = 3`` 下载失败重试次数
    - ``return: Optional[Path]`` 本地文件路径。出错时返回空
    """

    # 图片保存路径处理
    f = DL_DIR / f"{dir}/{rename}.png".lstrip("/")
    if f.exists():
        return f
    f.parent.mkdir(parents=True, exist_ok=True)

    # 远程文件下载
    async with AsyncClient(verify=False, timeout=20.0) as client:
        logger.info(f"正在下载文件 {f.name}\n>>>>> {url}")
        while retry:
            try:
                headers = {
                    "referer": "https://genshin.honeyhunterworld.com/d_1001/?lang=CHS",
                    "user-agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/"
                        "104.0.5112.81 Safari/537.36 Edg/104.0.1293.47"
                    ),
                }
                res = await client.get(url, headers=headers)
                userImage = Image.open(BytesIO(res.content)).convert("RGBA")
                userImage.save(f, format="PNG", quality=100)
                return f
            except Exception as e:
                retry -= 1
                if retry:
                    await asyncio.sleep(2)
                else:
                    logger.opt(exception=e).error(f"文件 {f.name} 下载失败！")


def fix_schedule_key(schedule: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """深境螺旋日程数据键值修正

    * ``param schedule: Dict[str, Dict[str, str]]`` 深境螺旋日程数据字典
    - ``return: Dict[str, Dict[str, str]]`` 修正后的深境螺旋日程数据字典
    """

    time_format = "%Y-%m-%d %H:%M:%S"
    start_time = datetime.strptime("2020-07-01 04:00:00", time_format)

    schedule_fixed = {}
    for time_key, data in reversed(schedule.items()):
        # 修正键值
        key_fixed = start_time.strftime(time_format)
        if time_key != key_fixed:
            logger.info(f"深境螺旋日程键值 {time_key} 已修正为 {key_fixed}")
        schedule_fixed[key_fixed] = data
        # 递增时间
        if start_time.day == 1:
            offset_days = 15
        else:
            _, days_total = monthrange(start_time.year, start_time.month)
            offset_days = days_total - start_time.day + 1
        start_time += timedelta(days=offset_days)

    return schedule_fixed


@scheduler.scheduled_job("cron", day="*/7", kwargs={"force": True})
@driver.on_startup
async def fetch_hhw_abyss(
    force: bool = False, retry: int = 3
) -> Optional[Dict[str, Dict[str, Dict[str, Any]]]]:
    """Honey Hunter World 深渊解析数据抓取

    * ``param force: bool = False`` 是否强制更新
    * ``param retry: int = 3`` 请求失败重试次数
    - ``return: Optional[Dict[str, Dict[str, Dict[str, Any]]]]`` JSON 数据。出错时无返回
    """

    # 使用本地缓存
    if HHW_CACHE.exists() and not force:
        logger.info("HHW 深渊数据已缓存，跳过更新")
        return json.loads(HHW_CACHE.read_text(encoding="UTF-8"))

    # 使用最新数据
    async with AsyncClient(verify=False, timeout=20.0) as client:
        res_json = {}
        while retry:
            try:
                res = await client.get("https://cdn.monsterx.cn/bot/gsabyss/abyss.json")
                res_json = res.json()
                break
            except Exception as e:
                retry -= 1
                if retry:
                    await asyncio.sleep(3)
                else:
                    logger.opt(exception=e).error("HHW 深渊数据更新失败！")
                    return

    # 深境螺旋日程数据的键值需要纠正
    res_json["Schedule"] = fix_schedule_key(res_json["Schedule"])
    # 写入缓存
    HHW_CACHE.write_text(json.dumps(res_json, ensure_ascii=False), encoding="UTF-8")
    logger.info("HHW 深渊数据已更新！")
    return res_json


def get_schedule_key(period: Literal["last", "now", "next"] = "now") -> str:
    """深境螺旋日程数据键值获取

    * ``param period: Literal["last", "now", "next"] = "now"`` 周期。支持上期 ``last``、本期 ``now``、下期 ``next``
    - ``return: str`` 深境螺旋日程数据键值。形如 ``2023-02-01 04:00:00``
    """  # noqa: E501

    # 获取当前周期的起点时间
    dt = datetime.fromtimestamp(time(), TZ)
    first_half_start = datetime(dt.year, dt.month, 1, 4, 0, 0, tzinfo=TZ)
    second_half_start = datetime(dt.year, dt.month, 16, 4, 0, 0, tzinfo=TZ)
    is_first_half = first_half_start <= dt < second_half_start
    dt = first_half_start if is_first_half else second_half_start

    # 获取语义对应周期的起点时间
    if period == "last":
        if is_first_half:
            _last_month = dt - timedelta(days=1)
            dt = datetime(_last_month.year, _last_month.month, 16, 4, 0, 0, tzinfo=TZ)
        else:
            dt -= timedelta(days=15)
    elif period == "next":
        _, month_total_day = monthrange(dt.year, dt.month)
        delta = 15 if is_first_half else (month_total_day - 15)
        dt += timedelta(days=delta)

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_quickview_input(input: str) -> Tuple[int, int, str]:
    """用户输入解析，默认结果为本期十二层全层

    * ``param input: str`` 用户输入
    - ``return: Tuple[int, int, str]`` 层数、间数（为 ``0`` 表示获取全层）、深境螺旋日程数据键值
    """

    # 层数默认 12，间数默认 0，周期默认本期
    floor_idx, chamber_idx, schedule_key = 12, 0, "now"

    chinese_regex = "(十一)|(十二)|一|二|三|四|五|六|七|八|九|十"
    chinese_convert = {
        "一": 1,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
        "十一": 11,
        "十二": 12,
    }

    # 输入关键词按空格分割
    for keyword in input.split():
        # 支持形如："12"、"12层"、"第12层"
        if keyword.lstrip("第").rstrip("层").isdigit():
            _keyword = keyword.lstrip("第").rstrip("层")
            if 1 <= int(_keyword) <= 12:
                floor_idx = int(_keyword)
                continue
        # 支持形如："十二"、"第十二层"
        if findall(rf"^第?({chinese_regex})层?$", keyword):
            first_matched = findall(rf"第?({chinese_regex})层?", keyword)[0]
            floor_idx = chinese_convert[first_matched[0]]
            continue
        # 支持形如："12-3"、"1-1"、"12_1"、"12—1"、"12－1"
        if sub(r"[-_—－]", "", keyword).isdigit():
            matched = findall(r"^(1[0-2]|[1-9])[-_—－]([1-3])$", keyword)
            if matched:
                floor_idx, chamber_idx = int(matched[0][0]), int(matched[0][1])
                continue
        # 支持形如："上期"、"下期"
        if keyword in ["上期", "下期"]:
            schedule_key = "last" if keyword == "上期" else "next"
            continue
        # 支持形如："23年2月上"、"2023年2月上"、"2023年二月上"、"二月上"
        if findall(
            rf"^(\d{4}|\d{2}|)年?((1[0-2]|[1-9])|({chinese_regex}))月(上|下)", keyword
        ):
            first_matched = findall(
                rf"^(\d{4}|\d{2}|)年?((1[0-2]|[1-9])|({chinese_regex}))月(上|下)", keyword
            )[0]
            _year = (
                (2000 + int(first_matched[0]))
                if len(first_matched[0]) == 2
                else int(first_matched[0])
                if first_matched[0]
                else datetime.fromtimestamp(time(), TZ).year
            )
            _month = (
                int(first_matched[1])
                if str(first_matched[1]).isdigit()
                else chinese_convert[first_matched[1]]
            )
            _day = 1 if first_matched[-1] == "上" else 16
            schedule_key = datetime(_year, _month, _day, 4, 0, 0).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            continue

    # 转换周期语义为深境螺旋日程数据键值
    if schedule_key in ["last", "now", "next"]:
        schedule_key = get_schedule_key(schedule_key)  # type: ignore

    return floor_idx, chamber_idx, schedule_key


async def fetch_akasha_abyss(retry: int = 3) -> Union[AkashaAbyssData, str]:
    """Akasha Database 深渊统计数据抓取

    * ``param retry: int = 3`` 请求失败重试次数
    - ``return: Union[AkashaAbyssData, str]`` AkashaAbyssData 数据。出错时返回错误消息
    """

    error_msg = ""

    # 使用最新数据
    async with AsyncClient(verify=False, timeout=20.0) as client:
        while retry:
            try:
                res = await client.get(
                    "https://akashadata.feixiaoqiu.com/static/data/abyss_total.js",
                    params={"v": str(time())[:7]},
                )
                res_json = json.loads(res.text.lstrip("var static_abyss_total ="))
                return AkashaAbyssData.parse_obj(res_json)
            except Exception as e:
                retry -= 1
                if retry:
                    await asyncio.sleep(3)
                else:
                    act = "获取" if isinstance(Exception, ValidationError) else "解析"
                    error_msg = f"Akasha 深渊数据{act}失败！"
                    logger.opt(exception=e).error(error_msg)

    return error_msg

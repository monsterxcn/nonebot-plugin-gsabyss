from nonebot.params import CommandArg
from nonebot.plugin import on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment

from .config import plugin_config
from .draw_quickview import AbyssQuickViewDraw
from .draw_statistic import AbyssStatisticDraw
from .data_source import fetch_akasha_abyss, parse_quickview_input

PRIORITY = plugin_config.gsabyss_priority
quickview_matcher = on_command("速览", aliases={"深渊速览"}, priority=PRIORITY, block=True)
totalview_matcher = on_command("深渊统计", priority=PRIORITY, block=True)


@quickview_matcher.handle()
async def abyssQuick(arg: Message = CommandArg()):
    floor_idx, chamber_idx, schedule_key = parse_quickview_input(str(arg))
    drawer = AbyssQuickViewDraw(floor_idx, chamber_idx, schedule_key)
    res = await drawer.get_full_picture()
    await quickview_matcher.finish(
        res if isinstance(res, str) else MessageSegment.image(res)
    )


@totalview_matcher.handle()
async def abyssTotal(arg: Message = CommandArg()):
    if arg:
        await totalview_matcher.finish()
    akasha_data = await fetch_akasha_abyss()
    if isinstance(akasha_data, str):
        await totalview_matcher.finish(akasha_data)
    drawer = AbyssStatisticDraw(akasha_data)
    res = await drawer.get_full_picture()
    await totalview_matcher.finish(MessageSegment.image(res))

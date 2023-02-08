from nonebot.params import CommandArg
from nonebot.plugin import on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment

from .data_source import parse_quickview_input
from .draw_quickview import AbyssQuickViewDraw

quickview_matcher = on_command("速览", aliases={"深渊速览"}, priority=1, block=True)


@quickview_matcher.handle()
async def abyssQuick(arg: Message = CommandArg()):
    floor_idx, chamber_idx, schedule_key = parse_quickview_input(str(arg))
    drawer = AbyssQuickViewDraw(floor_idx, chamber_idx, schedule_key)
    res = await drawer.get_full_picture()
    await quickview_matcher.finish(
        res if isinstance(res, str) else MessageSegment.image(res)
    )

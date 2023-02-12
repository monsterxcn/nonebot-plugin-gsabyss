import asyncio
from io import BytesIO
from typing import List

from PIL import Image, ImageDraw
from nonebot.utils import run_sync

from .data_source import DL_DIR, download_pic
from .models.akasha import (
    LastRate,
    TeamItem,
    CharacterItem,
    AbyssTotalView,
    AkashaAbyssData,
)
from .draw_utils import (
    WHITE,
    NEG_BG,
    ORANGE,
    POS_BG,
    YELLOW,
    BG_DEEP,
    RARITY4,
    RARITY5,
    BG_COLOR,
    BG_LIGHT,
    RESAMPLE,
    NEG_COLOR,
    POS_COLOR,
    _f16,
    _f24,
    _gsf16,
    _gsf20,
    _gsf32,
    _half_img,
    _gsf16_char_height,
    _gsf20_char_height,
    rounded_rectangle_mask,
)


class AbyssStatisticDraw:
    """深境螺旋统计绘图类"""

    _mask_50r7 = rounded_rectangle_mask(mask=True)

    def __init__(self, akasha_data: AkashaAbyssData) -> None:
        """
        * ``param akasha_data: Dict[str, Any]`` Akasha Database 深渊统计数据
        """

        self.DATA = akasha_data
        """Akasha Database 深渊统计数据"""

    @run_sync
    def draw_top(
        self,
        modify_time: str,
        schedule_version_desc: str,
        abyss_total_view: AbyssTotalView,
        last_rate: LastRate,
    ) -> Image.Image:
        """绘制顶部。包含标题、数据汇总

        * ``param modify_time: str`` 更新时间
        * ``param schedule_version_desc: str`` 深渊版本描述
        * ``param abyss_total_view: AbyssTotalView`` 深渊数据汇总数据
        * ``param last_rate: LastRate`` 深渊数据汇总相比上期变化数据
        - ``return Image.Image`` 顶部图像
        """

        result = Image.new("RGBA", (700, 250), BG_DEEP)
        drawer = ImageDraw.Draw(result)

        # 标题
        title = f"{schedule_version_desc[:3]} {schedule_version_desc[3:]} 深渊统计"
        drawer.text(
            (int((700 - _gsf32.getlength(title)) / 2), 20),
            title,
            fill=YELLOW,
            font=_gsf32,
        )
        # 描述
        description = f"虚空数据库出战人数 {abyss_total_view.person_war}    更新时间 {modify_time}"
        drawer.text(
            (int((700 - _f24.getlength(description)) / 2), 70),
            description,
            fill=ORANGE,
            font=_f24,
        )
        # 数据汇总
        total_view_items = [
            # 左侧项目
            ["人均获得渊星", abyss_total_view.avg_star, last_rate.avg_star],
            ["平均战斗次数", abyss_total_view.avg_battle_count, last_rate.avg_battle_count],
            [
                "满星战斗次数",
                abyss_total_view.avg_maxstar_battle_count,
                last_rate.avg_maxstar_battle_count,
            ],
            # 右侧项目
            ["通关比例", abyss_total_view.pass_rate, last_rate.pass_rate],
            ["满星比例", abyss_total_view.maxstar_rate, last_rate.maxstar_rate],
            ["一遍满星", abyss_total_view.maxstar_12_rate, last_rate.maxstar_12_rate],
        ]
        for _idx, items in enumerate(total_view_items):
            start_x, end_x = (40, 330) if _idx < 3 else (370, 700 - 40)
            start_y = 120 + 40 * (_idx % 3)
            # 项目标题
            drawer.text((start_x, start_y), items[0], fill=YELLOW, font=_f24)
            # 项目内容
            value_start_y = int(start_y + 13 - _gsf20_char_height / 2)
            if len(items) == 2:
                drawer.text(
                    (end_x - _gsf20.getlength(items[1]), value_start_y),
                    items[1],
                    fill=WHITE,
                    font=_gsf20,
                )
            else:
                # 含上期变化的项目绘制
                if items[0] in ["通关比例", "满星比例", "一遍满星"]:
                    value_str, diff_str = f"{items[1]}%", f"{items[-1]}%"
                else:
                    value_str, diff_str = items[1], items[-1]
                diff_str = diff_str if diff_str.startswith("-") else f"+{diff_str}"
                diff_width = _gsf20.getlength(diff_str)
                diff_bg = rounded_rectangle_mask(
                    diff_width + 10,
                    26,
                    radius=5,
                    fill=POS_BG if float(items[-1]) >= 0 else NEG_BG,
                )
                result.paste(diff_bg, (int(end_x - diff_width - 10), start_y), diff_bg)
                drawer.text(
                    (end_x - diff_width - 5, value_start_y),
                    diff_str,
                    fill=POS_COLOR if float(items[-1]) >= 0 else NEG_COLOR,
                    font=_gsf20,
                )
                drawer.text(
                    (
                        end_x - diff_width - 10 - 10 - _gsf20.getlength(value_str),
                        value_start_y,
                    ),
                    value_str,
                    fill=WHITE,
                    font=_gsf20,
                )

        return result

    @run_sync
    def draw_middle(self, character_used_list: List[CharacterItem]) -> Image.Image:
        """绘制中间。包含使用排行

        * ``param character_used_list: List[CharacterItem]`` 角色列表
        - ``return Image.Image`` 中间图像
        """

        result = Image.new("RGBA", (700, 375), BG_COLOR)
        drawer = ImageDraw.Draw(result)

        drawer.text((20, 25), "第 12 层使用排行", fill=YELLOW, font=_f24)

        drawer.rectangle((20, 65, 680, 375), fill=BG_LIGHT, width=0)
        for _idx, char in enumerate(character_used_list[:30]):
            start_x = 32 + 65 * (_idx % 10)
            start_y = 85 + 100 * (_idx // 10)
            icon_path = DL_DIR / f"char/{char.name}.png"
            if icon_path.exists():
                # 存在从虚空数据库直接下载的图标
                icon_img = Image.open(icon_path).convert("RGBA")
                icon_img = icon_img.resize((50, 50), resample=RESAMPLE)
                icon_img.putalpha(AbyssStatisticDraw._mask_50r7)
                result.paste(icon_img, (start_x, start_y), icon_img)
            else:
                # 图标不存在时绘制文字
                drawer.rectangle(
                    (start_x, start_y, start_x + 50 - 1, start_y + 50 - 1),
                    fill=RARITY5 if char.rarity == 5 else RARITY4,
                    width=0,
                )
                drawer.text(
                    (
                        int(start_x + 25 - _gsf16.getlength(char.name) / 2),
                        int(start_y + 25 - _gsf16_char_height / 2),
                    ),
                    char.name,
                    fill=WHITE,
                    font=_gsf16,
                )
            drawer.text(
                (
                    int(start_x + 25 - _f16.getlength(f"{char.value}%") / 2),
                    start_y + 59,
                ),
                f"{char.value}%",
                fill=WHITE,
                font=_f16,
            )

        return result

    @run_sync
    def draw_buttom(
        self,
        team_up_list: List[TeamItem],
        team_down_list: List[TeamItem],
        character_used_list: List[CharacterItem],
    ) -> Image.Image:
        """绘制底部。包含热门队伍

        * ``param team_up_list: List[TeamItem]`` 上半队伍列表
        * ``param team_down_list: List[TeamItem]`` 下半队伍列表
        * ``param character_used_list: List[CharacterItem]`` 角色列表，用于获取角色图标
        - ``return Image.Image`` 底部图像
        """

        # 将角色列表数据转为 ID 为键的字典
        _char_list = {char.avatar_id: char for char in character_used_list}

        result = Image.new("RGBA", (700, 595), BG_COLOR)
        drawer = ImageDraw.Draw(result)

        drawer.text((20, 25), "第 12 层热门队伍", fill=YELLOW, font=_f24)

        for group_idx, teams in enumerate([team_up_list[:5], team_down_list[:5]]):
            group_start_x, group_start_y = (360 if group_idx else 20), 65
            drawer.rectangle(
                (
                    group_start_x,
                    group_start_y,
                    group_start_x + 320 - 1,
                    group_start_y + 510 - 1,
                ),
                fill=BG_LIGHT,
                width=0,
            )
            if not group_idx:
                half_icon = _half_img
            else:
                # 下半间的图标由原图标上下翻转生成
                half_icon = _half_img.transpose(Image.FLIP_TOP_BOTTOM)
            result.paste(
                half_icon, (group_start_x + 320 - 12, group_start_y - 12), half_icon
            )

            for team_idx, team in enumerate(teams):
                team_start_x = group_start_x + 30
                team_start_y = group_start_y + 20 + 100 * team_idx
                drawer.text(
                    (team_start_x + 3, team_start_y + 59),
                    f"出场 {team.dc if group_idx else team.uc}",
                    fill=WHITE,
                    font=_gsf16,
                )
                right_string = f"满星 {team.dmr if group_idx else team.umr}%"
                drawer.text(
                    (
                        team_start_x + 260 - 3 - _gsf16.getlength(right_string),
                        team_start_y + 59,
                    ),
                    right_string,
                    fill=WHITE,
                    font=_gsf16,
                )
                for char_idx, char_short_id in enumerate(team.tl):
                    char = _char_list[10000000 + char_short_id]
                    char_start_x = team_start_x + 70 * char_idx
                    icon_path = DL_DIR / f"char/{char.name}.png"
                    if icon_path.exists():
                        # 存在从虚空数据库直接下载的图标
                        icon_img = Image.open(icon_path).convert("RGBA")
                        icon_img = icon_img.resize((50, 50), resample=RESAMPLE)
                        icon_img.putalpha(AbyssStatisticDraw._mask_50r7)
                        result.paste(icon_img, (char_start_x, team_start_y), icon_img)
                    else:
                        # 图标不存在时绘制文字
                        drawer.rectangle(
                            (
                                char_start_x,
                                team_start_y,
                                char_start_x + 50 - 1,
                                team_start_y + 50 - 1,
                            ),
                            fill=RARITY5 if char.rarity == 5 else RARITY4,
                            width=0,
                        )
                        drawer.text(
                            (
                                int(
                                    char_start_x + 25 - _gsf16.getlength(char.name) / 2
                                ),
                                int(team_start_y + 25 - _gsf16_char_height / 2),
                            ),
                            char.name,
                            fill=WHITE,
                            font=_gsf16,
                        )

        return result

    async def get_full_picture(self) -> BytesIO:
        """深境螺旋统计图生成入口

        - ``return BytesIO`` 深境螺旋统计图 BytesIO
        """

        # 图标下载
        download_tasks = [
            download_pic(
                f"https://t.akashadata.com/xstatic/img/c/s/{char.en_name}.jpg",
                "char",
                char.name,
            )
            for char in self.DATA.character_used_list
        ]
        await asyncio.gather(*download_tasks)
        download_tasks.clear()

        # 绘制图片各部分
        imgs: List[Image.Image] = await asyncio.gather(
            *[
                self.draw_top(
                    self.DATA.modify_time,
                    self.DATA.schedule_version_desc,
                    self.DATA.abyss_total_view,
                    self.DATA.last_rate,
                ),
                self.draw_middle(self.DATA.character_used_list),
                self.draw_buttom(
                    self.DATA.team_up_list,
                    self.DATA.team_down_list,
                    self.DATA.character_used_list,
                ),
            ]
        )
        result = Image.new("RGBA", (700, 1220), BG_COLOR)
        result.paste(imgs[0], (0, 0), imgs[0])
        result.paste(imgs[1], (0, imgs[0].height), imgs[1])
        result.paste(imgs[2], (0, imgs[0].height + imgs[1].height), imgs[2])

        # 返回 BytesIO
        buf = BytesIO()
        result = result.convert("RGB").save(buf, format="PNG")
        return buf

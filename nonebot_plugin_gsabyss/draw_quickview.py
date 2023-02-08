import json
import asyncio
from math import ceil
from io import BytesIO
from datetime import datetime
from typing import List, Union, Optional

from PIL import Image, ImageDraw
from nonebot.utils import run_sync

from .data_source import DL_DIR, HHW_CACHE, download_pic
from .models.hhw import (
    Blessing,
    Monsters,
    RewardItem,
    ChamberModel,
    VariantModel,
    PossibleBuffItem,
    ScheduleItemModel,
)
from .draw_utils import (
    BLACK,
    BROWN,
    WHITE,
    BG_CNT,
    ORANGE,
    YELLOW,
    BG_DEEP,
    BG_COLOR,
    BG_LIGHT,
    RESAMPLE,
    RARITY_BG,
    _f16,
    _f24,
    _gsf16,
    _gsf20,
    _gsf32,
    _gsf64,
    _half_img,
    _star_img,
    _coord_calc,
    _f24_char_height,
    _gsf16_char_height,
    _gsf20_char_height,
    _gsf32_char_height,
)


class AbyssQuickViewDraw:
    """深境螺旋速览绘图类"""

    def __init__(self, floor_id: int, chamber_id: int, schedule_key: str) -> None:
        """
        * ``param floor_id: int`` 深境螺旋层 ID
        * ``param chamber_id: int`` 深境螺旋间 ID
        * ``param schedule_key: str`` 深境螺旋日程数据键名
        """

        self.floor_id = floor_id
        self.floor_key = str(floor_id)
        self.chamber_id = chamber_id
        self.chamber_key = str(chamber_id)
        self.schedule_key = schedule_key
        self.DATA = json.loads(HHW_CACHE.read_text(encoding="UTF-8"))
        """Honey Hunter World 深渊解析数据"""
        self.picture_mode = "vertical" if chamber_id else "horizontal"
        """深渊速览图片模式。单间为竖直排版，全层为水平排版"""

    @property
    def variant_key(self) -> Optional[str]:
        """深境螺旋层变种键名"""

        if self.floor_id <= 8:
            return list(self.DATA["Floor"][self.floor_key].keys())[0]
        elif self.DATA["Schedule"].get(self.schedule_key):
            return self.DATA["Schedule"][self.schedule_key]["arrangement"][
                self.floor_key
            ]
        else:
            return

    @property
    def schedule_title(self) -> str:
        """深境螺旋日程标题"""
        dt = datetime.strptime(self.schedule_key, "%Y-%m-%d %H:%M:%S")
        return f"{dt.year}年{dt.month}月上" if dt.day < 16 else f"{dt.year}年{dt.month}月下"

    @run_sync
    def draw_header_blessing_para(self, blessing: Blessing) -> Image.Image:
        """绘制头部渊月祝福段落。宽度 530，高度自适应

        * ``param blessing: Blessing`` 深境螺旋日程数据 渊月祝福
        - ``return Image.Image`` 渊月祝福段落图像
        """

        result = Image.new("RGBA", (530, 200), BG_DEEP)
        drawer = ImageDraw.Draw(result)

        _width, height_acul = 0, 0
        for text_with_color in blessing.split_colorful_detail:
            color = text_with_color.color or WHITE
            for s in text_with_color.text:
                _x, height_acul, _width = _coord_calc(
                    s, _width, height_acul, result.width
                )
                drawer.text((_x, height_acul), s, fill=color, font=_gsf20)
        height_acul += _gsf20_char_height

        return result.crop((0, 0, 530, height_acul))

    @run_sync
    def draw_header_disorder_para(self, disorders: List[str]) -> Image.Image:
        """绘制头部地脉异常段落。宽度 530，高度自适应

        * ``param disorders: List[str]`` 深境螺旋单层变种数据 地脉异常
        - ``return Image.Image`` 地脉异常段落图像
        """

        result = Image.new("RGBA", (530, 300), BG_DEEP)
        drawer = ImageDraw.Draw(result)

        _width, height_acul = 0, 0
        for text in disorders:
            for s in text:
                x_s, height_acul, _width = _coord_calc(
                    s, _width, height_acul, result.width
                )
                drawer.text((x_s, height_acul), s, fill=WHITE, font=_gsf20)
            # 一条地脉异常绘制完毕，换行并从行首开始绘制
            _width = 0
            height_acul += _gsf20_char_height + 10
        height_acul -= 10

        return result.crop((0, 0, 530, height_acul))

    async def draw_header(
        self,
        blessing: Blessing,
        disorders: List[str],
    ) -> Image.Image:
        """绘制头部

        * ``param blessing: Blessing`` 深境螺旋日程数据 渊月祝福
        * ``param disorders: List[str]`` 深境螺旋单层变种数据 地脉异常
        - ``return Image.Image`` 头部图像
        """

        title = f"{self.schedule_title}   深渊速览 {self.floor_id} 层"
        imgs: List[Image.Image] = await asyncio.gather(
            *[
                self.draw_header_blessing_para(blessing),
                self.draw_header_disorder_para(disorders),
            ]
        )

        # 绘制基准坐标计算
        if self.picture_mode == "horizontal":
            # 水平排版
            width = 700 * 3
            height = 40 + max(
                [
                    _gsf32_char_height,
                    _f24_char_height * 2 + 10,
                    imgs[0].height,
                    imgs[1].height,
                ]
            )
            pos = {
                "title": (
                    int((700 - _gsf32.getlength(title)) / 2),
                    int((height - _gsf32_char_height) / 2),
                ),
                "bls_title": (700 + 30, int((height - _f24_char_height * 2 - 10) / 2)),
                "bls_para": (700 + 140, int((height - imgs[0].height) / 2)),
                "dsd_title": (700 * 2 + 30, int((height - _f24_char_height) / 2)),
                "dsd_para": (700 * 2 + 140, int((height - imgs[1].height) / 2)),
            }
        else:
            # 竖直排版
            bls_perch = max(_f24_char_height * 2 + 10, imgs[0].height)
            dsd_perch = max(_f24_char_height, imgs[1].height)
            width = 700
            height = sum([20, _gsf32_char_height, 20, bls_perch, 20, dsd_perch, 20])
            pos = {
                "title": (int((700 - _gsf32.getlength(title)) / 2), 20),
                "bls_title": (
                    30,
                    40
                    + _gsf32_char_height
                    + int((bls_perch - _f24_char_height * 2 - 10) / 2),
                ),
                "bls_para": (
                    140,
                    40 + _gsf32_char_height + int((bls_perch - imgs[0].height) / 2),
                ),
                "dsd_title": (
                    30,
                    60
                    + _gsf32_char_height
                    + bls_perch
                    + int((dsd_perch - _f24_char_height) / 2),
                ),
                "dsd_para": (
                    140,
                    60
                    + _gsf32_char_height
                    + bls_perch
                    + int((dsd_perch - imgs[1].height) / 2),
                ),
            }

        # 绘制
        result = Image.new("RGBA", (width, height), BG_DEEP)
        drawer = ImageDraw.Draw(result)

        # 第一部分：标题
        drawer.text(pos["title"], title, fill=YELLOW, font=_gsf32)
        # 第二部分：渊月祝福
        drawer.text(pos["bls_title"], "渊月祝福", fill=YELLOW, font=_f24)
        drawer.text(
            (pos["bls_title"][0], int(pos["bls_title"][1] + _f24_char_height + 10)),
            blessing.name,
            fill=YELLOW,
            font=_f24,
        )
        result.paste(imgs[0], pos["bls_para"], imgs[0])
        # 竖直排版时第二部分与第三部分之间绘制直线分割
        if self.picture_mode == "vertical":
            drawer.line(
                (25, pos["dsd_para"][1] - 9, 700 - 25, pos["dsd_para"][1] - 9),
                fill=BG_CNT,
                width=1,
            )
        # 第三部分：地脉异常
        drawer.text(pos["dsd_title"], "地脉异常", fill=YELLOW, font=_f24)
        result.paste(imgs[1], pos["dsd_para"], imgs[1])

        return result

    @run_sync
    def draw_chamber_top(
        self,
        conditions: List[str],
        rewards: List[RewardItem],
        chamber_id_: Optional[int] = None,
    ) -> Image.Image:
        """绘制单间顶部。包含间标题、挑战目标、间之秘宝

        * ``param conditions: List[str]`` 深境螺旋单间数据 挑战目标
        * ``param rewards: List[RewardItem]`` 深境螺旋单间数据 间之秘宝
        * ``param chamber_id_: Optional[int] = None`` 深境螺旋间 ID。获取全层时每间需要分别传入
        - ``return Image.Image`` 单间顶部图像
        """

        result = Image.new("RGBA", (700, 165), BG_COLOR)
        drawer = ImageDraw.Draw(result)

        # 标题水印
        this_chamber_id = chamber_id_ if chamber_id_ is not None else self.chamber_id
        chamber_title = f"{self.floor_id}-{this_chamber_id}"
        drawer.text(
            (700 - _gsf64.getlength(chamber_title) - 30, 10),
            chamber_title,
            fill=BLACK,
            font=_gsf64,
        )
        # 挑战目标
        drawer.text((25, 25), "挑战目标", fill=YELLOW, font=_f24)
        drawer.rectangle((30, 65, 350 - 1, 165 - 1), fill=BG_LIGHT, width=0)
        for c_idx, cond in enumerate(conditions):
            result.paste(_star_img, (43, 73 + c_idx * 30), _star_img)
            drawer.text(
                (80, int(73 + c_idx * 30 + 24 / 2 - _gsf20.getbbox(cond)[-1] / 2)),
                cond,
                fill=WHITE,
                font=_gsf20,
            )
        # 间之秘宝
        drawer.text((365, 55), "间之秘宝", fill=YELLOW, font=_f24)
        for r_idx, reward in enumerate(rewards):
            # 稀有度背景
            drawer.rectangle(
                (370 + r_idx * 60, 95, 370 + 60 + r_idx * 60 - 1, 155 - 1),
                fill=RARITY_BG[reward.rarity - 1],
                width=0,
            )
            # 秘宝图标
            icon_path = DL_DIR / f"reward/{reward.name}.png"
            if icon_path.exists():
                icon_img = Image.open(icon_path).convert("RGBA")
                # HHW 物品图标可能非正方形，使较长边的长度缩放至 50px
                icon_img = icon_img.resize(
                    (50, int(icon_img.height * 50 / icon_img.width))
                    if icon_img.width >= icon_img.height
                    else (int(icon_img.width * 50 / icon_img.height), 50),
                    resample=RESAMPLE,
                )
                result.paste(
                    icon_img,
                    (
                        int(370 + r_idx * 60 + (60 - icon_img.width) / 2),
                        int(95 + (60 - icon_img.height) / 2),
                    ),
                    icon_img,
                )
            # 数量背景
            cnt_bg = Image.new("RGBA", (60, 20), BG_CNT)
            result.paste(cnt_bg, (370 + r_idx * 60, 145), cnt_bg)
            # 数量
            cnt_str = str(reward.count)
            drawer.text(
                (
                    int(370 + r_idx * 60 + 60 / 2 - _f16.getlength(cnt_str) / 2),
                    int(145 + 20 - _f16.getbbox(cnt_str)[-1] - 2),
                ),
                cnt_str,
                fill=WHITE,
                font=_f16,
            )

        return result

    @run_sync
    def draw_chamber_middle(
        self, monster_lvl_overwrite: int, monsters: Monsters
    ) -> Image.Image:
        """绘制单间中间。包含讨伐列表

        * ``param monster_lvl_overwrite: int`` 深境螺旋单间数据 本间敌人等级
        * ``param monsters: Monsters`` 深境螺旋单间数据 讨伐列表
        - ``return Image.Image`` 单间中间图像
        """

        # 预计算讨伐列表区域高度
        height = sum(
            (30 + ceil(len(monsters.dict()[_k]) / 2) * 50)
            for _k in monsters.dict().keys()
            if monsters.dict()[_k]
        )

        result = Image.new("RGBA", (700, 65 + height - 20), BG_COLOR)
        drawer = ImageDraw.Draw(result)

        # 标题
        drawer.text((25, 25), "讨伐列表", fill=YELLOW, font=_f24)
        drawer.text(
            (115, 25 + 8), f"敌人等级 Lv.{monster_lvl_overwrite}", fill=BROWN, font=_f16
        )
        # 讨伐列表
        y_add = 0
        for half_idx, monsters_half in enumerate(
            [monsters.first_half, monsters.second_half]
        ):
            # 如果没有下半则跳过绘制
            if not monsters_half:
                continue
            # 背景
            _bg_height = ceil(len(monsters_half) / 2) * 50 + 10
            drawer.rectangle(
                (30, 65 + y_add, 670 - 1, 65 + y_add + _bg_height - 1),
                fill=BG_LIGHT,
                width=0,
            )
            # 半间图标
            if len([_k for _k in monsters.dict().keys() if monsters.dict()[_k]]) == 2:
                if half_idx == 0:
                    half_icon = _half_img
                else:
                    # 下半间的图标由原图标上下翻转生成
                    half_icon = _half_img.transpose(Image.FLIP_TOP_BOTTOM)
                result.paste(half_icon, (670 - 12, 65 + y_add - 12), half_icon)
            # 敌人
            for m_idx, monster in enumerate(monsters_half):
                _idx_from_one = m_idx + 1
                icon_x = 40 if (_idx_from_one % 2) else 360
                icon_y = 65 + y_add + 10 + (ceil(_idx_from_one / 2) - 1) * 50
                # rarity_bg = RARITY_BG[monster.rRarity - 1]
                rarity_bg = RARITY_BG[0]  # 怪物背景一律使用 1 级
                drawer.rectangle(
                    (icon_x, icon_y, icon_x + 40 - 1, icon_y + 40 - 1),
                    fill=rarity_bg,
                    width=0,
                )
                icon_path = DL_DIR / f"monster/{monster.name}.png"
                if icon_path.exists():
                    icon_img = Image.open(icon_path).convert("RGBA")
                    icon_img = icon_img.resize((38, 38), resample=RESAMPLE)
                    result.paste(icon_img, (icon_x + 1, icon_y + 1), icon_img)
                drawer.text(
                    (
                        icon_x + 55,
                        int(icon_y + 40 / 2 - _gsf20.getbbox(monster.name)[-1] / 2),
                    ),
                    monster.name,
                    fill=YELLOW,
                    font=_gsf20,
                )
            # 半间讨伐列表绘制完毕
            y_add += _bg_height + 20

        return result

    @run_sync
    def draw_chamber_buttom(
        self, possible_buff: List[List[PossibleBuffItem]]
    ) -> Image.Image:
        """绘制单间底部。包含深秘降福

        * ``param possible_buff: List[List[PossibleBuffItem]]`` 深境螺旋单间数据 深秘降福
        - ``return Image.Image`` 单间底部图像
        """

        # 估算深秘降福区域高度
        height_est = 80 + sum(len(buffs) for buffs in possible_buff) * 50

        result = Image.new("RGBA", (700, 65 + height_est), BG_COLOR)
        drawer = ImageDraw.Draw(result)

        # 标题
        drawer.text((25, 25), "深秘降福", fill=YELLOW, font=_f24)
        drawer.rectangle((30, 65, 670 - 1, 65 + height_est - 1), fill=BG_LIGHT, width=0)
        # 深秘降福
        _max_width = 95 + 550
        height_acul = 65 + 20
        for b_idx, buffs in enumerate(possible_buff):
            drawer.text(
                (50, height_acul - 2), f"#{b_idx + 1}", fill=ORANGE, font=_gsf20
            )
            for buff in buffs:
                text = f"{buff.buff}{buff.time}"
                _width = 95
                for s_idx, s in enumerate(text):
                    color = WHITE if s_idx < len(text) - 4 else BROWN
                    _x, height_acul, _width = _coord_calc(
                        s, _width, height_acul, _max_width, 95, 16
                    )
                    drawer.text((_x, height_acul), s, fill=color, font=_gsf16)
                height_acul += _gsf16_char_height + 10
            height_acul += 10

        # 根据实际绘制占用高度填补背景色
        drawer.rectangle(
            (0, height_acul, 700 - 1, height_acul + 20 - 1), fill=BG_COLOR, width=0
        )
        return result.crop((0, 0, 700, height_acul + 20))

    async def draw_chamber(
        self, chamber_data: ChamberModel, chamber_id_: Optional[int] = None
    ) -> Image.Image:
        """绘制单间

        * ``param chamber_data: ChamberModel`` 深境螺旋单间数据
        * ``param chamber_id_: Optional[int] = None`` 深境螺旋间 ID。获取全层时每间需要分别传入
        - ``return Image.Image`` 单间图像
        """

        # 下载图片素材。包括间之秘宝、敌人
        dl_tasks = [
            download_pic(reward.icon, "reward", reward.name)
            for reward in chamber_data.reward
        ]
        for monsters_half in [
            chamber_data.monsters.first_half,
            chamber_data.monsters.second_half,
        ]:
            if monsters_half:
                dl_tasks.extend(
                    [
                        download_pic(monster.icon, "monster", monster.name)
                        for monster in monsters_half
                    ]
                )
        await asyncio.gather(*dl_tasks)
        dl_tasks.clear()

        # 获取单间图片各部分
        tasks = [
            self.draw_chamber_top(
                chamber_data.conditions, chamber_data.reward, chamber_id_
            ),
            self.draw_chamber_middle(
                chamber_data.monster_lvl_overwrite, chamber_data.monsters
            ),
            self.draw_chamber_buttom(chamber_data.possible_buff),
        ]
        imgs: List[Image.Image] = await asyncio.gather(*tasks)
        # 合并各部分
        chamber = Image.new("RGBA", (700, sum(img.height for img in imgs)))
        paste_height = 0
        for img in imgs:
            chamber.paste(img, (0, paste_height), img)
            paste_height += img.height

        return chamber

    async def get_full_picture(self) -> Union[str, BytesIO]:
        """深境螺旋速览图生成入口

        - ``return Union[str, BytesIO]`` 深境螺旋速览图 BytesIO。出错时返回字符串
        """

        DATA = self.DATA
        floor_key = self.floor_key
        variant_key = self.variant_key
        schedule_key = self.schedule_key
        schedule_title = self.schedule_title
        if not variant_key:
            return f"没有找到「{schedule_title}」的深渊数据哦！"

        variant_data = VariantModel.parse_obj(DATA["Floor"][floor_key][variant_key])
        schedule_data = ScheduleItemModel.parse_obj(DATA["Schedule"][schedule_key])

        # 根据深渊速览图片模式决定各部分图片合并规则
        if self.picture_mode == "vertical":
            imgs: List[Image.Image] = await asyncio.gather(
                *[
                    self.draw_header(
                        schedule_data.blessing,
                        variant_data.disorders,
                    ),
                    self.draw_chamber(variant_data.chambers[self.chamber_id - 1]),
                ]
            )
            result = Image.new("RGBA", (700, imgs[0].height + imgs[1].height), BG_COLOR)
            result.paste(imgs[0], (0, 0), imgs[0])
            result.paste(imgs[1], (0, imgs[0].height), imgs[1])
        else:  # "horizontal"
            tasks = [
                self.draw_header(
                    schedule_data.blessing,
                    variant_data.disorders,
                )
            ]
            tasks.extend(
                [
                    self.draw_chamber(
                        variant_data.chambers[_idx],
                        _idx + 1,
                    )
                    for _idx in range(3)
                ]
            )
            imgs: List[Image.Image] = await asyncio.gather(*tasks)
            result = Image.new(
                "RGBA",
                (700 * 3, imgs[0].height + max(i.height for i in imgs[1:])),
                BG_COLOR,
            )
            result.paste(imgs[0], (0, 0), imgs[0])
            result.paste(imgs[1], (0, imgs[0].height), imgs[1])
            result.paste(imgs[2], (700, imgs[0].height), imgs[2])
            result.paste(imgs[3], (700 * 2, imgs[0].height), imgs[3])

        # 返回 BytesIO
        buf = BytesIO()
        result = result.convert("RGB").save(buf, format="JPEG", quality=100)
        return buf

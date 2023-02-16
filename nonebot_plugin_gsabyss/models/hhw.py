from re import sub, findall
from typing import List, Optional

from pydantic import Field, BaseModel, validator


class CommonItem(BaseModel):
    """通用物品数据"""

    icon: str = Field(..., alias="Icon")
    """物品图标 URL"""
    id: int = Field(..., alias="Id")
    """物品 HHW ID。似乎不可用于其他数据库"""
    rarity: int = Field(..., alias="Rarity")
    """物品稀有度"""
    name: str = Field(..., alias="Name")
    """物品名称。跟随网页语言"""

    @validator("icon", pre=True)
    def _parse_raw_icon(cls, v: str) -> str:
        """转换物品图标 URL 为高清图片 URL"""
        return sub(r"(\w+_\w?\d+)_\d+\.webp$", r"\1.webp", v)


class RewardItem(CommonItem):
    """秘宝物品数据"""

    count: int = Field(..., alias="Count")
    """物品数量"""


class PossibleBuffItem(BaseModel):
    """深境螺旋单条深秘降福数据"""

    icon: str = Field(..., alias="Icon")
    """图标 URL"""
    buff: str = Field(..., alias="Buff")
    """效果"""
    time: str = Field(..., alias="Time")
    """持续时间"""

    @validator("time", pre=True)
    def _parse_chs_time(cls, v: str) -> str:
        """转换持续时间为中文字符"""
        if v in ["此层生效", "本间生效", "立即生效"]:
            return v
        return {"Whole Floor": "此层生效", "Single Chamber": "本间生效"}.get(v, "立即生效")


class Monsters(BaseModel):
    """深境螺旋单间讨伐列表数据"""

    first_half: List[CommonItem] = Field(..., alias="FirstHalf")
    """上半讨伐列表"""
    second_half: Optional[List[CommonItem]] = Field(None, alias="SecondHalf")
    """下半讨伐列表。仅渊月螺旋含有此数据"""


class ChamberModel(BaseModel):
    """深境螺旋单间数据"""

    monster_lvl_overwrite: int = Field(..., alias="MonsterLvlOverwrite")
    """本间敌人等级"""
    teams: int = Field(..., alias="Teams")
    """队伍数量。用于判断是否路径分岔"""
    conditions: List[str] = Field(..., alias="Conditions")
    """挑战目标"""
    possible_buff: List[List[PossibleBuffItem]] = Field(..., alias="PossibleBuff")
    """深秘降福。含 3 个子列表，实际战斗时从 3 个子列表中各随机抽取 1 个"""
    monsters: Monsters = Field(..., alias="Monsters")
    """讨伐列表"""
    reward: List[RewardItem] = Field(..., alias="Reward")
    """间之秘宝"""

    @validator("conditions", pre=True)
    def _parse_chs_conditionss(cls, v: List[str]) -> List[str]:
        """转换挑战目标为中文字符"""
        return [
            "挑战剩余时间大于{}秒".format(findall(r"\d+", cond)[0])
            if cond.endswith("s")
            else "守护目标完整度大于{}%".format(findall(r"\d+", cond)[0])
            if cond.endswith("%")
            else cond
            for cond in v
        ]

    @validator("monster_lvl_overwrite", pre=True)
    def _parse_actual_lvl(cls, v: int) -> int:
        """转换本间敌人等级为游戏内实际等级"""
        return v + 1


class VariantModel(BaseModel):
    """深境螺旋单层变种数据"""

    icon: str = Field(..., alias="Icon")
    """图标 URL"""
    monster_lvl_global: int = Field(..., alias="MonsterLvlGlobal")
    """全局敌人等级"""
    teams: int = Field(..., alias="Teams")
    """队伍数量。用于判断是否路径分岔"""
    unlock: int = Field(..., alias="Unlock")
    """通关需求渊星数。一般为 `6`"""
    disorders: List[str] = Field(..., alias="Disorders")
    """地脉异常"""
    reward: List[List[RewardItem]] = Field(..., alias="Reward")
    """星之秘宝。含 3 个子列表，依次为获得渊星 3 星、6 星、9 星的秘宝"""
    chambers: List[ChamberModel] = Field(..., alias="Chambers")
    """间数据"""

    @validator("disorders", pre=True)
    def _remove_disorder_test(cls, v: List[str]) -> List[str]:
        """去除地脉异常测试字符"""
        return [
            string
            for string in v
            if not any(string.startswith(_test) for _test in ["(test)", "n/a"])
        ]


class Arrangement(BaseModel):
    """渊月螺旋变种安排数据"""

    floor_9: int = Field(..., alias="9")
    """第 9 层变种 ID"""
    floor_10: int = Field(..., alias="10")
    """第 10 层变种 ID"""
    floor_11: int = Field(..., alias="11")
    """第 11 层变种 ID"""
    floor_12: int = Field(..., alias="12")
    """第 12 层变种 ID"""


class ColorfulText(BaseModel):
    """多彩文本数据"""

    color: str
    """文本颜色"""
    text: str
    """文本内容"""


class Blessing(BaseModel):
    """深境螺旋渊月祝福数据"""

    icon: str = Field(..., alias="Icon")
    """图标 URL"""
    name: str = Field(..., alias="Name")
    """名称。跟随网页语言"""
    detail: str = Field(..., alias="Detail")
    """效果纯文本"""
    colorful_detail: str = Field(..., alias="ColorfulDetail")
    """效果多彩文本。包含 `<color=#f39000ff>` 等标签"""

    @property
    def split_colorful_detail(self) -> List[ColorfulText]:
        """分割效果多彩文本为特定形式的字典列表"""
        raw = self.colorful_detail.replace("<br>", "").replace(" ", "")
        highlights = [_m[0] for _m in findall(r"<color=#f39000ff>(.+?)(，|。)", raw)]
        raw = sub(r"<color=#f39000ff>(.+?)(，|。)", r" \1 \2", raw)
        raw = sub(r"</?color=#f39000ff>", "", raw)
        return [
            ColorfulText.parse_obj(
                {"color": "#f39000ff" if _s in highlights else "", "text": _s}
            )
            for _s in raw.split()
        ]


class ScheduleItemModel(BaseModel):
    """深境螺旋日程数据"""

    arrangement: Arrangement
    """渊月螺旋变种安排"""
    blessing: Blessing
    """渊月祝福"""

from typing import List, Literal

from pydantic import BaseModel


class TeamItem(BaseModel):
    """队伍数据"""

    ac: int
    """数量 `all_count`"""
    mr: str
    """满星率 `maxstar_rate`"""
    uc: str
    """上半数量 `up_count`"""
    dc: str
    """下半数量 `down_count`"""
    ud: str
    """上下比 `up_down`"""
    umr: str
    """上半满星率 `up_maxstar_rate`"""
    dmr: str
    """下半满星率 `down_maxstar_rate`"""
    tl: List[int]
    """队伍 `team_character_list`"""


class AbyssTotalView(BaseModel):
    """深渊数据汇总数据"""

    avg_star: str
    """人均摘星。即摘星总数 / 出战人数"""
    avg_battle_count: str
    """平均战斗次数。即战斗次数总和 / 出战人数"""
    avg_maxstar_battle_count: str
    """满星平均战斗次数。即满星总次数 / 满星人数"""
    pass_rate: str
    """通关比例。即通关 12-3 人数 / 出战人数"""
    maxstar_rate: str
    """满星比例。即满星人数 / 出战人数"""
    maxstar_12_rate: str
    """12 场 36 星比例。即 12 场 36 星人数 / 出战人数"""
    person_war: int
    """出战人数"""
    person_pass: int
    """通关人数"""
    maxstar_person: int
    """满星人数"""


class LastRate(BaseModel):
    """深渊数据汇总相比上期变化数据"""

    avg_star: str
    """人均摘星相比上期变化"""
    pass_rate: str
    """通关比例相比上期变化"""
    maxstar_rate: str
    """满星比例相比上期变化"""
    avg_battle_count: str
    """平均战斗次数相比上期变化"""
    avg_maxstar_battle_count: str
    """满星平均战斗次数相比上期变化"""
    maxstar_12_rate: str
    """12 场 36 星比例相比上期变化"""


class MaxstarPlayerData(BaseModel):
    """满星玩家数据"""

    title: Literal["满星率"]
    """标题"""
    y_list: List[str]
    """满星率百分数列表"""
    x_list: List[str]
    """等级列表。子字符串格式为 `Lv.60`"""


class PassPlayerData(BaseModel):
    """通关玩家数据"""

    title: Literal["通关率"]
    """标题"""
    y_list: List[str]
    """通关率百分数列表"""
    x_list: List[str]
    """等级列表。子字符串格式为 `Lv.60`"""


class PlayerLevelData(BaseModel):
    """不同等级战绩数据"""

    maxstar_player_data: MaxstarPlayerData
    """满星玩家数据"""
    pass_player_data: PassPlayerData
    """通关玩家数据"""


class PalyerCountLevelData(BaseModel):
    """不同等级出战人数数据"""

    player_count_data: List[int]
    """人数列表"""
    level_data: List[str]
    """等级列表。子字符串格式为 `Lv.60`"""


class LevelData(BaseModel):
    """参与统计玩家等级数据"""

    player_level_data: PlayerLevelData
    """不同等级战绩数据"""
    palyer_count_level_data: PalyerCountLevelData
    """不同等级出战人数数据"""


class CharacterItem(BaseModel):
    """角色数据"""

    avatar_id: int
    """角色 ID"""
    maxstar_person_had_count: int
    """满星玩家持有数"""
    maxstar_person_use_count: int
    """满星玩家使用数"""
    value: float
    """使用率百分数"""
    used_index: int
    """使用率排行"""
    name: str
    """名称"""
    en_name: str
    """英文名称。首字母为小写"""
    icon: str
    """图标名称。首字母为大写"""
    element: Literal["pyro", "hydro", "anemo", "electro", "dendro", "cryo", "geo"]
    """元素类型"""
    rarity: int
    """稀有度"""


class AkashaAbyssData(BaseModel):
    """虚空数据库深渊统计数据"""

    schedule_id: int
    """深渊版本 ID"""
    modify_time: str
    """更新时间。格式为 `%Y-%m-%d %H:%M`"""
    schedule_version_desc: str
    """深渊版本描述"""
    team_list: List[TeamItem]
    """队伍列表。按数量排序"""
    team_up_list: List[TeamItem]
    """上半队伍列表。按上半数量排序"""
    team_down_list: List[TeamItem]
    """下半队伍列表。按下半数量排序"""
    abyss_total_view: AbyssTotalView
    """深渊数据汇总数据"""
    last_rate: LastRate
    """深渊数据汇总相比上期变化数据"""
    level_data: LevelData
    """参与统计玩家等级数据"""
    character_used_list: List[CharacterItem]
    """角色列表。按使用率排序"""

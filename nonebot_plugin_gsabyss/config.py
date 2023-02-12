from pathlib import Path

from nonebot import get_driver
from pydantic import Extra, BaseModel


class Config(BaseModel, extra=Extra.ignore):
    gsabyss_dir: Path = Path("data/gsabyss")
    """本地缓存目录。默认 `data/gsabyss`"""
    gsabyss_priority: int = 10
    """响应优先级。默认 10"""


plugin_config = Config.parse_obj(get_driver().config)
plugin_config.gsabyss_dir.mkdir(parents=True, exist_ok=True)

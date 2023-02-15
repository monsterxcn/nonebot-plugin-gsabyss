from typing import Tuple, Union, Literal

from PIL import Image, ImageDraw, ImageFont

from .data_source import download_init_res


def font(size: int, family: str = "HYWH-85W") -> ImageFont.FreeTypeFont:
    """绘图字体获取，默认汉仪文黑"""

    font_path = download_init_res(f"{family}.ttf")
    return ImageFont.truetype(str(font_path), size=size)


_gsf64 = font(64)
"""汉仪文黑 64 号字体"""
_gsf32 = font(32)
"""汉仪文黑 32 号字体"""
_f24 = font(24, "SmileySans-Oblique")
"""得意黑 24 号字体"""
_gsf20 = font(20)
"""汉仪文黑 20 号字体"""
_f16 = font(16, "SmileySans-Oblique")
"""得意黑 16 号字体"""
_gsf16 = font(16)
"""汉仪文黑 16 号字体"""

_gsf32_char_height = _gsf32.getbbox("高度")[-1]
"""汉仪文黑 32 号字体高度"""
_f24_char_height = _f24.getbbox("高度")[-1]
"""得意黑 24 号字体高度"""
_gsf20_char_height = _gsf20.getbbox("高度")[-1]
"""汉仪文黑 20 号字体高度"""
_gsf16_char_height = _gsf16.getbbox("高度")[-1]
"""汉仪文黑 16 号字体高度"""

RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS
_star_img_path = download_init_res("star_icon.png")
_star_img = (
    Image.open(_star_img_path).resize((24, 24), resample=RESAMPLE).convert("RGBA")
)
"""渊星图标"""
_half_img_path = download_init_res("half_icon.png")
_half_img = (
    Image.open(_half_img_path).resize((24, 24), resample=RESAMPLE).convert("RGBA")
)
"""半间图标"""

BG_COLOR = "#3F4454"
BG_LIGHT = "#484D5C"
BG_DEEP = "#333643"
BG_CNT = "rgba(74, 81, 101, 250)"  # "#4A5165"
YELLOW = "#CFBD93"
ORANGE = "#E59435"
WHITE = "#EBE5D9"
BLACK = "#51545C"
BROWN = "#AB9F83"

POS_COLOR = "#F1416C"
POS_BG = "#FFF5F8"
NEG_COLOR = "#50CD89"
NEG_BG = "#E8FFF3"

RARITY1 = "#818486"
RARITY2 = "#5A977A"
RARITY3 = "#5987AD"
RARITY4 = "#9470BB"
RARITY5 = "#C87C24"
RARITY_BG = [RARITY1, RARITY2, RARITY3, RARITY4, RARITY5]
"""物品稀有度背景"""


def _coord_calc(
    s: str,
    start_width: int,
    start_height: int,
    max_width: int,
    init_width: int = 0,
    font_size: Literal[16, 20] = 20,
) -> Tuple[int, int, int]:
    """字符绘制坐标计算。注意传入参数与传出参数对应关系

    * ``param s: str`` 待绘制字符
    * ``param start_width: int`` 绘制起点横轴初始坐标
    * ``param start_height: int`` 绘制起点纵轴初始坐标
    * ``param max_width: int`` 横轴允许的最大坐标，即判断字符是否需要换行的横轴坐标
    * ``param init_width: int = 0`` 横轴允许的最小坐标，即字符需要换行时回归的横轴坐标
    * ``param font_size: Literal[16, 20] = 20`` 字体大小
    - ``return: Tuple[int, int, int]`` 绘制起点横轴坐标、绘制起点纵轴坐标、下个字绘制起点横轴初始坐标
    """

    if font_size == 20:
        _font, line_height, space = _gsf20, _gsf20_char_height, 10
    else:
        _font, line_height, space = _gsf16, _gsf16_char_height, 6

    if start_width + _font.getlength(s) <= max_width:
        coord_x = start_width
        start_width += _font.getlength(s)
    else:
        coord_x, start_width = init_width, init_width + _font.getlength(s)
        start_height += line_height + space

    # 当前字符绘制坐标为 (coord_x, start_height)
    # 下个字符绘制坐标初始为 (start_width, start_height)
    return coord_x, start_height, start_width


def rounded_rectangle_mask(
    width: Union[int, float] = 50,
    height: Union[int, float] = 50,
    radius: int = 7,
    fill: str = BG_LIGHT,
    scale: int = 5,
    mask: bool = False,
) -> Image.Image:
    """圆角矩形生成

    * ``param width: Union[int, float] = 50`` 矩形宽度
    * ``param height: Union[int, float] = 50`` 矩形高度
    * ``param radius: int = 7`` 圆角弧度
    * ``param fill: str = BG_LIGHT`` 矩形区域填充色。返回遮罩时为完全不透明填充
    * ``param scale: int = 5`` 矩形缩放系数。抗锯齿作用
    * ``param mask: bool = False`` 是否返回遮罩
    - ``return: Image.Image`` 圆角矩形
    """

    scaled_width, scaled_height = int(width * scale), int(height * scale)
    result = Image.new("L" if mask else "RGBA", (scaled_width, scaled_height), 0)
    ImageDraw.Draw(result).rounded_rectangle(
        (0, 0, scaled_width, scaled_height),
        radius=radius * scale,
        fill=255 if mask else fill,
        outline=None,
        width=0,
    )
    return result.resize((int(width), int(height)), resample=RESAMPLE)

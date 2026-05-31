import math
from config import (
    ICON_SIZE,
    ICON_BORDER_WIDTH,
    ICON_COLOR_BORDER,
    ICON_COLOR_EMPTY,
    ICON_COLOR_LINE,
    LINE_WIDTH,
    ICON_COLOR_PAUSE,
    ICON_COLOR_PAUSE_BG,
    LONGITUDES,
)
from PIL import Image, ImageDraw


def draw_icon(
    size: int = ICON_SIZE,
    border_width: int = ICON_BORDER_WIDTH,
    border_color: tuple = ICON_COLOR_BORDER,
    fill_color: tuple = ICON_COLOR_EMPTY,
    line_color: tuple = ICON_COLOR_LINE,
    flash_state: int = -1,
):
    """
    创建一个地球仪图标

    参数:
        size: 图标大小（宽高相同）
        border_width: 边框宽度（像素）
        border_color: 边框颜色（RGBA元组）
        fill_color: 填充颜色（RGBA元组）
        line_color: 线条颜色（RGBA元组）
        flash_state: 闪烁状态 (-1=不闪烁, 0-5=熄灭连续4个条带)

    返回:
        PIL Image对象（RGBA模式，透明背景）
    """
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    center = size // 2
    radius = (size - border_width) // 2
    inner_radius = (size - 2 * border_width) // 2

    border_box = [(0, 0), (size - 1, size - 1)]
    draw.ellipse(border_box, fill=border_color)

    if border_width > 0:
        inner_size = size - 2 * border_width
        inner_box = [
            (border_width, border_width),
            (border_width + inner_size - 1, border_width + inner_size - 1),
        ]
        draw.ellipse(inner_box, fill=fill_color)

    for lat in LONGITUDES:
        lat_rad = math.radians(lat)
        y_offset = int(inner_radius * math.sin(lat_rad))
        half_width = int(inner_radius * math.cos(lat_rad)) - LINE_WIDTH // 2

        if half_width > 0:
            y = center - y_offset
            x1 = center - half_width
            x2 = center + half_width
            draw.line([(x1, y), (x2, y)], fill=line_color, width=LINE_WIDTH)

    for lon in LONGITUDES:
        lon_rad = math.radians(lon)

        points = []
        for lat in range(-87, 88, 5):
            lat_rad = math.radians(lat)
            x = center + int(inner_radius * math.cos(lat_rad) * math.sin(lon_rad))
            y = center - int(inner_radius * math.sin(lat_rad))
            points.append((x, y))

        if len(points) >= 2:
            draw.line(points, fill=line_color, width=LINE_WIDTH)

    if flash_state >= 0 and flash_state <= 5:
        strips_to_extinguish = [(flash_state + i) % 6 for i in range(3)]

        for y in range(size):
            for x in range(size):
                dx = x - center
                dy = center - y

                dist_sq = dx * dx + dy * dy
                if dist_sq > radius * radius:
                    continue

                if (
                    border_width <= x < size - border_width
                    and border_width <= y < size - border_width
                ):
                    dist = math.sqrt(dist_sq)
                    if dist < 1:
                        lon_deg: float = 0
                    else:
                        cos_lat = (
                            math.sqrt(1 - (dy / radius) ** 2) if abs(dy) < radius else 0
                        )
                        if cos_lat < 0.001:
                            lon_deg = 0.0
                        else:
                            sin_lon = dx / (radius * cos_lat)
                            sin_lon = max(-1, min(1, sin_lon))
                            lon_rad = math.asin(sin_lon)
                            lon_deg = math.degrees(lon_rad)

                    strip_idx = -1
                    for i in range(len(LONGITUDES) - 1):
                        if LONGITUDES[i] <= lon_deg < LONGITUDES[i + 1]:
                            strip_idx = i
                            break

                    if strip_idx == -1:
                        if lon_deg >= LONGITUDES[-1]:
                            strip_idx = len(LONGITUDES) - 2
                        elif lon_deg < LONGITUDES[0]:
                            strip_idx = 0

                    if strip_idx in strips_to_extinguish:
                        image.putpixel((x, y), ICON_COLOR_EMPTY)

    return image


def draw_icon_pause(
    size: int = ICON_SIZE,
    border_width: int = ICON_BORDER_WIDTH,
    border_color: tuple = ICON_COLOR_BORDER,
    fill_color: tuple = ICON_COLOR_EMPTY,
    line_color: tuple = ICON_COLOR_LINE,
    flash_state: int = -1,
):
    """
    创建一个带暂停符号的地球仪图标（右下角有圆圈-暂停符号）

    参数:
        size: 图标大小（宽高相同）
        border_width: 边框宽度（像素）
        border_color: 边框颜色（RGBA元组）
        fill_color: 地球仪填充颜色（RGBA元组）
        line_color: 线条颜色（RGBA元组）
        flash_state: 闪烁状态 (-1=不闪烁, 0-5=熄灭连续4个条带)

    返回:
        PIL Image对象（RGBA模式，透明背景）
    """
    image = draw_icon(
        size, border_width, border_color, fill_color, line_color, flash_state
    )
    draw = ImageDraw.Draw(image)

    badge_radius = size // 4
    badge_center_x = size - badge_radius
    badge_center_y = size - badge_radius

    draw.ellipse(
        [
            (badge_center_x - badge_radius, badge_center_y - badge_radius),
            (badge_center_x + badge_radius, badge_center_y + badge_radius),
        ],
        fill=ICON_COLOR_PAUSE_BG,
        outline=border_color,
    )

    pause_bar_width = badge_radius // 3
    pause_bar_height = badge_radius
    pause_gap = pause_bar_width // 2

    bar1_x1 = badge_center_x - pause_gap - pause_bar_width
    bar1_x2 = badge_center_x - pause_gap
    bar2_x1 = badge_center_x + pause_gap
    bar2_x2 = badge_center_x + pause_gap + pause_bar_width

    bar_y1 = badge_center_y - pause_bar_height // 2
    bar_y2 = badge_center_y + pause_bar_height // 2

    draw.rectangle([(bar1_x1, bar_y1), (bar1_x2, bar_y2)], fill=ICON_COLOR_PAUSE)
    draw.rectangle([(bar2_x1, bar_y1), (bar2_x2, bar_y2)], fill=ICON_COLOR_PAUSE)

    return image


def generate_all_icons():
    """
    预生成所有可能用到的图标并缓存到内存

    返回:
        dict: {
            'normal': {icon_type: {flash_state: Image}},
            'paused': {icon_type: {flash_state: Image}}
        }
    """
    from config import (
        ICON_COLOR_EMPTY,
        ICON_COLOR_INFO,
        ICON_COLOR_WARN,
        ICON_COLOR_ERROR,
    )

    icon_colors = {
        0: ICON_COLOR_EMPTY,
        1: ICON_COLOR_INFO,
        2: ICON_COLOR_WARN,
        3: ICON_COLOR_ERROR,
    }

    all_icons = {"normal": {}, "paused": {}}

    for icon_type, color in icon_colors.items():
        all_icons["normal"][icon_type] = {}
        all_icons["paused"][icon_type] = {}

        all_icons["normal"][icon_type][-1] = draw_icon(fill_color=color, flash_state=-1)
        all_icons["paused"][icon_type][-1] = draw_icon_pause(
            fill_color=color, flash_state=-1
        )

        for flash_state in range(6):
            all_icons["normal"][icon_type][flash_state] = draw_icon(
                fill_color=color, flash_state=flash_state
            )
            all_icons["paused"][icon_type][flash_state] = draw_icon_pause(
                fill_color=color, flash_state=flash_state
            )

    return all_icons


if __name__ == "__main__":
    from config import ICON_COLOR_INFO

    icon = draw_icon(fill_color=ICON_COLOR_INFO, flash_state=-1)
    icon.save(
        "info.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print("info.ico 已保存到项目根目录")

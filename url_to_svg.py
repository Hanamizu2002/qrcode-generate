#!/usr/bin/env python3
"""URL → 带中央圆角 Logo 框的 SVG 二维码（Python 3.10+）。

安装：python -m pip install qrcode pillow cairosvg zxing-cpp
使用：python url_to_svg.py "https://www.voxisle.art" -o qr.svg
参数：--size 1668 --center-ratio 0.333 --border 4 --force

完全本地编码，不访问 URL，也不上传链接。输出是矢量路径。
默认高纠错 H，至少使用版本 4；尝试不同掩模并对最终 SVG 栅格化解码，
必要时自动缩小中央装饰。解码成功不等于所有手机或印刷条件均可识别。
依赖参考：https://github.com/lincolnloop/python-qrcode
macOS 若 Cairo 加载失败可安装系统 Cairo：brew install cairo。
Linux Debian/Ubuntu 可安装 libcairo2；Windows 需提供可用的 Cairo DLL。
"""

import argparse
import io
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit


def validate_url(url: str) -> str:
    """验证但不改写 URL，保留路径、查询参数及 Unicode 字符。"""
    if not url or any(c.isspace() or ord(c) < 32 for c in url):
        raise ValueError("URL 不能为空，也不能包含空白或控制字符，请先进行 URL 编码。")
    parts = urlsplit(url)
    if parts.scheme.lower() not in ("http", "https") or not parts.hostname:
        raise ValueError("请输入完整的 http:// 或 https:// 链接。")
    _ = parts.port  # 同时检查端口是否合法
    return url


def validate_color(color: str) -> str:
    """只允许可安全写入 SVG 属性的六位十六进制颜色。"""
    if not isinstance(color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        raise ValueError("颜色必须是 #RRGGBB 格式，例如 #1D1F2A。")
    return color.upper()


def load_logo(path: Path):
    """解析 Logo SVG，返回 viewBox 和可直接嵌入的矢量节点。"""
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"Logo SVG 无法解析：{exc}") from exc
    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise ValueError("Logo 文件根节点必须是 <svg>。")
    view_box = root.get("viewBox")
    try:
        _, _, width, height = map(float, view_box.split())
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("Logo SVG 需要有效的 viewBox。") from exc
    if width <= 0 or height <= 0:
        raise ValueError("Logo SVG 的 viewBox 尺寸必须大于 0。")
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    return view_box, "".join(ET.tostring(child, encoding="unicode") for child in root)


def render_svg(matrix, *, size=1024, border=4, ratio=1 / 3, logo=None, color="#000000"):
    """矩阵以一个模块为 SVG 单位；描边宽度与二维码模块一致。"""
    n = len(matrix)
    total = n + 2 * border
    width = n * ratio if ratio else 0
    edge = (total - width) / 2
    clear_start = edge - 1.05
    clear_end = total - clear_start

    def visible(row, x, y):
        center_x, center_y = x + border + 0.5, y + border + 0.5
        cleared = ratio and clear_start <= center_x <= clear_end and clear_start <= center_y <= clear_end
        return row[x] and not cleared

    commands = []
    for y, row in enumerate(matrix):
        x = 0
        while x < n:
            if not visible(row, x, y):
                x += 1
                continue
            start = x
            while x < n and visible(row, x, y):
                x += 1
            commands.append(f"M{start + border} {y + border}h{x-start}v1h{start-x}z")

    mark = ""
    if ratio:
        stroke = min(1.0, width / 6)
        radius = width * (72 / 524)
        logo_size = width * 0.55
        logo_edge = (total - logo_size) / 2
        logo_svg = (
            f'<svg x="{logo_edge:.6f}" y="{logo_edge:.6f}" '
            f'width="{logo_size:.6f}" height="{logo_size:.6f}" '
            f'viewBox="{logo[0]}" preserveAspectRatio="xMidYMid meet">'
            f'{logo[1]}</svg>' if logo else ""
        )
        mark = (
            f'<g id="center-frame" fill="{color}">'
            f'<rect x="{edge+stroke/2:.6f}" y="{edge+stroke/2:.6f}" '
            f'width="{width-stroke:.6f}" height="{width-stroke:.6f}" '
            f'rx="{max(0, radius-stroke/2):.6f}" '
            f'fill="none" stroke="{color}" stroke-width="{stroke:.6f}"/>'
            f'{logo_svg}'
            '</g>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {total} {total}">\n'
        '<title>URL QR code with outlined center</title>\n'
        f'<path id="qr-modules" fill="{color}" d="{"".join(commands)}"/>\n'
        f'{mark}\n</svg>\n'
    )


def generate_svg(url: str, *, size=1024, border=4, center_ratio=1 / 3, color="#000000"):
    """返回 (SVG 字符串, 实际中央比例, QR 版本)。不执行文件写入。

    尝试 8 种掩模；全部失败时逐步缩小中央框，最小比例 0.12。
    解码比对原始 UTF-8 字节，无法通过检查则报错而不输出文件。
    """
    import qrcode
    import cairosvg
    import zxingcpp
    from PIL import Image

    validate_url(url)
    color = validate_color(color)
    if not isinstance(size, int) or size < 256 or size > 16384:
        raise ValueError("size 必须是 256～16384 之间的整数。")
    if not isinstance(border, int) or not 4 <= border <= 32:
        raise ValueError("border 必须是 4～32 个模块，保留标准静区。")
    if not math.isfinite(center_ratio) or not (center_ratio == 0 or 0.12 <= center_ratio <= 0.36):
        raise ValueError("center_ratio 应为 0（无中央框），或 0.12～0.36。")

    data = url.encode("utf-8")
    logo = load_logo(Path(__file__).with_name("logo.svg")) if center_ratio else None
    matrices = []
    for mask in range(8):
        qr = qrcode.QRCode(version=4, error_correction=qrcode.constants.ERROR_CORRECT_H,
                           border=0, mask_pattern=mask)
        qr.add_data(data)
        try:
            qr.make(fit=True)
        except qrcode.exceptions.DataOverflowError as exc:
            raise ValueError("链接超出高纠错二维码容量，请缩短链接。") from exc
        matrices.append((qr.get_matrix(), qr.version))

    ratios = [center_ratio]
    if center_ratio:
        while ratios[-1] > 0.12:
            ratios.append(max(0.12, round(ratios[-1] - 0.02, 6)))
    for ratio in ratios:
        for matrix, version in matrices:
            svg = render_svg(matrix, size=size, border=border, ratio=ratio, logo=logo, color=color)
            # 验证时模拟将透明 SVG 放在白色背景上的实际使用效果。
            # 验证大小限制为 1024，避免用户指定超大尺寸导致内存开销。
            raster_size = min(size, 1024)
            png = cairosvg.svg2png(bytestring=svg.encode("utf-8"),
                                  output_width=raster_size, output_height=raster_size,
                                  background_color="white")
            with Image.open(io.BytesIO(png)) as image:
                results = zxingcpp.read_barcodes(image.convert("RGB"))
                if any(result.bytes == data for result in results):
                    return svg, ratio, version
    raise ValueError("未通过解码验证。请缩短链接，或使用 --center-ratio 0 生成标准二维码。")


def svg_to_png(svg: str, size: int) -> bytes:
    """将 SVG 透明渲染为同尺寸 PNG。"""
    import cairosvg

    return cairosvg.svg2png(bytestring=svg.encode("utf-8"), output_width=size, output_height=size)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("url", help="完整 URL；建议用引号包裹")
    parser.add_argument("-o", "--output", type=Path, default=Path("qrcode.svg"))
    parser.add_argument("--size", type=int, default=1024, help="输出尺寸，默认 1024")
    parser.add_argument("--border", type=int, default=4, help="四周静区模块数，默认 4")
    parser.add_argument("--center-ratio", type=float, default=1 / 3,
                        help="中央框占二维码主体宽度的比例，默认 0.333；0 关闭装饰")
    parser.add_argument("--color", default="#000000", help="二维码颜色，#RRGGBB 格式，默认 #000000")
    parser.add_argument("--force", action="store_true", help="允许覆盖已有输出文件")
    args = parser.parse_args(argv)
    try:
        suffix = args.output.suffix.lower()
        if suffix not in (".svg", ".png"):
            raise ValueError("输出文件扩展名必须为 .svg 或 .png。")
        if args.output.exists() and not args.force:
            raise ValueError("输出文件已存在；请换一个名称或使用 --force。")
        svg, ratio, version = generate_svg(args.url, size=args.size, border=args.border,
                                           center_ratio=args.center_ratio, color=args.color)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if suffix == ".svg":
            with args.output.open("w" if args.force else "x", encoding="utf-8") as file:
                file.write(svg)
        else:
            with args.output.open("wb" if args.force else "xb") as file:
                file.write(svg_to_png(svg, args.size))
        print(f"已生成：{args.output.resolve()}\n版本：{version}，纠错：H，中央比例：{ratio:.3f}，解码验证：通过")
        if ratio < args.center_ratio:
            print("为通过解码验证，已自动缩小中央框。")
        print("发布或印刷前请用实际手机扫码复核；请勿再扩大中央遮挡。")
        return 0
    except (ImportError, OSError) as exc:
        print(f"依赖或文件错误：{exc}\n安装依赖：python -m pip install qrcode pillow cairosvg zxing-cpp", file=sys.stderr)
        return 1
    except (ValueError, OverflowError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

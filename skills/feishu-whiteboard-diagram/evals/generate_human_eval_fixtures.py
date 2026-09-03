#!/usr/bin/env python3
"""Generate human-eval whiteboard fixtures as UTF-8 SVG / Mermaid / HTML."""

from __future__ import annotations

import html
from pathlib import Path

OUT = Path(__file__).resolve().parent / "fixtures" / "human-eval"

INK = "#1F2329"
MUTED = "#64748B"
LINE = "#94A3B8"
WHITE = "#FFFFFF"
CANVAS = "#F8FAFC"
CANVAS_EDGE = "#CBD5E1"
BLUE_FILL, BLUE_EDGE = "#EFF6FF", "#2563EB"
BLUE_SOFT = "#DBEAFE"
PURPLE_FILL, PURPLE_EDGE = "#F5F3FF", "#7C3AED"
ORANGE_FILL, ORANGE_EDGE = "#FFF7ED", "#EA580C"
GREEN_FILL, GREEN_EDGE = "#ECFDF5", "#16A34A"
GREEN_SOFT = "#DCFCE7"
RED_FILL, RED_EDGE = "#FEE2E2", "#DC2626"
YELLOW_FILL, YELLOW_EDGE = "#FEF3C7", "#D97706"
PINK_FILL, PINK_EDGE = "#FDF2F8", "#DB2777"
RISO_CREAM, RISO_CREAM2 = "#EFE9D9", "#E4DCC4"
RISO_INK, RISO_INK2 = "#0F0F0F", "#2A2A2A"
RISO_GREEN, RISO_ORANGE = "#1F8A4C", "#E85A1F"
RISO_PINK, RISO_YELLOW = "#F06CA8", "#F5C518"
RIPTIDE_COBALT, RIPTIDE_CREAM, RIPTIDE_INK = "#375DFE", "#FDF0E0", "#1A2240"
CORAL, CORAL_CREAM, CORAL_INK = "#E85D5D", "#F5F0E8", "#1A1A1A"
GROVE_PARCH, GROVE_FOREST, GROVE_TERRA = "#E8E4D6", "#192B1B", "#C8524A"
AVO_BLUE, AVO_LIME, AVO_INK = "#0055A4", "#DCF4A2", "#0B1F3A"


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def markers() -> str:
    defs = []
    for name, color in {
        "arrow-gray": LINE,
        "arrow-blue": BLUE_EDGE,
        "arrow-green": GREEN_EDGE,
        "arrow-purple": PURPLE_EDGE,
        "arrow-orange": ORANGE_EDGE,
        "arrow-red": RED_EDGE,
        "arrow-ink": RISO_INK,
        "arrow-riso-green": RISO_GREEN,
        "arrow-riso-orange": RISO_ORANGE,
        "arrow-cobalt": RIPTIDE_COBALT,
        "arrow-coral": CORAL,
        "arrow-grove": GROVE_FOREST,
        "arrow-avo": AVO_BLUE,
    }.items():
        defs.append(
            f'<marker id="{name}" markerWidth="10" markerHeight="8" refX="9" refY="4" '
            f'orient="auto" markerUnits="userSpaceOnUse">'
            f'<path d="M0 0 L10 4 L0 8 z" fill="{color}"/></marker>'
        )
    return "<defs>" + "".join(defs) + "</defs>"


def svg(width: int, height: int, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">\n'
        f"{markers()}\n{body}\n</svg>\n"
    )


def t(
    x: float,
    y: float,
    text: str,
    *,
    size: int = 14,
    weight: int = 400,
    fill: str = INK,
    anchor: str = "start",
) -> str:
    return (
        f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}">{esc(text)}</text>'
    )


def rect(
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str,
    stroke: str,
    *,
    sw: float = 2,
    rx: float = 12,
) -> str:
    return (
        f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{rx:.0f}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
    )


def circle(cx: float, cy: float, r: float, fill: str, stroke: str, sw: float = 0) -> str:
    stroke_attr = f' stroke="{stroke}" stroke-width="{sw}"' if sw else ""
    return f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="{fill}"{stroke_attr}/>'


def poly(
    points: str,
    stroke: str,
    *,
    marker: str = "arrow-gray",
    dash: bool = False,
    sw: float = 2,
) -> str:
    dash_attr = ' stroke-dasharray="8 6"' if dash else ""
    return (
        f'<polyline points="{points}" fill="none" stroke="{stroke}" stroke-width="{sw}" '
        f'marker-end="url(#{marker})"{dash_attr}/>'
    )


def line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    stroke: str,
    *,
    marker: str = "arrow-gray",
    dash: bool = False,
    sw: float = 2,
) -> str:
    dash_attr = ' stroke-dasharray="8 6"' if dash else ""
    return (
        f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" fill="none" '
        f'stroke="{stroke}" stroke-width="{sw}" marker-end="url(#{marker})"{dash_attr}/>'
    )


def diamond(cx: float, cy: float, w: float, h: float, fill: str, stroke: str) -> str:
    pts = f"{cx:.0f},{cy - h / 2:.0f} {cx + w / 2:.0f},{cy:.0f} {cx:.0f},{cy + h / 2:.0f} {cx - w / 2:.0f},{cy:.0f}"
    return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'


def card(x: float, y: float, w: float, h: float, title: str, detail: str, edge: str) -> str:
    return "".join(
        [
            rect(x, y, w, h, WHITE, edge, sw=1.5, rx=12),
            t(x + 16, y + 30, title, size=16, weight=700),
            t(x + 16, y + 54, detail, size=14, fill=MUTED),
        ]
    )


def layered_strip() -> str:
    parts: list[str] = [
        t(48, 52, "支付网关分层：每层屏蔽什么", size=28, weight=700),
        t(48, 84, "自上而下看职责，自下而上看出边界。层间只暴露真实 API。", size=16, fill=MUTED),
        t(1180, 52, "↑ 上行", size=16, weight=700, fill=BLUE_EDGE),
        t(1288, 52, "↓ 下行", size=16, weight=700, fill=GREEN_EDGE),
    ]
    layers = [
        (
            "L4",
            "接入层",
            PINK_FILL,
            PINK_EDGE,
            [
                ("组件 / 协议", "HTTP · gRPC Gateway · TLS"),
                ("功能职责", "鉴权、限流、协议终结"),
                ("边界", "不理解业务会话，只转发流"),
            ],
        ),
        (
            "L3",
            "协议层",
            BLUE_FILL,
            BLUE_EDGE,
            [
                ("组件 / 协议", "Frame codec · Mux"),
                ("功能职责", "帧编解码、多路复用"),
                ("边界", "不持有用户身份，只认 streamId"),
            ],
        ),
        (
            "L2",
            "会话层",
            PURPLE_FILL,
            PURPLE_EDGE,
            [
                ("组件 / 协议", "Session · Track registry"),
                ("功能职责", "会话生命周期、轨道绑定"),
                ("边界", "不调用具体后端 SDK"),
            ],
        ),
        (
            "L1",
            "后端适配",
            GREEN_FILL,
            GREEN_EDGE,
            [
                ("组件 / 协议", "Vendor adapter · Retry"),
                ("功能职责", "后端差异、超时与重试"),
                ("边界", "对上只暴露稳定媒体事件"),
            ],
        ),
    ]
    apis = [
        ("OpenStream", "OnTrackData"),
        ("BindSession", "OnTrackEvent"),
        ("Dispatch", "MediaEvent"),
    ]
    y = 100
    layer_h = 168
    gap = 56
    x = 48
    w = 1424
    for i, (badge, name, fill, edge, cards) in enumerate(layers):
        parts.append(rect(x, y, w, layer_h, fill, edge, sw=2, rx=16))
        parts.append(rect(x - 8, y - 12, 52, 28, edge, edge, sw=0, rx=8))
        parts.append(t(x + 18, y + 8, badge, size=13, weight=700, fill=WHITE, anchor="middle"))
        parts.append(t(x + 56, y + 28, name, size=16, weight=700, fill=edge))
        card_y = y + 48
        card_h = 100
        card_w = 448
        gap_x = 16
        inner = x + 20
        for j, (title, detail) in enumerate(cards):
            cx = inner + j * (card_w + gap_x)
            parts.append(card(cx, card_y, card_w, card_h, title, detail, edge))
        if i < len(apis):
            gy = y + layer_h + gap / 2
            up, down = apis[i]
            parts.append(line(220, gy + 16, 220, gy - 16, BLUE_EDGE, marker="arrow-blue"))
            parts.append(t(236, gy + 5, f"上行 {up}", size=14, fill=BLUE_EDGE))
            parts.append(line(1280, gy - 16, 1280, gy + 16, GREEN_EDGE, marker="arrow-green"))
            parts.append(t(1108, gy + 5, f"下行 {down}", size=14, fill=GREEN_EDGE, anchor="end"))
            y += layer_h + gap
        else:
            y += layer_h
    fy = y + 24
    parts.append(rect(48, fy, 1424, 52, GREEN_SOFT, GREEN_EDGE, sw=2, rx=12))
    parts.append(
        t(
            760,
            fy + 32,
            "上层只暴露稳定 API；下层屏蔽协议与后端差异。",
            size=15,
            weight=700,
            fill=GREEN_EDGE,
            anchor="middle",
        )
    )
    return svg(1520, fy + 92, "".join(parts))


def hard_shadow(x: float, y: float, w: float, h: float, color: str = RISO_INK, d: float = 10) -> str:
    return rect(x + d, y + d, w, h, color, color, sw=0, rx=0)


def cream_bg(parts: list[str], w: float, h: float, fill: str = RISO_CREAM) -> None:
    parts.append(rect(0, 0, w, h, fill, fill, sw=0, rx=0))


def ink_footer(parts: list[str], x: float, y: float, w: float, text: str, fill: str = RISO_INK, fg: str = RISO_CREAM) -> None:
    parts.append(rect(x, y, w, 56, fill, fill, sw=0, rx=0))
    parts.append(t(x + w / 2, y + 36, text, size=18, weight=700, fill=fg, anchor="middle"))


def quiet_box(
    parts: list[str],
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    detail: str = "",
    *,
    fill: str = WHITE,
    ink: str = RISO_INK,
    muted: str = RISO_INK2,
) -> None:
    parts.append(rect(x, y, w, h, fill, ink, sw=4, rx=0))
    parts.append(t(x + 20, y + 40, title, size=18, weight=700, fill=ink))
    if detail:
        parts.append(t(x + 20, y + 68, detail, size=16, fill=muted))


def solid_box(
    parts: list[str],
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str,
    title: str,
    detail: str = "",
    *,
    ink: str = RISO_INK,
    fg: str = RISO_CREAM,
    title_size: int = 22,
    shadow: str | None = None,
) -> None:
    if shadow:
        parts.append(hard_shadow(x, y, w, h, shadow))
    parts.append(rect(x, y, w, h, fill, ink, sw=4, rx=0))
    cy = y + h / 2
    if detail:
        parts.append(t(x + w / 2, cy - 6, title, size=title_size, weight=700, fill=fg, anchor="middle"))
        parts.append(t(x + w / 2, cy + 24, detail, size=16, fill=fg, anchor="middle"))
    else:
        parts.append(t(x + w / 2, cy + 8, title, size=title_size, weight=700, fill=fg, anchor="middle"))


def task_loop() -> str:
    """Pipeline-fork: quiet prep, then a large tool-loop band as the visual centre."""
    w, h = 1600, 900
    parts: list[str] = []
    cream_bg(parts, w, h)
    parts.append(t(80, 80, "Hermes 普通任务循环", size=40, weight=700, fill=RISO_INK))
    parts.append(
        t(
            80,
            122,
            "谁决策、谁执行。能直接回答就结束；真正要放大的是工具分叉，不是一排均等盒子。",
            size=18,
            fill=RISO_INK2,
        )
    )
    parts.append(t(80, 172, "准备", size=16, weight=700, fill=RISO_INK2))
    quiet_box(parts, 80, 188, 260, 100, "用户任务", "提出问题")
    quiet_box(parts, 380, 188, 280, 100, "加载上下文", "记忆 / 技能 / 会话")
    solid_box(parts, 720, 172, 400, 132, RISO_ORANGE, "判断", "谁决策", title_size=28, shadow=RISO_ORANGE)
    parts.append(line(340, 238, 380, 238, RISO_INK, marker="arrow-ink", sw=3))
    parts.append(line(660, 238, 720, 238, RISO_INK, marker="arrow-ink", sw=3))

    parts.append(t(80, 340, "直接回答 · 短支", size=16, weight=700, fill=RISO_INK2))
    solid_box(parts, 80, 360, 520, 220, RISO_GREEN, "最终答案", "到这里就结束", title_size=26)
    parts.append(poly("720,304 340,304 340,360", RISO_GREEN, marker="arrow-riso-green", sw=3))
    parts.append(t(500, 292, "直接回答", size=16, weight=700, fill=RISO_GREEN))

    parts.append(hard_shadow(650, 350, 870, 360, RISO_INK))
    parts.append(rect(640, 340, 870, 360, RISO_GREEN, RISO_INK, sw=4, rx=0))
    parts.append(t(672, 384, "工具回路", size=24, weight=700, fill=RISO_CREAM))
    parts.append(t(672, 416, "需要工具才走 · 这一段才是焦点", size=16, fill=RISO_CREAM))
    parts.append(rect(672, 444, 360, 216, WHITE, RISO_INK, sw=4, rx=0))
    parts.append(t(852, 524, "执行工具", size=24, weight=700, fill=RISO_INK, anchor="middle"))
    parts.append(t(852, 560, "谁执行", size=16, fill=RISO_INK2, anchor="middle"))
    parts.append(rect(1072, 444, 400, 216, WHITE, RISO_INK, sw=4, rx=0))
    parts.append(rect(1072, 444, 400, 12, RISO_ORANGE, RISO_ORANGE, sw=0, rx=0))
    parts.append(t(1272, 536, "工具结果", size=24, weight=700, fill=RISO_INK, anchor="middle"))
    parts.append(t(1272, 572, "回填后再判断", size=16, fill=RISO_INK2, anchor="middle"))
    parts.append(line(1032, 552, 1072, 552, RISO_INK, marker="arrow-ink", sw=3))
    parts.append(poly("852,304 852,444", RISO_ORANGE, marker="arrow-riso-orange", sw=3))
    parts.append(t(868, 380, "需要工具", size=16, weight=700, fill=RISO_CREAM))
    parts.append(
        poly(
            "1272,444 1272,428 1080,428 1080,304",
            RISO_ORANGE,
            marker="arrow-riso-orange",
            dash=True,
            sw=3,
        )
    )
    parts.append(t(1188, 418, "结果回填，再次判断", size=16, weight=700, fill=RISO_ORANGE, anchor="middle"))
    ink_footer(parts, 80, 788, 1440, "直接回答就结束。工具结果用短虚线回填到判断，不要绕画布一圈。")
    return svg(w, h, "".join(parts))


def learning_loop() -> str:
    """Gate row + three dense comparison columns. No wrap-around dashed loop."""
    w, h = 1600, 980
    parts: list[str] = []
    cream_bg(parts, w, h)
    parts.append(t(80, 80, "学习闭环：值不值得写回去", size=40, weight=700, fill=RISO_INK))
    parts.append(
        t(
            80,
            122,
            "上门禁，下三列对比。焦点是三种落盘，不是从门禁拉出三根斜线。",
            size=18,
            fill=RISO_INK2,
        )
    )
    parts.append(rect(80, 148, 220, 28, RISO_YELLOW, RISO_INK, sw=3, rx=0))
    parts.append(t(190, 168, "下一轮从这里开始", size=14, weight=700, fill=RISO_INK, anchor="middle"))
    quiet_box(parts, 80, 188, 220, 96, "任务完成", "一次执行结束")
    quiet_box(parts, 340, 188, 200, 96, "复盘", "值不值得留下")
    solid_box(parts, 580, 180, 280, 112, RISO_ORANGE, "值得复用?", "是 ↓   否 →", title_size=22)
    quiet_box(parts, 900, 196, 220, 88, "结束", "不写回去")
    parts.append(line(300, 236, 340, 236, RISO_INK, marker="arrow-ink", sw=3))
    parts.append(line(540, 236, 580, 236, RISO_INK, marker="arrow-ink", sw=3))
    parts.append(line(860, 236, 900, 236, RISO_INK, marker="arrow-ink", sw=3))
    parts.append(t(872, 220, "否", size=16, weight=700, fill=RISO_INK))
    parts.append(poly("720,292 720,348", RISO_ORANGE, marker="arrow-riso-orange", sw=3))
    parts.append(t(736, 328, "是 · 过门禁", size=16, weight=700, fill=RISO_ORANGE))

    cols = [
        (
            80,
            RISO_GREEN,
            "USER.md",
            [
                ("写什么", "偏好、习惯、禁忌"),
                ("何时读", "每轮任务开始注入"),
                ("门禁", "是否稳定偏好"),
                ("风险", "写进人格会漂移"),
                ("怎么用", "注入，不检索"),
            ],
        ),
        (
            573,
            RISO_INK,
            "MEMORY",
            [
                ("写什么", "可检索事实、约定"),
                ("何时读", "需要时召回，不是全文"),
                ("门禁", "扫描 / 去重"),
                ("风险", "脏事实被反复引用"),
                ("怎么用", "召回，不养成习惯"),
            ],
        ),
        (
            1066,
            RISO_ORANGE,
            "SKILL.md",
            [
                ("写什么", "可复用步骤、检查清单"),
                ("何时读", "匹配任务时按步骤调用"),
                ("门禁", "质量可否复现"),
                ("风险", "步骤过时仍被执行"),
                ("怎么用", "执行，不写进人格"),
            ],
        ),
    ]
    col_w, cap_h, row_h = 454, 56, 72
    for x, cap, title, rows in cols:
        body_h = cap_h + row_h * len(rows)
        parts.append(hard_shadow(x, 358, col_w, body_h, RISO_INK))
        parts.append(rect(x, 348, col_w, cap_h, cap, RISO_INK, sw=4, rx=0))
        parts.append(t(x + col_w / 2, 386, title, size=22, weight=700, fill=RISO_CREAM, anchor="middle"))
        y = 348 + cap_h
        for i, (label, value) in enumerate(rows):
            bg = WHITE if i < len(rows) - 1 else RISO_CREAM2
            parts.append(rect(x, y, col_w, row_h, bg, RISO_INK, sw=4, rx=0))
            parts.append(t(x + 20, y + 28, label, size=14, weight=700, fill=RISO_INK2))
            parts.append(t(x + 20, y + 54, value, size=16, weight=700, fill=RISO_INK))
            y += row_h

    quiet_box(parts, 80, 800, 454, 80, "后续任务注入", "USER.md + MEMORY")
    solid_box(parts, 573, 800, 454, 80, RISO_GREEN, "复用执行", "SKILL.md 按步骤调用", title_size=20)
    parts.append(t(1140, 848, "一类知识只进一列", size=18, weight=700, fill=RISO_INK))
    parts.append(line(534, 840, 573, 840, RISO_INK, marker="arrow-ink", sw=3))
    ink_footer(parts, 80, 900, 1440, "「否」必须有结束态。门禁写的是扫描 / 去重 / 质量，不是「保存」。")
    return svg(w, h, "".join(parts))


def multicolumn_runtime() -> str:
    w, h = 1600, 720
    parts: list[str] = []
    cream_bg(parts, w, h)
    parts.append(t(80, 80, "运行架构：请求向右，事件向左", size=40, weight=700, fill=RISO_INK))
    parts.append(
        t(80, 122, "列是职责边界。运行时必须最大：模型只在这里跑。", size=18, fill=RISO_INK2)
    )
    parts.append(t(1180, 80, "请求 →", size=16, weight=700, fill=RISO_GREEN, anchor="end"))
    parts.append(t(1520, 80, "← 事件", size=16, weight=700, fill=RISO_ORANGE, anchor="end"))
    cols = [
        (80, 280, False, "01 宿主", "发起与投影", "发起请求", "thread/start", "投影到 UI", "item/completed"),
        (380, 280, False, "02 传输", "连接与鉴权", "Gate", "auth · stream", "Outbound", "event frame"),
        (680, 280, False, "03 协调", "排队与调度", "Processor", "turn queue", "Outbound", "delta / event"),
        (1000, 520, True, "04 运行时", "思考与工具", "Agent Loop", "model · tools", "Events", "item / file"),
    ]
    req_y, ev_y = 220, 400
    for x, col_w, hero, name, duty, req, req_d, ev, ev_d in cols:
        if hero:
            parts.append(hard_shadow(x, 168, col_w, 392, RISO_INK))
            parts.append(rect(x, 158, col_w, 392, RISO_GREEN, RISO_INK, sw=4, rx=0))
            fg, sub, box_fill, box_ink = RISO_CREAM, RISO_CREAM, WHITE, RISO_INK
        else:
            parts.append(rect(x, 158, col_w, 392, WHITE, RISO_INK, sw=4, rx=0))
            fg, sub, box_fill, box_ink = RISO_INK, RISO_INK2, RISO_CREAM2, RISO_INK
        parts.append(t(x + 20, 196, name, size=20, weight=700, fill=fg))
        parts.append(t(x + 20, 224, duty, size=16, fill=sub))
        inner_w = col_w - 40
        parts.append(rect(x + 20, req_y, inner_w, 88, box_fill, box_ink, sw=3, rx=0))
        parts.append(t(x + col_w / 2, req_y + 36, req, size=18, weight=700, fill=RISO_INK, anchor="middle"))
        parts.append(t(x + col_w / 2, req_y + 64, req_d, size=14, fill=RISO_INK2, anchor="middle"))
        parts.append(rect(x + 20, ev_y, inner_w, 88, WHITE, box_ink, sw=3, rx=0))
        parts.append(t(x + col_w / 2, ev_y + 36, ev, size=18, weight=700, fill=RISO_INK, anchor="middle"))
        parts.append(t(x + col_w / 2, ev_y + 64, ev_d, size=14, fill=RISO_INK2, anchor="middle"))
        if hero:
            parts.append(line(x + col_w / 2, req_y + 88, x + col_w / 2, ev_y, RISO_INK, marker="arrow-ink", sw=3))
            parts.append(t(x + col_w / 2 + 16, 392, "tools", size=14, weight=700, fill=RISO_CREAM))
    pairs = [(80, 280, 380), (380, 280, 680), (680, 280, 1000)]
    for x, col_w, nxt in pairs:
        parts.append(line(x + col_w, req_y + 44, nxt, req_y + 44, RISO_GREEN, marker="arrow-riso-green", sw=3))
        parts.append(line(nxt, ev_y + 44, x + col_w, ev_y + 44, RISO_ORANGE, marker="arrow-riso-orange", sw=3))
    notes = [(220, "宿主不跑模型"), (520, "传输不理解 turn"), (820, "协调不碰工具"), (1260, "运行时不画 UI")]
    parts.append(rect(80, 572, 1440, 56, RISO_INK, RISO_INK, sw=0, rx=0))
    for x, note in notes:
        parts.append(t(x, 608, note, size=16, weight=700, fill=RISO_CREAM, anchor="middle"))
    return svg(w, h, "".join(parts))


def recovery_layers() -> str:
    parts: list[str] = [
        t(48, 52, "三层状态，三种恢复粒度", size=28, weight=700),
        t(48, 84, "中断之后到底恢复哪一层：对话、事务，还是某一个动作。", size=16, fill=MUTED),
        t(1472, 52, "一张图回答：从哪继续", size=16, weight=700, fill=BLUE_EDGE, anchor="end"),
    ]
    layers = [
        (
            "01",
            "THREAD  对话边界",
            BLUE_FILL,
            BLUE_EDGE,
            "恢复哪段上下文？",
            [("HISTORY", "thread/start"), ("FORK", "branch"), ("SUBSCRIBE", "live")],
            "一个 Thread 含多个 Turn",
        ),
        (
            "02",
            "TURN  事务边界",
            PURPLE_FILL,
            PURPLE_EDGE,
            "这次事务结束了吗？",
            [
                ("inProgress", "进行"),
                ("completed", "成功"),
                ("interrupted", "中断"),
                ("failed", "失败"),
            ],
            "一次 Turn 产生多个 Item",
        ),
        (
            "03",
            "ITEM  工作单元",
            GREEN_FILL,
            GREEN_EDGE,
            "哪个动作到了哪？",
            [
                ("USER", "输入"),
                ("PLAN", "计划"),
                ("COMMAND", "命令"),
                ("FILE", "文件"),
                ("AGENT", "回复"),
            ],
            "",
        ),
    ]
    status_colors = {
        "inProgress": (BLUE_FILL, BLUE_EDGE),
        "completed": (GREEN_FILL, GREEN_EDGE),
        "interrupted": (YELLOW_FILL, YELLOW_EDGE),
        "failed": (RED_FILL, RED_EDGE),
    }
    y = 108
    for i, (num, title, fill, edge, question, pills, between) in enumerate(layers):
        h = 168
        parts.append(rect(40, y, 1440, h, fill, edge, sw=2, rx=16))
        parts.append(rect(28, y - 14, 56, 32, edge, edge, sw=0, rx=8))
        parts.append(t(56, y + 8, num, size=14, weight=700, fill=WHITE, anchor="middle"))
        parts.append(t(100, y + 28, title, size=16, weight=700, fill=edge))
        parts.append(rect(1120, y + 20, 336, 44, WHITE, edge, sw=1.5, rx=12))
        parts.append(t(1288, y + 48, question, size=14, weight=700, fill=edge, anchor="middle"))
        px = 64
        py = y + 72
        for label, detail in pills:
            pw = 200 if i != 2 else 160
            cfill, cedge = status_colors.get(label, (WHITE, edge))
            parts.append(rect(px, py, pw, 64, cfill, cedge, sw=1.5, rx=12))
            parts.append(t(px + pw / 2, py + 28, label, size=14, weight=700, fill=cedge, anchor="middle"))
            parts.append(t(px + pw / 2, py + 50, detail, size=14, fill=MUTED, anchor="middle"))
            px += pw + 16
        y += h
        if between:
            parts.append(line(760, y + 4, 760, y + 36, LINE, marker="arrow-gray"))
            parts.append(t(776, y + 24, between, size=14, fill=MUTED))
            y += 44
    fy = y + 16
    parts.append(rect(40, fy, 1440, 64, GREEN_SOFT, GREEN_EDGE, sw=2, rx=12))
    parts.append(
        t(
            760,
            fy + 28,
            "恢复坐标：threadId + turnId + itemId",
            size=16,
            weight=700,
            fill=GREEN_EDGE,
            anchor="middle",
        )
    )
    parts.append(
        t(760, fy + 50, "Delta 是预览 · Completed 是事实", size=14, fill=MUTED, anchor="middle")
    )
    return svg(1520, fy + 92, "".join(parts))


def comparison_matrix() -> str:
    w, h = 1600, 820
    parts: list[str] = [
        rect(0, 0, w, h, RIPTIDE_CREAM, RIPTIDE_CREAM, sw=0, rx=0),
        t(64, 72, "三种落盘，哪一列接什么", size=40, weight=700, fill=RIPTIDE_INK),
        t(64, 112, "逐项对比。钴色块是该行更该写入的去处，不是三种都写。", size=18, fill=RIPTIDE_INK),
    ]
    headers = [("写什么", 64), ("USER.md", 400), ("MEMORY", 800), ("SKILL.md", 1200)]
    col_w = 336
    xs = [64, 400, 800, 1200]
    parts.append(rect(xs[0], 160, col_w, 64, RIPTIDE_INK, RIPTIDE_INK, sw=0, rx=0))
    parts.append(t(xs[0] + 24, 200, "维度", size=20, weight=700, fill=RIPTIDE_CREAM))
    for x, name in zip(xs[1:], ["USER.md", "MEMORY", "SKILL.md"]):
        parts.append(rect(x, 160, col_w, 64, RIPTIDE_COBALT, RIPTIDE_INK, sw=4, rx=0))
        parts.append(t(x + col_w / 2, 202, name, size=20, weight=700, fill="#FFFFFF", anchor="middle"))
    rows = [
        ("内容", "偏好与习惯", "可检索事实", "可复用步骤", 2),
        ("读取时机", "每轮开始注入", "需要时召回", "匹配任务时加载", 0),
        ("风险", "写进人格会漂移", "脏事实被反复引用", "步骤过时仍被执行", 1),
        ("门禁", "先问是否稳定偏好", "扫描去重", "质量是否可复现", 1),
    ]
    y = 240
    labels = ["内容", "读取时机", "风险", "门禁"]
    cells = [
        ["偏好与习惯", "可检索事实", "可复用步骤"],
        ["每轮开始注入", "需要时召回", "匹配任务时加载"],
        ["写进人格会漂移", "脏事实被反复引用", "步骤过时仍被执行"],
        ["是否稳定偏好", "扫描 / 去重", "质量可否复现"],
    ]
    winners = [0, 2, 1, 1]
    for i, (label, row, win) in enumerate(zip(labels, cells, winners)):
        parts.append(rect(xs[0], y, col_w, 100, RIPTIDE_INK, RIPTIDE_INK, sw=0, rx=0))
        parts.append(t(xs[0] + 24, y + 58, label, size=18, weight=700, fill=RIPTIDE_CREAM))
        for j, text in enumerate(row):
            x = xs[j + 1]
            if j == win:
                parts.append(rect(x, y, col_w, 100, RIPTIDE_COBALT, RIPTIDE_INK, sw=4, rx=0))
                parts.append(t(x + 20, y + 58, text, size=16, weight=700, fill="#FFFFFF"))
            else:
                parts.append(rect(x, y, col_w, 100, "#FFFFFF", RIPTIDE_INK, sw=4, rx=0))
                parts.append(t(x + 20, y + 58, text, size=16, fill=RIPTIDE_INK))
        y += 108
    parts.append(rect(64, 700, 1472, 64, RIPTIDE_COBALT, RIPTIDE_INK, sw=4, rx=0))
    parts.append(
        t(
            800,
            740,
            "结论：一类知识只进一列。钴色是该行的去处，不是装饰。",
            size=18,
            weight=700,
            fill="#FFFFFF",
            anchor="middle",
        )
    )
    return svg(w, h, "".join(parts))


def hub_spoke() -> str:
    w, h = 1600, 900
    parts: list[str] = [
        rect(0, 0, w, h, RISO_CREAM, RISO_CREAM, sw=0, rx=0),
        t(64, 72, "Agent 枢纽：周围一圈是什么", size=40, weight=700, fill=RISO_INK),
        t(64, 112, "核心必须最大。卫星同等大小，连线接到边缘，不穿文字。", size=18, fill=RISO_INK2),
    ]
    hx, hy, hw, hh = 620, 340, 360, 220
    spokes = [
        (80, 200, "用户任务", "提出目标", 360, 250, hx, hy + 48),
        (1180, 200, "最终答案", "直接结束", 1180, 250, hx + hw, hy + 48),
        (80, 520, "工具", "谁执行", 360, 570, hx, hy + hh - 48),
        (1180, 520, "记忆", "可检索事实", 1180, 570, hx + hw, hy + hh - 48),
        (200, 740, "技能", "可复用方法", 340, 740, hx + 80, hy + hh),
        (980, 740, "上下文", "本轮会话", 1120, 740, hx + hw - 80, hy + hh),
    ]
    for x, y, title, detail, x1, y1, x2, y2 in spokes:
        parts.append(
            f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" fill="none" '
            f'stroke="{RISO_INK}" stroke-width="3"/>'
        )
        quiet_box(parts, x, y, 280, 100, title, detail)
    parts.append(hard_shadow(hx, hy, hw, hh, RISO_ORANGE))
    parts.append(rect(hx, hy, hw, hh, RISO_GREEN, RISO_INK, sw=4, rx=0))
    parts.append(t(hx + hw / 2, hy + 90, "Agent Loop", size=28, weight=700, fill=RISO_CREAM, anchor="middle"))
    parts.append(t(hx + hw / 2, hy + 132, "判断 · 调用 · 回填", size=16, fill=RISO_CREAM, anchor="middle"))
    return svg(w, h, "".join(parts))


def turn_timeline() -> str:
    w, h = 1600, 680
    parts: list[str] = []
    cream_bg(parts, w, h, CORAL_CREAM)
    parts.append(t(80, 80, "一次 Turn：高潮在完成", size=40, weight=700, fill=CORAL_INK))
    parts.append(
        t(
            80,
            122,
            "Coral 色板。前面安静，完成态最大。中断和失败是旁路，不是主轴上的均等点。",
            size=18,
            fill=CORAL_INK,
        )
    )
    parts.append(rect(80, 320, 1440, 8, CORAL_INK, CORAL_INK, sw=0, rx=0))
    nodes = [
        (80, "start", "thread 已在", False),
        (400, "inProgress", "模型 / 工具进行中", False),
        (760, "completed", "结果成为事实", True),
        (1160, "delta", "预览不是完成", False),
    ]
    for x, title, detail, hero in nodes:
        if hero:
            parts.append(hard_shadow(x, 188, 300, 170, CORAL))
            parts.append(rect(x, 178, 300, 170, CORAL, CORAL_INK, sw=4, rx=0))
            parts.append(t(x + 150, 248, title, size=24, weight=700, fill="#FFFFFF", anchor="middle"))
            parts.append(t(x + 150, 286, detail, size=16, fill="#FFFFFF", anchor="middle"))
            parts.append(rect(x + 138, 308, 24, 24, "#F1E84E", CORAL_INK, sw=3, rx=12))
        else:
            parts.append(rect(x, 228, 240, 100, WHITE, CORAL_INK, sw=4, rx=0))
            parts.append(t(x + 20, 268, title, size=18, weight=700, fill=CORAL_INK))
            parts.append(t(x + 20, 296, detail, size=16, fill=CORAL_INK))
            parts.append(circle(x + 120, 324, 10, CORAL_INK, CORAL_INK, sw=0))
    parts.append(rect(80, 430, 240, 88, WHITE, CORAL_INK, sw=4, rx=0))
    parts.append(t(100, 470, "interrupted", size=18, weight=700, fill=CORAL_INK))
    parts.append(t(100, 498, "中断 · 可恢复", size=16, fill=CORAL_INK))
    parts.append(rect(360, 430, 240, 88, WHITE, CORAL_INK, sw=4, rx=0))
    parts.append(t(380, 470, "failed", size=18, weight=700, fill=CORAL_INK))
    parts.append(t(380, 498, "失败 · 可重试", size=16, fill=CORAL_INK))
    parts.append(t(80, 580, "Delta 是预览。Completed 才是事实。", size=18, weight=700, fill=CORAL_INK))
    return svg(w, h, "".join(parts))


def swimlane_handshake() -> str:
    """Swimlanes: Agent lane is the focal track."""
    w, h = 1600, 900
    parts: list[str] = []
    cream_bg(parts, w, h)
    parts.append(t(80, 80, "一次调用：三条泳道怎么握手", size=40, weight=700, fill=RISO_INK))
    parts.append(
        t(80, 122, "时间向右。Agent 是主角车道：绿帽 + 更重的色带。判断那一格是唯一饱和块。", size=18, fill=RISO_INK2)
    )
    label_w, body_x = 200, 300
    headers = ["提出", "判断", "执行", "回填", "作答"]
    step_w, gap = 208, 24
    for i, name in enumerate(headers):
        x = body_x + i * (step_w + gap)
        parts.append(t(x + step_w / 2, 156, name, size=16, weight=700, fill=RISO_INK2, anchor="middle"))
    lanes = [
        (176, False, "用户", "提出目标，收答案"),
        (376, True, "Agent", "决策与组织"),
        (576, False, "工具", "谁执行"),
    ]
    for y, focal, name, duty in lanes:
        if focal:
            parts.append(hard_shadow(80, y + 10, 1440, 180, RISO_INK))
            parts.append(rect(80, y, 1440, 180, RISO_CREAM2, RISO_INK, sw=4, rx=0))
            parts.append(rect(80, y, label_w, 180, RISO_GREEN, RISO_INK, sw=4, rx=0))
            fg = RISO_CREAM
        else:
            parts.append(rect(80, y, 1440, 180, WHITE, RISO_INK, sw=4, rx=0))
            parts.append(rect(80, y, label_w, 180, RISO_INK, RISO_INK, sw=4, rx=0))
            fg = RISO_CREAM
        parts.append(t(80 + label_w / 2, y + 80, name, size=22, weight=700, fill=fg, anchor="middle"))
        parts.append(t(80 + label_w / 2, y + 112, duty, size=14, fill=fg, anchor="middle"))
        for i in range(5):
            x = body_x + i * (step_w + gap)
            occupied = False
            cell_title, cell_detail = "", ""
            fill, tfill = RISO_CREAM2, RISO_INK2
            if name == "用户" and i == 0:
                occupied, cell_title, cell_detail = True, "提出任务", "目标进场"
                fill, tfill = WHITE, RISO_INK
            elif name == "用户" and i == 4:
                occupied, cell_title, cell_detail = True, "收答案", "直接结束"
                fill, tfill = WHITE, RISO_INK
            elif name == "Agent" and i == 0:
                occupied, cell_title, cell_detail = True, "加载上下文", "记忆 / 技能"
                fill, tfill = WHITE, RISO_INK
            elif name == "Agent" and i == 1:
                occupied, cell_title, cell_detail = True, "判断", "谁决策"
                fill, tfill = RISO_ORANGE, RISO_CREAM
            elif name == "Agent" and i == 2:
                occupied, cell_title, cell_detail = True, "组织调用", "要不要工具"
                fill, tfill = WHITE, RISO_INK
            elif name == "Agent" and i == 3:
                occupied, cell_title, cell_detail = True, "吸收结果", "再次判断"
                fill, tfill = WHITE, RISO_INK
            elif name == "Agent" and i == 4:
                occupied, cell_title, cell_detail = True, "最终答案", "写回用户"
                fill, tfill = RISO_GREEN, RISO_CREAM
            elif name == "工具" and i == 2:
                occupied, cell_title, cell_detail = True, "执行工具", "谁执行"
                fill, tfill = WHITE, RISO_INK
            elif name == "工具" and i == 3:
                occupied, cell_title, cell_detail = True, "回填结果", "虚线回判断"
                fill, tfill = WHITE, RISO_INK
            if occupied:
                if fill == RISO_ORANGE:
                    parts.append(hard_shadow(x, y + 28, step_w, 124, RISO_ORANGE))
                parts.append(rect(x, y + 28, step_w, 124, fill, RISO_INK, sw=4, rx=0))
                parts.append(t(x + 16, y + 76, cell_title, size=16, weight=700, fill=tfill))
                parts.append(t(x + 16, y + 108, cell_detail, size=14, fill=tfill))
            else:
                parts.append(rect(x, y + 48, step_w, 84, RISO_CREAM2, RISO_INK, sw=2, rx=0))
    backfill_x = body_x + 3 * (step_w + gap) + step_w / 2
    parts.append(
        poly(
            f"{backfill_x:.0f},604 {backfill_x:.0f},528",
            RISO_ORANGE,
            marker="arrow-riso-orange",
            dash=True,
            sw=3,
        )
    )
    parts.append(t(backfill_x + 16, 572, "回填", size=16, weight=700, fill=RISO_ORANGE))
    ink_footer(parts, 80, 788, 1440, "主角车道上色。判断是唯一饱和块。工具结果虚线回填，不是另一条正向边。")
    return svg(w, h, "".join(parts))


def reuse_quadrant() -> str:
    """2x2: 可复用 × 可验证. Winning quadrant is SKILL.md."""
    w, h = 1600, 1020
    parts: list[str] = []
    cream_bg(parts, w, h, GROVE_PARCH)
    parts.append(t(80, 80, "写不写回去：可复用 × 可验证", size=40, weight=700, fill=GROVE_FOREST))
    parts.append(
        t(80, 122, "Grove 色板。只有右上角值得写成 SKILL.md。其余三格老实留白。", size=18, fill=GROVE_FOREST)
    )
    plot_x, plot_y, plot = 400, 168, 720
    mid = plot_x + plot / 2
    parts.append(rect(mid - 2, plot_y, 4, plot, GROVE_FOREST, GROVE_FOREST, sw=0, rx=0))
    parts.append(rect(plot_x, plot_y + plot / 2 - 2, plot, 4, GROVE_FOREST, GROVE_FOREST, sw=0, rx=0))
    parts.append(t(plot_x + plot / 2, plot_y + plot + 32, "可复用 →", size=20, weight=700, fill=GROVE_FOREST, anchor="middle"))
    parts.append(t(plot_x - 28, plot_y + 32, "可验证 ↑", size=20, weight=700, fill=GROVE_FOREST, anchor="end"))
    pad = 20
    cell = (plot / 2) - 36
    # Q2 top-left: high verify, low reuse
    q = [
        (plot_x + pad, plot_y + pad, False, "MEMORY", "可验证但不必复用", "召回事实，不养成习惯"),
        (mid + 16, plot_y + pad, True, "SKILL.md", "可复用且可验证", "过门禁后按步骤落盘"),
        (plot_x + pad, plot_y + plot / 2 + 16, False, "结束", "既不复用也难验证", "不写回去"),
        (mid + 16, plot_y + plot / 2 + 16, False, "先过门禁", "想复用但还不可验证", "扫描 / 去重 / 质量"),
    ]
    for x, y, hero, title, line1, line2 in q:
        if hero:
            parts.append(hard_shadow(x, y, cell, cell, GROVE_TERRA))
            parts.append(rect(x, y, cell, cell, GROVE_TERRA, GROVE_FOREST, sw=4, rx=0))
            fg = "#F4F1E6"
        else:
            parts.append(rect(x, y, cell, cell, GROVE_PARCH, GROVE_FOREST, sw=4, rx=0))
            fg = GROVE_FOREST
        parts.append(t(x + 24, y + 56, title, size=24, weight=700, fill=fg))
        parts.append(t(x + 24, y + 100, line1, size=16, fill=fg))
        parts.append(t(x + 24, y + 132, line2, size=16, fill=fg))
    ink_footer(
        parts,
        80,
        948,
        1440,
        "右上角才写 SKILL.md。想复用但不可验证，先过门禁，不要直接保存。",
        fill=GROVE_FOREST,
        fg="#F4F1E6",
    )
    return svg(w, h, "".join(parts))


def focus_detail() -> str:
    """Focus + detail: 判断 is the hero panel."""
    w, h = 1600, 820
    parts: list[str] = []
    cream_bg(parts, w, h, "#FFFFFF")
    parts.append(t(80, 80, "判断这一步到底看什么", size=40, weight=700, fill=AVO_BLUE))
    parts.append(
        t(80, 122, "Avocado Press。左边一块是焦点；右边三张小卡是支持，不要做成均等四宫格。", size=18, fill=AVO_INK)
    )
    parts.append(hard_shadow(80, 176, 880, 520, AVO_BLUE))
    parts.append(rect(80, 166, 880, 520, AVO_BLUE, AVO_BLUE, sw=0, rx=0))
    parts.append(t(120, 230, "判断", size=40, weight=700, fill="#FFFFFF"))
    parts.append(t(120, 286, "谁决策，不是谁执行。", size=22, weight=700, fill=AVO_LIME))
    for i, line in enumerate(
        [
            "上下文已经在，不必再找工具。",
            "能直接回答 → 写最终答案，结束。",
            "缺事实或缺动作 → 才进工具回路。",
            "工具结果必须回来，再判断一次。",
        ]
    ):
        parts.append(t(120, 360 + i * 44, line, size=18, fill="#FFFFFF"))
    supports = [
        (AVO_LIME, AVO_INK, "直接回答", "短支。到最终答案就停。"),
        ("#FFFFFF", AVO_BLUE, "需要工具", "整段放大。执行是下一张卡。"),
        ("#FFFFFF", AVO_BLUE, "虚线回填", "结果进判断，不是新的正向边。"),
    ]
    y = 166
    for fill, ink, title, detail in supports:
        parts.append(rect(1000, y, 520, 160, fill, AVO_BLUE, sw=4, rx=0))
        parts.append(t(1028, y + 56, title, size=22, weight=700, fill=ink))
        parts.append(t(1028, y + 96, detail, size=16, fill=ink))
        y += 180
    parts.append(rect(80, 720, 1440, 56, AVO_BLUE, AVO_BLUE, sw=0, rx=0))
    parts.append(
        t(800, 756, "一张图只放大判断。执行工具另走工具回路，不要和判断抢尺寸。", size=18, weight=700, fill="#FFFFFF", anchor="middle")
    )
    return svg(w, h, "".join(parts))


MERMAID = """sequenceDiagram
    autonumber
    participant Caller as 调用方
    participant Access as 接入层
    participant Session as 会话层
    participant Adapt as 后端适配
    Caller->>Access: OpenStream
    Access->>Session: OnTrackOpen
    Session->>Adapt: Dispatch(track)
    Adapt-->>Session: MediaEvent
    Session-->>Access: OnTrackData
    Access-->>Caller: StreamChunk
"""

HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="use-iframe" content="true">
  <meta name="html-box-height-mode" content="auto">
  <meta name="description" content="请求在支付网关四层中流动的阶段动画：接入、协议、会话、后端适配。默认静态可读，可暂停和重放。">
  <title>请求在网关里流动</title>
  <style>
    :root {
      --ink: #1F2329;
      --muted: #64748B;
      --line: #CBD5E1;
      --blue: #2563EB;
      --purple: #7C3AED;
      --green: #16A34A;
      --pink: #DB2777;
    }
    * { box-sizing: border-box; }
    html, body { margin: 0; }
    body {
      margin: 0;
      padding: 16px;
      color: var(--ink);
      background: #F8FAFC;
      font-family: "Noto Sans SC", ui-sans-serif, system-ui, sans-serif;
      line-height: 1.45;
    }
    .wrap { width: 100%; max-width: 100%; }
    h1 { margin: 0 0 6px; font-size: 20px; }
    p.lead { margin: 0 0 14px; color: var(--muted); font-size: 13px; }
    .controls { display: flex; gap: 8px; margin-bottom: 14px; }
    button {
      border: 1.5px solid var(--line);
      background: #fff;
      border-radius: 999px;
      padding: 6px 14px;
      font: inherit;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
    }
    button[aria-pressed="true"] { background: #FEF3C7; border-color: #D97706; }
    .lane {
      position: relative;
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      padding: 18px 12px 28px;
      border: 1.5px solid var(--line);
      border-radius: 16px;
      background: #fff;
    }
    .stage {
      min-height: 92px;
      padding: 12px;
      border-radius: 12px;
      border: 1.5px solid var(--line);
    }
    .stage:nth-child(1) { background: #FDF2F8; border-color: var(--pink); }
    .stage:nth-child(2) { background: #EFF6FF; border-color: var(--blue); }
    .stage:nth-child(3) { background: #F5F3FF; border-color: var(--purple); }
    .stage:nth-child(4) { background: #ECFDF5; border-color: var(--green); }
    .k { font-size: 12px; font-weight: 700; color: var(--muted); }
    .n { margin-top: 4px; font-size: 15px; font-weight: 700; }
    .d { margin-top: 4px; font-size: 12px; color: var(--muted); }
    .packet {
      position: absolute;
      top: 8px;
      left: 4%;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: var(--blue);
      animation: move 6s linear infinite;
    }
    .paused .packet { animation-play-state: paused; }
    @keyframes move {
      0% { left: 6%; }
      25% { left: 30%; }
      50% { left: 55%; }
      75% { left: 80%; }
      100% { left: 6%; }
    }
    @media (prefers-reduced-motion: reduce) {
      .packet { animation: none; left: 55%; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>请求在网关里流动</h1>
    <p class="lead">动画只解释阶段顺序。四层名称在静止时也能读完；暂停后圆点停在当前层。</p>
    <div class="controls">
      <button id="pause" type="button" aria-pressed="false">暂停</button>
      <button id="reset" type="button">重放</button>
    </div>
    <div class="lane" id="lane">
      <div class="packet" id="packet" aria-hidden="true"></div>
      <div class="stage"><div class="k">L4</div><div class="n">接入</div><div class="d">鉴权与限流</div></div>
      <div class="stage"><div class="k">L3</div><div class="n">协议</div><div class="d">编解码与复用</div></div>
      <div class="stage"><div class="k">L2</div><div class="n">会话</div><div class="d">生命周期</div></div>
      <div class="stage"><div class="k">L1</div><div class="n">后端适配</div><div class="d">差异与重试</div></div>
    </div>
  </div>
  <script>
    const lane = document.getElementById("lane");
    const pause = document.getElementById("pause");
    const reset = document.getElementById("reset");
    const packet = document.getElementById("packet");
    pause.addEventListener("click", () => {
      const paused = lane.classList.toggle("paused");
      pause.setAttribute("aria-pressed", String(paused));
      pause.textContent = paused ? "继续" : "暂停";
    });
    reset.addEventListener("click", () => {
      packet.style.animation = "none";
      packet.offsetHeight;
      packet.style.animation = "";
      lane.classList.remove("paused");
      pause.setAttribute("aria-pressed", "false");
      pause.textContent = "暂停";
    });
  </script>
</body>
</html>
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if any(ord(c) > 127 for c in text):
        raw = path.read_bytes()
        if "\ufffd".encode("utf-8") in raw:
            raise SystemExit(f"replacement char written to {path}")


EVAL_DOC = """<title>飞书画板精美图表 · Human Eval</title>
<callout emoji="🧪" background-color="light-blue" border-color="blue">
  <p>这份文档用来肉眼评测文档精排画板：每种图前面有一句论点。请在飞书 Web 和桌面分别打开画板，点进去改一个节点，确认是原生画板而不是图片。HTML 对照块不是画板。</p>
</callout>
<p>评测包日期 2026-09-03。本地已通过 lint-valid 与 local-render-valid。请在文末记分表填写 feishu-experience-valid。</p>
<h1 seq="auto">怎么评</h1>
<p>先记证据层，再打 1–5 分。SVG / Mermaid 是静态精排图，运动和交互记 N/A。有一项低于 3，或出现截断、豆腐、把 HTML 当成画板，整张图不通过。</p>
<table>
  <colgroup>
    <col width="80"/>
    <col width="160"/>
    <col width="240"/>
    <col width="340"/>
  </colgroup>
  <thead>
    <tr>
      <th background-color="light-gray"><p>ID</p></th>
      <th background-color="light-gray"><p>介质</p></th>
      <th background-color="light-gray"><p>语法</p></th>
      <th background-color="light-gray"><p>你要确认</p></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><p>01</p></td>
      <td><p>SVG 画板</p></td>
      <td><p>分层条带</p></td>
      <td><p>职责 / 边界成列，上下行 API 分色</p></td>
    </tr>
    <tr>
      <td><p>02</p></td>
      <td><p>SVG 画板</p></td>
      <td><p>任务循环 · 分叉</p></td>
      <td><p>工具回路是放大色块；短虚线回填，不绕场</p></td>
    </tr>
    <tr>
      <td><p>03</p></td>
      <td><p>SVG 画板</p></td>
      <td><p>学习闭环 · 三列</p></td>
      <td><p>三列写满对比项；下一轮是标签不是绕场虚线</p></td>
    </tr>
    <tr>
      <td><p>04</p></td>
      <td><p>SVG 画板</p></td>
      <td><p>多列运行</p></td>
      <td><p>请求向右、事件向左，页脚是边界</p></td>
    </tr>
    <tr>
      <td><p>05</p></td>
      <td><p>SVG 画板</p></td>
      <td><p>编号层级</p></td>
      <td><p>右侧每层一个问题；页脚是恢复坐标</p></td>
    </tr>
    <tr>
      <td><p>06</p></td>
      <td><p>Mermaid 画板</p></td>
      <td><p>时序</p></td>
      <td><p>不要被重画成架构分层</p></td>
    </tr>
    <tr>
      <td><p>07</p></td>
      <td><p>HTML5</p></td>
      <td><p>对照：语义运动</p></td>
      <td><p>这不是画板；静止时也能读完四层</p></td>
    </tr>
    <tr>
      <td><p>08</p></td>
      <td><p>空白画板</p></td>
      <td><p>共创</p></td>
      <td><p>能拖便签，不要和精排图锁在一起</p></td>
    </tr>
    <tr>
      <td><p>09</p></td>
      <td><p>SVG 画板</p></td>
      <td><p>对比列 · Riptide</p></td>
      <td><p>钴色块是该行去处，不是每格都上色</p></td>
    </tr>
    <tr>
      <td><p>10</p></td>
      <td><p>SVG 画板</p></td>
      <td><p>枢纽</p></td>
      <td><p>Agent Loop 最大且唯一饱和</p></td>
    </tr>
    <tr>
      <td><p>11</p></td>
      <td><p>SVG 画板</p></td>
      <td><p>时间线 · Coral</p></td>
      <td><p>completed 是高潮；中断/失败是旁路</p></td>
    </tr>
    <tr>
      <td><p>12</p></td>
      <td><p>SVG 画板</p></td>
      <td><p>泳道</p></td>
      <td><p>Agent 车道上色；判断是唯一饱和块</p></td>
    </tr>
    <tr>
      <td><p>13</p></td>
      <td><p>SVG 画板</p></td>
      <td><p>四象限 · Grove</p></td>
      <td><p>右上 SKILL.md 最大；其余老实留白</p></td>
    </tr>
    <tr>
      <td><p>14</p></td>
      <td><p>SVG 画板</p></td>
      <td><p>焦点+细节 · Avocado</p></td>
      <td><p>左边判断最大，右边三张小卡不要均分</p></td>
    </tr>
  </tbody>
</table>
<h1 seq="auto">分层条带</h1>
<p>这张图回答：支付网关每一层屏蔽什么，层间真正暴露哪条 API。</p>
<whiteboard type="svg" path="@./01-layered-strip.svg"/>
<h1 seq="auto">任务循环</h1>
<p>这张图回答：谁决策、谁执行。工具回路才是要放大的分叉；直接回答是短支。</p>
<whiteboard type="svg" path="@./02-task-loop.svg"/>
<h1 seq="auto">学习闭环</h1>
<p>这张图回答：值不值得写回去。上门禁，下三列对比。门禁写的是扫描 / 去重 / 质量，不是保存。</p>
<whiteboard type="svg" path="@./03-learning-loop.svg"/>
<h1 seq="auto">多列运行架构</h1>
<p>这张图回答：请求向右送进 Agent Loop，事件向左投影回宿主。列是职责边界。</p>
<whiteboard type="svg" path="@./04-multicolumn-runtime.svg"/>
<h1 seq="auto">编号层级</h1>
<p>这张图回答：中断之后恢复哪一层。页脚给出 threadId + turnId + itemId。</p>
<whiteboard type="svg" path="@./05-recovery-layers.svg"/>
<h1 seq="auto">Mermaid 时序</h1>
<p>用户已经给了 sequenceDiagram。只把源码放进 whiteboard type=mermaid，飞书服务端自动转成画板，不要重画成 SVG 架构。</p>
<whiteboard type="mermaid" path="@./06-sequence.mmd"/>
<h1 seq="auto">HTML 动画对照</h1>
<p>请求在网关里流动需要看见阶段。画板做不好语义运动，所以走 feishu-html-diagram，而不是假装画板会动。</p>
<html5-block path="@./07-packet-flow.html"/>
<h1 seq="auto">空白共创画板</h1>
<p>现场评审要一起拖便签、改聚类。这是空白画板，不是上面那些精排插图。</p>
<whiteboard type="blank"/>
<h1 seq="auto">对比列</h1>
<p>这张图回答：三种落盘哪一列接什么。钴色是该行更该写入的去处。</p>
<whiteboard type="svg" path="@./09-comparison.svg"/>
<h1 seq="auto">枢纽</h1>
<p>这张图回答：Agent 周围一圈是什么。核心必须最大。</p>
<whiteboard type="svg" path="@./10-hub.svg"/>
<h1 seq="auto">时间线</h1>
<p>这张图回答：一次 Turn 的高潮在完成。Delta 不是完成。Coral 色板，和其他图不是同一套皮。</p>
<whiteboard type="svg" path="@./11-timeline.svg"/>
<h1 seq="auto">泳道握手</h1>
<p>这张图回答：一次调用里用户 / Agent / 工具怎么接力。主角车道上色，不要三条一样灰。</p>
<whiteboard type="svg" path="@./12-swimlane.svg"/>
<h1 seq="auto">四象限</h1>
<p>这张图回答：可复用 × 可验证，哪一格才写 SKILL.md。Grove 色板。</p>
<whiteboard type="svg" path="@./13-quadrant.svg"/>
<h1 seq="auto">焦点+细节</h1>
<p>这张图回答：判断这一步到底看什么。左边一块焦点，右边三张支持卡。Avocado Press。</p>
<whiteboard type="svg" path="@./14-focus-detail.svg"/>
<h1 seq="auto">记分表</h1>
<p>每张图复制一行。Web / 桌面都打开过再把最高证据层写成 feishu-experience-valid。</p>
<table>
  <colgroup>
    <col width="70"/>
    <col width="90"/>
    <col width="90"/>
    <col width="90"/>
    <col width="90"/>
    <col width="90"/>
    <col width="110"/>
    <col width="90"/>
  </colgroup>
  <thead>
    <tr>
      <th background-color="light-gray"><p>ID</p></th>
      <th background-color="light-gray"><p>理解</p></th>
      <th background-color="light-gray"><p>观感</p></th>
      <th background-color="light-gray"><p>语法</p></th>
      <th background-color="light-gray"><p>可编辑</p></th>
      <th background-color="light-gray"><p>可读</p></th>
      <th background-color="light-gray"><p>证据层</p></th>
      <th background-color="light-gray"><p>结论</p></th>
    </tr>
  </thead>
  <tbody>
    <tr><td><p>01</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td></tr>
    <tr><td><p>02</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td></tr>
    <tr><td><p>03</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td></tr>
    <tr><td><p>04</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td></tr>
    <tr><td><p>05</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td></tr>
    <tr><td><p>06</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td></tr>
    <tr><td><p>07</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td></tr>
    <tr><td><p>08</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td></tr>
    <tr><td><p>09</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td></tr>
    <tr><td><p>10</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td></tr>
    <tr><td><p>11</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td></tr>
    <tr><td><p>12</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td></tr>
    <tr><td><p>13</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td></tr>
    <tr><td><p>14</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td><td><p>—</p></td></tr>
  </tbody>
</table>
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write(OUT / "01-layered-strip.svg", layered_strip())
    write(OUT / "02-task-loop.svg", task_loop())
    write(OUT / "03-learning-loop.svg", learning_loop())
    write(OUT / "04-multicolumn-runtime.svg", multicolumn_runtime())
    write(OUT / "05-recovery-layers.svg", recovery_layers())
    write(OUT / "06-sequence.mmd", MERMAID)
    write(OUT / "07-packet-flow.html", HTML)
    write(OUT / "09-comparison.svg", comparison_matrix())
    write(OUT / "10-hub.svg", hub_spoke())
    write(OUT / "11-timeline.svg", turn_timeline())
    write(OUT / "12-swimlane.svg", swimlane_handshake())
    write(OUT / "13-quadrant.svg", reuse_quadrant())
    write(OUT / "14-focus-detail.svg", focus_detail())
    write(OUT / "eval-doc.xml", EVAL_DOC)
    print(f"wrote fixtures to {OUT}")
    for path in sorted(OUT.glob("*.svg")):
        text = path.read_text(encoding="utf-8")
        print(f"{path.name}: {len(text)} bytes, has CJK={any(ord(c) > 127 for c in text)}")


if __name__ == "__main__":
    main()

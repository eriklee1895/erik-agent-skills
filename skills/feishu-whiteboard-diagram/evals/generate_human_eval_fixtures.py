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
            t(x + 16, y + 28, title, size=14, weight=700),
            t(x + 16, y + 50, detail, size=13, fill=MUTED),
        ]
    )


def layered_strip() -> str:
    parts: list[str] = [
        t(40, 48, "支付网关分层：每层屏蔽什么", size=24, weight=700),
        t(40, 76, "自上而下看职责，自下而上看出边界。层间只暴露真实 API。", size=14, fill=MUTED),
        t(1180, 48, "↑ 上行", size=13, weight=700, fill=BLUE_EDGE),
        t(1280, 48, "↓ 下行", size=13, weight=700, fill=GREEN_EDGE),
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
    x = 40
    w = 1440
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
            parts.append(t(236, gy + 5, f"上行 {up}", size=13, fill=BLUE_EDGE))
            parts.append(line(1280, gy - 16, 1280, gy + 16, GREEN_EDGE, marker="arrow-green"))
            parts.append(t(1108, gy + 5, f"下行 {down}", size=13, fill=GREEN_EDGE, anchor="end"))
            y += layer_h + gap
        else:
            y += layer_h
    fy = y + 24
    parts.append(rect(40, fy, 1440, 52, GREEN_SOFT, GREEN_EDGE, sw=2, rx=12))
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


def task_loop() -> str:
    parts: list[str] = [
        rect(40, 32, 1440, 700, CANVAS, CANVAS_EDGE, sw=2, rx=16),
        t(64, 72, "Hermes 普通任务循环：谁决策、谁执行", size=24, weight=700),
        t(64, 100, "能直接回答就结束；需要工具则执行后虚线回填，再判断一次。", size=14, fill=MUTED),
    ]
    caps = [
        (80, 176, 210, "用户任务", BLUE_FILL, BLUE_EDGE),
        (360, 176, 220, "加载上下文", PURPLE_FILL, PURPLE_EDGE),
        (930, 176, 210, "最终答案", GREEN_FILL, GREEN_EDGE),
        (620, 390, 210, "执行工具", BLUE_FILL, BLUE_EDGE),
        (620, 520, 210, "工具结果", PURPLE_FILL, PURPLE_EDGE),
    ]
    for x, y, w, label, fill, edge in caps:
        parts.append(rect(x, y, w, 56, fill, edge, sw=2, rx=28))
        parts.append(t(x + w / 2, y + 36, label, size=15, weight=700, fill=edge, anchor="middle"))
    cx, cy = 720, 204
    parts.append(diamond(cx, cy, 110, 92, ORANGE_FILL, ORANGE_EDGE))
    parts.append(t(cx, cy + 6, "判断", size=15, weight=700, fill=ORANGE_EDGE, anchor="middle"))
    parts.append(line(290, 204, 348, 204, LINE))
    parts.append(line(580, 204, 665, 204, LINE))
    parts.append(line(775, 204, 918, 204, GREEN_EDGE, marker="arrow-green"))
    parts.append(t(846, 190, "直接回答", size=12, fill=GREEN_EDGE, anchor="middle"))
    parts.append(poly("720,250 720,390", ORANGE_EDGE, marker="arrow-orange"))
    parts.append(t(736, 330, "需要工具", size=12, fill=ORANGE_EDGE))
    parts.append(line(725, 446, 725, 512, LINE))
    parts.append(
        poly(
            "620,548 460,548 460,268 720,250",
            PURPLE_EDGE,
            marker="arrow-purple",
            dash=True,
        )
    )
    parts.append(t(360, 536, "结果回填，再次判断", size=13, fill=PURPLE_EDGE, anchor="middle"))
    parts.append(rect(64, 640, 1392, 56, WHITE, CANVAS_EDGE, sw=1.5, rx=12))
    parts.append(
        t(
            760,
            674,
            "蓝 = 动作 · 紫 = 上下文 · 橙 = 判断 · 绿 = 产出。虚线不是另一条正向边。",
            size=14,
            fill=MUTED,
            anchor="middle",
        )
    )
    return svg(1520, 764, "".join(parts))


def learning_loop() -> str:
    parts: list[str] = [
        rect(40, 32, 1440, 780, CANVAS, CANVAS_EDGE, sw=2, rx=16),
        t(64, 72, "学习闭环：值不值得写回去", size=24, weight=700),
        t(64, 100, "复盘之后先过门禁；只有值得复用的才分类落盘，并在后续任务注入。", size=14, fill=MUTED),
    ]

    def capsule(x: float, y: float, w: float, label: str, fill: str, edge: str) -> None:
        parts.append(rect(x, y, w, 56, fill, edge, sw=2, rx=28))
        parts.append(t(x + w / 2, y + 36, label, size=15, weight=700, fill=edge, anchor="middle"))

    capsule(64, 160, 180, "任务完成", GREEN_FILL, GREEN_EDGE)
    capsule(310, 160, 160, "复盘", PURPLE_FILL, PURPLE_EDGE)
    cx, cy = 620, 188
    parts.append(diamond(cx, cy, 120, 96, ORANGE_FILL, ORANGE_EDGE))
    parts.append(t(cx, cy - 2, "值得", size=14, weight=700, fill=ORANGE_EDGE, anchor="middle"))
    parts.append(t(cx, cy + 18, "复用?", size=14, weight=700, fill=ORANGE_EDGE, anchor="middle"))
    capsule(780, 160, 150, "结束", RED_FILL, RED_EDGE)
    capsule(540, 320, 200, "写入门禁", ORANGE_FILL, ORANGE_EDGE)
    stores = [
        (220, 460, 220, "USER.md", "个人偏好 / 习惯", BLUE_FILL, BLUE_EDGE),
        (640, 460, 220, "MEMORY", "可检索事实", PURPLE_FILL, PURPLE_EDGE),
        (1060, 460, 220, "SKILL.md", "可复用方法", GREEN_FILL, GREEN_EDGE),
    ]
    for x, y, w, title, detail, fill, edge in stores:
        parts.append(rect(x, y, w, 88, fill, edge, sw=2, rx=12))
        parts.append(t(x + w / 2, y + 36, title, size=15, weight=700, fill=edge, anchor="middle"))
        parts.append(t(x + w / 2, y + 62, detail, size=13, fill=MUTED, anchor="middle"))
    capsule(430, 610, 220, "后续任务注入", BLUE_FILL, BLUE_EDGE)
    capsule(760, 610, 200, "复用执行", GREEN_FILL, GREEN_EDGE)
    parts.append(line(244, 188, 298, 188, LINE))
    parts.append(line(470, 188, 560, 188, LINE))
    parts.append(line(680, 188, 770, 188, RED_EDGE, marker="arrow-red"))
    parts.append(t(725, 174, "否", size=13, fill=RED_EDGE, anchor="middle"))
    parts.append(poly("620,236 620,320", LINE, marker="arrow-gray"))
    parts.append(t(636, 286, "是", size=13, fill=GREEN_EDGE))
    parts.append(poly("640,376 330,376 330,460", BLUE_EDGE, marker="arrow-blue"))
    parts.append(line(640, 376, 750, 460, PURPLE_EDGE, marker="arrow-purple"))
    parts.append(poly("740,348 1170,348 1170,460", GREEN_EDGE, marker="arrow-green"))
    parts.append(t(560, 404, "扫描 / 去重 / 质量", size=13, fill=ORANGE_EDGE, anchor="middle"))
    parts.append(poly("330,548 330,638 430,638", LINE, marker="arrow-gray"))
    parts.append(line(750, 548, 540, 638, LINE))
    parts.append(poly("1170,548 1170,638 960,638", LINE, marker="arrow-gray"))
    parts.append(line(650, 638, 748, 638, LINE))
    parts.append(
        poly(
            "960,638 1410,638 1410,128 154,128 154,160",
            PURPLE_EDGE,
            marker="arrow-purple",
            dash=True,
        )
    )
    parts.append(t(1320, 150, "下一轮", size=13, fill=PURPLE_EDGE, anchor="middle"))
    parts.append(rect(64, 710, 1392, 56, WHITE, CANVAS_EDGE, sw=1.5, rx=12))
    parts.append(
        t(
            760,
            744,
            "「否」必须有结束态。门禁写的是扫描 / 去重 / 质量，不是「保存」。",
            size=14,
            fill=MUTED,
            anchor="middle",
        )
    )
    return svg(1520, 844, "".join(parts))


def multicolumn_runtime() -> str:
    parts: list[str] = [
        t(40, 48, "运行架构：请求向右，事件向左", size=24, weight=700),
        t(40, 76, "列是职责边界。上排把请求送进 Agent Loop，下排把事件投影回宿主。", size=14, fill=MUTED),
        t(1180, 48, "请求向右 →", size=13, weight=700, fill=BLUE_EDGE, anchor="end"),
        t(1480, 48, "← 事件向左", size=13, weight=700, fill=PURPLE_EDGE, anchor="end"),
    ]
    cols = [
        ("01", "宿主", "发起与投影", PURPLE_FILL, PURPLE_EDGE, "发起请求", "thread/start", "投影到 UI", "item/completed"),
        ("02", "传输", "连接与鉴权", BLUE_FILL, BLUE_EDGE, "Gate", "auth · stream", "Outbound", "event frame"),
        ("03", "协调", "排队与调度", ORANGE_FILL, ORANGE_EDGE, "Processor", "turn queue", "Outbound", "delta / event"),
        ("04", "运行时", "思考与工具", GREEN_FILL, GREEN_EDGE, "Agent Loop", "model · tools", "Events", "item / file"),
    ]
    x0 = 40
    col_w = 348
    gap = 16
    top = 100
    h = 560
    for i, (num, name, duty, fill, edge, req, req_d, ev, ev_d) in enumerate(cols):
        x = x0 + i * (col_w + gap)
        parts.append(rect(x, top, col_w, h, CANVAS, CANVAS_EDGE, sw=2, rx=16))
        parts.append(circle(x + 28, top + 28, 16, edge, edge))
        parts.append(t(x + 28, top + 34, num, size=12, weight=700, fill=WHITE, anchor="middle"))
        parts.append(t(x + 52, top + 24, name, size=16, weight=700))
        parts.append(t(x + 52, top + 46, duty, size=13, fill=MUTED))
        parts.append(rect(x + 16, 168, col_w - 32, 120, fill, edge, sw=2, rx=12))
        parts.append(t(x + col_w / 2, 216, req, size=16, weight=700, fill=edge, anchor="middle"))
        parts.append(t(x + col_w / 2, 244, req_d, size=13, fill=MUTED, anchor="middle"))
        parts.append(rect(x + 16, 488, col_w - 32, 120, WHITE, edge, sw=2, rx=12))
        parts.append(t(x + col_w / 2, 536, ev, size=16, weight=700, fill=edge, anchor="middle"))
        parts.append(t(x + col_w / 2, 564, ev_d, size=13, fill=MUTED, anchor="middle"))
        if i < 3:
            x2 = x + col_w + gap
            parts.append(line(x + col_w - 16, 228, x2 + 16, 228, BLUE_EDGE, marker="arrow-blue"))
            parts.append(line(x2 + 16, 548, x + col_w - 16, 548, PURPLE_EDGE, marker="arrow-purple"))
        if i == 3:
            parts.append(t(x + col_w / 2, 430, "tools ↓", size=13, fill=GREEN_EDGE, anchor="middle"))
            parts.append(line(x + col_w / 2, 288, x + col_w / 2, 476, GREEN_EDGE, marker="arrow-green"))
    fy = 684
    parts.append(rect(40, fy, 1440, 72, GREEN_SOFT, GREEN_EDGE, sw=2, rx=12))
    parts.append(t(80, fy + 28, "边界", size=14, weight=700, fill=GREEN_EDGE))
    notes = ["宿主不跑模型", "传输不理解 turn", "协调不碰工具", "运行时不画 UI"]
    for i, note in enumerate(notes):
        parts.append(t(220 + i * 310, fy + 46, note, size=14, fill=INK, anchor="middle"))
    return svg(1520, 788, "".join(parts))


def recovery_layers() -> str:
    parts: list[str] = [
        t(40, 48, "三层状态，三种恢复粒度", size=24, weight=700),
        t(40, 76, "中断之后到底恢复哪一层：对话、事务，还是某一个动作。", size=14, fill=MUTED),
        t(1480, 48, "一张图回答：从哪继续", size=14, weight=700, fill=BLUE_EDGE, anchor="end"),
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
            parts.append(t(px + pw / 2, py + 50, detail, size=12, fill=MUTED, anchor="middle"))
            px += pw + 16
        y += h
        if between:
            parts.append(line(760, y + 4, 760, y + 36, LINE, marker="arrow-gray"))
            parts.append(t(776, y + 24, between, size=13, fill=MUTED))
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
        t(760, fy + 50, "Delta 是预览 · Completed 是事实", size=13, fill=MUTED, anchor="middle")
    )
    return svg(1520, fy + 92, "".join(parts))


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
    if "支付" in text or "Hermes" in text or "sequenceDiagram" in text or "html-box-height-mode" in text:
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
      <td><p>任务循环</p></td>
      <td><p>紫虚线回填接到判断，不是另一条正向边</p></td>
    </tr>
    <tr>
      <td><p>03</p></td>
      <td><p>SVG 画板</p></td>
      <td><p>学习闭环</p></td>
      <td><p>「否」有结束；下一轮回到任务完成</p></td>
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
  </tbody>
</table>
<h1 seq="auto">分层条带</h1>
<p>这张图回答：支付网关每一层屏蔽什么，层间真正暴露哪条 API。</p>
<whiteboard type="svg" path="@./01-layered-strip.svg"/>
<h1 seq="auto">任务循环</h1>
<p>这张图回答：谁决策、谁执行；工具结果必须虚线回填再判断。</p>
<whiteboard type="svg" path="@./02-task-loop.svg"/>
<h1 seq="auto">学习闭环</h1>
<p>这张图回答：值不值得写回去。门禁写的是扫描 / 去重 / 质量，不是保存。</p>
<whiteboard type="svg" path="@./03-learning-loop.svg"/>
<h1 seq="auto">多列运行架构</h1>
<p>这张图回答：请求向右送进 Agent Loop，事件向左投影回宿主。列是职责边界。</p>
<whiteboard type="svg" path="@./04-multicolumn-runtime.svg"/>
<h1 seq="auto">编号层级</h1>
<p>这张图回答：中断之后恢复哪一层。页脚给出 threadId + turnId + itemId。</p>
<whiteboard type="svg" path="@./05-recovery-layers.svg"/>
<h1 seq="auto">Mermaid 时序</h1>
<p>用户已经给了 sequenceDiagram。按代码图路径插入，不要重画成架构图。</p>
<whiteboard type="mermaid" path="@./06-sequence.mmd"/>
<h1 seq="auto">HTML 动画对照</h1>
<p>请求在网关里流动需要看见阶段。画板做不好语义运动，所以走 feishu-html-diagram，而不是假装画板会动。</p>
<html5-block path="@./07-packet-flow.html"/>
<h1 seq="auto">空白共创画板</h1>
<p>现场评审要一起拖便签、改聚类。这是空白画板，不是上面那些精排插图。</p>
<whiteboard type="blank"/>
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
    write(OUT / "eval-doc.xml", EVAL_DOC)
    print(f"wrote fixtures to {OUT}")
    for name in [
        "01-layered-strip.svg",
        "02-task-loop.svg",
        "03-learning-loop.svg",
        "04-multicolumn-runtime.svg",
        "05-recovery-layers.svg",
    ]:
        text = (OUT / name).read_text(encoding="utf-8")
        print(f"{name}: {len(text)} bytes, has CJK={any(ord(c) > 127 for c in text)}")


if __name__ == "__main__":
    main()

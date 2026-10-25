"""Portable fixed prompts and synthetic references for the 80-request study."""

import random

from PIL import Image, ImageDraw, ImageFont


EXTRA_FIXTURES = {"robot.png", "complex.png"}
FAST_CASES = {"cn-poster", "product-photo", "coordinate-edit", "multi-reference"}


def make_fixtures(folder):
    robot = Image.new("RGB", (1024, 1024), "#fff4df")
    draw = ImageDraw.Draw(robot)
    draw.line((540, 170, 580, 100), fill="#26394c", width=18)
    draw.ellipse((548, 62, 612, 126), fill="#d64035")
    draw.rounded_rectangle((290, 170, 730, 510), 65, fill="#159b91")
    for x in (400, 600):
        draw.ellipse((x - 32, 290, x + 32, 354), fill="#142f4a")
    draw.arc((430, 350, 590, 450), 0, 180, fill="#fff4df", width=16)
    draw.rounded_rectangle((350, 520, 670, 800), 45, fill="#b4bec8")
    draw.polygon(((510, 565), (440, 690), (580, 690)), fill="#edba36")
    draw.line((350, 570, 240, 730), fill="#159b91", width=65)
    draw.line((670, 570, 780, 730), fill="#159b91", width=65)
    for x in (390, 570):
        draw.rounded_rectangle((x, 790, x + 110, 900), 20, fill="#142f4a")
    robot.save(folder / "robot.png")

    scene = Image.new("RGB", (1024, 1024), "#fff4df")
    draw = ImageDraw.Draw(scene)
    draw.text((100, 65), "NOVA", fill="#203344", font=ImageFont.load_default(size=120))
    draw.rectangle((0, 850, 1024, 1024), fill="#e8d4b1")
    draw.rounded_rectangle((660, 610, 890, 895), 30, fill="#207a85")
    draw.line((760, 650, 620, 300), fill="#456e43", width=24)
    draw.line((770, 650, 900, 360), fill="#456e43", width=24)
    for box in ((560, 300, 730, 440), (690, 430, 850, 550), (800, 320, 970, 460)):
        draw.ellipse(box, fill="#78976a")
    draw.ellipse((130, 825, 640, 940), fill="#b9a998")
    draw.rounded_rectangle((180, 490, 540, 890), 45, fill="#d64035")
    draw.ellipse((450, 560, 660, 800), outline="#d64035", width=45)
    draw.rounded_rectangle((230, 580, 470, 700), 16, fill="#f8f0dc")
    draw.text((255, 600), "SUN", fill="#203344", font=ImageFont.load_default(size=65))
    scene.save(folder / "complex.png")


def definitions():
    def case(name, category, prompt, size, criteria, references=(), command="generate", **options):
        return dict(case=name, category=category, command=command, prompt=prompt, size=size,
                    criteria=criteria, references=list(references), **options)

    return [
        case("cn-poster", "typography", "3:4竖版科技杂志封面，暖米白纸张背景。顶部居中深蓝色粗黑无衬线主标题准确写“让创作更自由”，下方小一号副标题“从想法到作品”。下半部是三个错落的青绿色几何纸片，留白充足。只出现这两行文字，各出现一次，不加其他字、标志或水印。", "2K",
             ["Exact headline 让创作更自由", "Exact subtitle 从想法到作品", "Only two text lines without duplicates", "Portrait hierarchy and clean geometric layout"], required_text=["让创作更自由", "从想法到作品"]),
        case("mixed-poster", "typography", "16:9横版技术信息图，白底深蓝色标题“AI 工作流”，标题下是英文副标题“CREATE WITH AI”。中部从左到右三个等宽青绿色卡片，用细箭头连接。卡片上行分别写“输入”“推理”“输出”，下行分别写“Input”“Reason”“Output”。每项文字只出现一次，无额外文字，标签清晰、对齐整齐。", "2K",
             ["All Chinese text exact", "All English text exact", "Three cards in the requested order", "No duplicated or invented labels"], required_text=["AI工作流", "CREATEWITHAI", "输入", "推理", "输出", "Input", "Reason", "Output"]),
        case("product-photo", "photography", "3:2横版真实商业产品摄影。一只哑光青绿色金属手冲咖啡壶，细长弯曲的鹅颈壶嘴、圆形壶盖、黑色弧形把手，置于暖米色石质台面。左侧窗光，右侧柔和接触阴影，壶嘴与把手完整可见。近景，浅景深，材质和白平衡自然。单个产品，不加杯子、文字、品牌或水印。", "2K",
             ["One gooseneck kettle with lid/spout/handle", "Photographic material and credible light", "Complete product without cropped parts", "No extra objects or text"]),
        case("portrait-photo", "photography", "3:4竖版真实生活方式摄影，一位30岁左右的东亚女性，短黑发、圆框眼镜、米色针织衫，坐在窗边木桌旁，双手自然捧着同一个白色陶瓷杯，手和杯子完整可见。柔和阴天窗光、自然皮肤纹理、浅景深，平静微笑。上半身中景，纪实照片质感，无文字、边框或水印。", "2K",
             ["One adult with the specified appearance", "Two anatomically plausible hands holding one cup", "Natural photographic skin/light", "Complete hands and no stray text"]),
        case("editorial-illustration", "illustration", "16:9横版编辑插画，一只小小的红色纸船航行在由展开旧书页组成的海洋上，远处一座简洁灯塔。隐喻探索与知识，纸张纹理、柔和水粉笔触、米白与深蓝主色、克制的红色点缀，大量留白。明确是手工插画而非真实摄影，不画人物、图表、箭头或文字。", "1.5K",
             ["Red paper boat on book-page ocean", "Distant lighthouse", "Handmade paper/gouache editorial style", "Restrained palette and no text/charts"]),
        case("handdrawn-tech", "illustration", "16:9横版手绘技术编辑插画，纯白背景，彩色铅笔线稿叠加淡彩晕染。左侧一个青绿色小机器人把纸条放入中央文件盒，右侧输出一片新长出的叶子，表达知识转化。松散有机线条，薄荷绿和陶土橙点缀，轻微纸纹，大量留白。不添加文字、发光效果、金属3D渲染或灰色背景。", "1.5K",
             ["Robot feeds paper into a file box and leaf emerges", "Visible pencil/wash medium", "White background with restrained accents", "No text/glow/metallic 3D style"]),
        case("chinese-ink", "illustration", "16:9横版中国水墨写意，江南水乡，白墙黑瓦、石拱桥、河上一只乌篷船，远处淡墨山峦与薄雾。疏朗留白，墨色层次和自然晕染，少量赭石秋叶点缀，安静诗意。保持宣纸与水墨质感，不加题字、印章、人物或现代建筑。", "1.5K",
             ["Jiangnan white-wall black-roof scene and stone bridge", "One covered boat", "Ink wash/paper and sparse ochre", "No text/seal/people/modern buildings"]),
        case("3d-icon", "illustration", "1:1方形等距3D图标，一本摊开的奶油白书，书页上方悬浮一片青绿色嫩叶，书和叶片组成单一清晰图标。圆润边角、哑光黏土材质、柔和工作室光、短而自然的接触阴影，纯暖米色背景。图标完整居中，四边留白，不加字母、文字、光环、其他道具或边框。", "1.5K",
             ["Open book and one floating leaf", "Isometric rounded matte 3D form", "Centered complete icon with margin", "Clean background without text/extra props"]),
        case("coordinate-edit", "editing", "把图1 <bbox>100 350 550 780</bbox> 中左侧红色杯子改为深蓝色，杯子外形和把手不变。右侧花瓶、顶部NOVA文字、所有位置和米色背景保持不变，保持扁平矢量风格。", "1.5K",
             ["Only selected cup becomes blue", "Cup silhouette and handle retained", "NOVA and right vase unchanged", "Layout/background retained"], ["objects.png"], "edit", edit_box=[100, 350, 550, 780]),
        case("marker-edit", "editing", "把红框内左侧红色杯子改为深蓝色，保留杯子外形和把手。右侧花瓶、顶部NOVA文字、所有位置和米色背景保持不变，保持扁平矢量风格，移除全部彩色标记。", "1.5K",
             ["Selected cup becomes blue", "Cup silhouette/handle retained", "NOVA/vase/layout retained", "No red marker outline or fill remains"], ["objects.png"], "edit", marker_rect=["10%,35%,45%,43%"], edit_box=[100, 350, 550, 780]),
        case("text-replace", "editing", "把图1 <bbox>70 40 460 210</bbox> 中顶部标题NOVA替换为中文“星野”，保持深蓝粗无衬线字形风格、字号占位和左对齐。只出现“星野”一次，不保留NOVA。杯子、花瓶、背景和其他区域保持不变。", "2K",
             ["Replacement 星野 is exact", "NOVA removed without duplicate title", "Title position and visual weight retained", "Cup/vase/background retained"], ["objects.png"], "edit", required_text=["星野"], forbidden_text=["NOVA"], edit_box=[70, 40, 460, 210]),
        case("object-edit", "editing", "编辑图1：移除右侧青绿色花瓶及黄色花朵，并在原花瓶下半部的位置放一个黄色柠檬。保持左侧红杯子和把手、顶部NOVA标题、米色背景和扁平矢量风格不变。只保留一个红杯子和一个柠檬，不增加其他物体。", "1.5K",
             ["Vase and flower fully removed", "One yellow lemon at the former vase position", "Red cup and NOVA retained", "No extra objects and consistent style"], ["objects.png"], "edit", edit_box=[620, 300, 900, 850]),
        case("multi-reference", "references", "图1提供左侧杯子的外形和把手，图2提供配色：杯子采用图2中央的青绿色，背景采用图2周围的暖米色。只画一个杯子，居中、完整、扁平矢量风格。保留图1的杯子形状，不画花瓶，不复制NOVA或图2色块边框，不加其他文字。", "1.5K",
             ["Cup/handle shape follows reference one", "Teal/cream palette follows reference two", "One complete centered cup", "No vase/title/palette swatch copied"], ["objects.png", "palette.png"]),
        case("character-consistency", "references", "以图1机器人为同一个角色，画它在花园里用小喷壶给一盆幼苗浇水的单张插画。保留青绿色方头、单根红色球头天线、黄色三角胸标、灰色躯干和深蓝色双脚。变成轻微四分之三侧身姿势，保持扁平矢量风格和暖米色背景，不加文字或其他机器人。", "1.5K",
             ["All five distinctive identity cues retained", "One robot in a changed three-quarter pose", "Watering can and one seedling pot", "Consistent flat style and no text"], ["robot.png"]),
        case("alpha-edit", "native", "把图1杯子改成橙黄色，保持杯子外形和把手不变，保持原有透明背景，不添加阴影、文字或其他物体。", "1.5K",
             ["Cup becomes orange/yellow", "Outline and handle retained", "Actual alpha background retained", "No extra object/text/shadow"], ["alpha-cup.png"], "edit", background="transparent"),
        case("decompose", "native", "只拆出图1左侧带SUN标签的红色杯子（包括把手和标签）及顶部NOVA标题，分别成为两个独立透明图层；其余花瓶、枝叶和桌面保留在底图。", "1.5K",
             ["Cup/handle/SUN extracted as one element", "NOVA extracted as a separate element", "Other elements stay in the base", "Alpha/bboxes/z-order permit sensible recomposition"], ["complex.png"], "decompose"),
        case("small-banner", "delivery", "横向产品封面，一只完整的哑光青绿色鹅颈咖啡壶位于画面右侧，暖米色桌面，自然窗光，真实产品摄影。左侧60%保持干净留白，左侧不放道具。不要人物、字母、文字、品牌、标志或水印。", "1500x600",
             ["Final image exactly 1500x600", "Complete gooseneck kettle at the right", "Left sixty percent usable negative space", "No text/people/brands"]),
        case("portrait-infographic", "delivery", "3:4竖版城市慢行信息图，顶部大号深蓝无衬线标题“城市慢行”，浅米色背景，中部一张真实摄影风格的绿树街道小景。下方四张大小一致的浅青色卡片按2乘2排列：左上“步行 35%”，右上“骑行 25%”，左下“公交 30%”，右下“其他 10%”。文字逐字准确，每项只出现一次，不添加其他标题、段落、图表或英文。", "1536x2048",
             ["Exact title and all four labels/percentages", "Exactly four cards in 2x2 requested order", "Readable hierarchy and photographic street inset", "Final portrait size and no extra copy"], required_text=["城市慢行", "步行", "35%", "骑行", "25%", "公交", "30%", "其他", "10%"]),
    ]


def cases():
    result = []
    for definition in definitions():
        configs = [("pro", "standard"), ("flash", "standard")]
        if definition["case"] in FAST_CASES:
            configs.append(("pro", "fast"))
        for model, mode in configs:
            for repeat in (1, 2):
                config = f"{model}-{mode}"
                result.append({**definition, "id": f"{definition['case']}-{config}-r{repeat}",
                               "model": model, "mode": mode, "configuration": config, "repeat": repeat})
    random.Random(20261025).shuffle(result)
    smoke = [f"{name}-{model}-standard-r1" for name in ("cn-poster", "coordinate-edit") for model in ("flash", "pro")]
    return [next(case for case in result if case["id"] == name) for name in smoke] + [case for case in result if case["id"] not in smoke]


def prompt_cases():
    """Three preregistered recipe comparisons, not missing-result retries."""
    source = {case["case"]: case for case in definitions()}
    experiments = [
        ("ab-edit-preservation", source["coordinate-edit"],
         "Compare a minimal edit instruction with the full coordinate+preservation recipe as a bundle; do not attribute the result to coordinates alone.",
         {"minimal": "把图1左侧红色杯子改为深蓝色。", "explicit": source["coordinate-edit"]["prompt"]}),
        ("ab-edit-language", source["text-replace"],
         "Check the old claim that Chinese editing operations need English instructions, with the same box, replacement and preservation requirements.",
         {"chinese": source["text-replace"]["prompt"],
          "english": 'In image 1 replace the top title NOVA inside <bbox>70 40 460 210</bbox> with the exact Chinese text "星野". Keep its dark-blue bold sans-serif style, occupied title area and left alignment. Show 星野 once and remove NOVA completely. Keep the cup, vase, background and all other areas unchanged.'}),
    ]
    infographic = dict(source["portrait-infographic"], criteria=[
        "Exact title and all four labels/percentages", "Four cards in the requested 2x2 order",
        "Translucent frosted cards over a photographic street", "Legible hierarchy with no duplicated or extra copy"])
    short = '3:4竖版信息图，绿树街道真实摄影为底图。顶部居中深蓝色大标题“城市慢行”。四张白色半透明毛玻璃卡片按2乘2排列在画面两侧，可以透过卡片看到背景，柔和圆角。左上“步行 35%”，右上“骑行 25%”，左下“公交 30%”，右下“其他 10%”。深蓝色清晰文字，每项只出现一次，不加其他文字、图表或图标。'
    detailed = '3:4竖版数据新闻信息图，全画幅真实摄影质感的绿树街道底图，Sony A1 50MP，soft overcast daylight，色彩自然，保持摄影而非CGI/游戏截图/3D渲染。顶部3%-12%居中标题“城市慢行”，深蓝色粗无衬线黑体，字号占高度约1/9。下方四张等尺寸卡片按2乘2排布：左上x4% y30%宽24%高18%写“步行 35%”；右上x72% y30%同尺寸写“骑行 25%”；左下x4% y58%同尺寸写“公交 30%”；右下x72% y58%同尺寸写“其他 10%”。卡片为frosted white glass毛玻璃效果，rgba(255,255,255,0.7)填充、backdrop-blur约24px、1px rgba(255,255,255,0.4)浅白描边、16px圆角、柔和投影，必须能透过卡片看见背后街道，禁止不透明白纸/卡纸/亚克力板。卡片内深蓝#1E293B无衬线文字，数字tabular numerals，字号清晰。所有文字逐字准确，每项只出现一次。只允许标题和四组标签数字，不加其他文字、图表或图标。'
    experiments.append(("ab-infographic-detail", infographic,
                        "Compare concise semantic directions with a longer camera/CSS/position recipe for the same text, four-card order and frosted-photo intent; size and references are fixed.",
                        {"concise": short, "detailed": detailed}))
    result = []
    for name, base, hypothesis, variants in experiments:
        for variant, prompt in variants.items():
            for model in ("pro", "flash"):
                for repeat in (1, 2):
                    result.append({**base, "case": name, "id": f"{name}-{variant}-{model}-r{repeat}",
                                   "prompt": prompt, "model": model, "mode": "standard",
                                   "configuration": f"{model}-standard", "repeat": repeat,
                                   "variant": variant, "hypothesis": hypothesis})
    random.Random(2026102501).shuffle(result)
    return result


def marker_cases():
    base = next(case for case in definitions() if case["case"] == "marker-edit")
    result = []
    for model in ("pro", "flash"):
        for variant, alpha in (("filled", 80), ("outline", 0)):
            for repeat in (1, 2):
                result.append({**base, "case": "ab-marker-opacity", "id": f"ab-marker-opacity-{variant}-{model}-r{repeat}",
                               "model": model, "mode": "standard", "configuration": f"{model}-standard",
                               "repeat": repeat, "variant": variant, "marker_alpha": alpha,
                               "hypothesis": "Hold prompt/box/stroke/size/reference fixed and compare alpha80 fill with alpha0 outline after observed pink-marker residue in the main study."})
    random.Random(2026102502).shuffle(result)
    return result

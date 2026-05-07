# prompts_i18n.py

"""
Internationalization (i18n) module for VQA Prompts.
This file centralizes all user-facing strings, prompt templates, and language-specific logic.
'zh' corresponds to Chinese, 'en' corresponds to English.
"""

PROMPTS = {
    'zh': {
        # --- MODIFICATION FOR P3: Added localized QA format example ---
        "QA_FORMAT_EXAMPLE": """
{
    "object describe": {
        "question": "<完整自然问题>",
        "correct_option": "<基于图像和标注事实的答案>"
    },
    "defect detection": {
        "question": "<完整自然问题>",
        "correct_option": "是，检测到缺陷。"
    },
    "defect classification": {
        "question": "<完整自然问题>",
        "correct_option": "<类别名称>"
    },
    "defect count": {
        "question": "总共有多少个缺陷？各类缺陷分别有多少？",
        "correct_option": "总共5个缺陷，其中：开路2个，短路3个。"
    },
    "defect location": {
        "question": "关于这些缺陷，它们主要出现在图像的哪些位置？",
        "correct_option": "缺陷主要分布在图像的中心和右下角区域。中心区域的缺陷表现为一条走线上的断裂，而右下角的缺陷则是焊盘上的一个明显凹坑。这些位置的缺陷表明可能存在应力集中或腐蚀问题。"
    },
    "defect detail describe": {
        "question": "<完整自然问题>",
        "correct_option": "<基于图像和标注事实的答案>"
    },
    "defect coordinates": {
        "question": "找到图像中的开路",
        "correct_option": "{[[0,0,0,0]]}"
    },
    "defect analysis": {
        "question": "<完整自然问题>",
        "correct_option": "<基于图像和标注事实的答案>"
    },
    "component count": {
        "question": "总共有多少个元件？各类元件分别有多少？",
        "correct_option": "总共8个元件，其中：电阻5个，电容3个。"
    },
    "component type": {
        "question": "<完整自然问题>",
        "correct_option": "<类别名称>"
    },
    "component location": {
        "question": "这些元件在电路板上是如何布局的？",
        "correct_option": "这些元件主要集中在电路板的左上角，形成一个密集的阵列。这种布局通常表明它们构成了一个完整的功能单元，例如电源管理模块或信号处理单元。"
    },
    "component describe": {
        "question": "<完整自然问题>",
        "correct_option": "<基于图像和标注事实的答案>"
    },
    "component coordinates": {
        "question": "找到图像中的电阻",
        "correct_option": "{[[0,0,0,0],[0,0,0,0],[0,0,0,0]]}"
    },
    "component analysis": {
        "question": "<完整自然问题>",
        "correct_option": "<基于图像和标注事实的答案>"
    }
}
""",
        # --- MODIFICATION FOR P3: Added localized question type names ---
        "QUESTION_TYPES": {
            "object describe": "object describe",
            "defect detection": "defect detection",
            "defect classification": "defect classification",
            "defect count": "defect count",
            "defect location": "defect location",
            "defect detail describe": "defect detail describe",
            "defect coordinates": "defect coordinates",
            "defect analysis": "defect analysis",
            "component count": "component count",
            "component type": "component type",
            "component location": "component location",
            "component describe": "component describe",
            "component coordinates": "component coordinates",
            "component analysis": "component analysis",
        },
        # --- General Prompts & Templates (COMPARE_PROMPT_HEADER 和 LLM_PROMPT_HEADER 保持不变) ---
        "LLM_PROMPT_HEADER": """
**【最高指令：语言统一】**
**你本次任务的所有输出，包括问题（question）和答案（correct_option），都必须、且只能使用【简体中文】。严禁在任何字段的任何部分出现任何英文单词、字母或标点（JSON格式要求的标点除外）。这是一个绝对的、必须遵守的规则。**

{random_prompt_intro}

【任务重点说明】
{task_focus}

【数据集信息】
- 描述：{dataset_description}
- 图像尺寸：原始 {original_width}x{original_height}, 调整后 {resized_width}x{resized_height}

{additional_context}

【任务说明】
我提供了图像及其相关的辅助信息。请先仔细分析这些信息，然后按照以下问题类型生成问题和对应的正确答案（不要生成选项）：

{questions_list_prompt}

【JSON格式要求】
请严格按照以下JSON格式生成高质量的JSON，只需要生成question和correct_option字段，确保所有键和值都使用双引号：
{qa_format_example}

【输出硬性要求】
- 只能输出一个JSON对象，不要输出Markdown代码块、解释、前后缀或额外文本。
- 必须包含上方请求的每一个问题类型，不得遗漏，也不得新增未请求的问题类型。
- 每个问题类型下必须同时包含非空的question和correct_option字段。
- 如果【结构化标注事实】中给出了类别、数量或坐标，你必须严格遵守，不得自行修改、增删或猜测。

【注意事项】
1.  **再次强调最高指令：所有生成的内容，包括问题和答案，必须100%是简体中文。**
2.  请在确保问题清晰、专业且与图中实际内容（包括提供的辅助信息）相关的条件下创建多样化的内容。
3.  确保所有答案与图像中的实际内容一致，术语专业、描述准确。
4.  详细描述特征和位置，保证答案准确、专业且详尽。
5.  所有回答输出时必须用双引号包围，确保生成的JSON格式完全正确。
6.  {map_instruction}
7.  所有的回答都要和当前问题相关，不要引入其他问题的回答。
{specific_rules}
""",
        "COMPARE_PROMPT_HEADER": """
**【最高指令：语言统一】**
**你本次任务的所有输出，包括问题（question）和答案（correct_option），都必须、且只能使用【简体中文】。严禁在任何字段的任何部分出现任何英文单词、字母或标点（JSON格式要求的标点除外）。这是一个绝对的、必须遵守的规则。**

作为工业缺陷质检员，请利用提供的多张对比图片（正常样本、缺陷样本、bbox标注图、类别标注图）和缺陷文本信息，生成深度技术分析型VQA数据。问题应涵盖缺陷特征识别、分类依据、产生原因以及对产品功能和可靠性的影响，答案需结合图像特征和文本标注提供系统、专业的缺陷知识。

【数据集信息】
- 描述：{dataset_description}
- 图像尺寸：原始 {original_width}x{original_height}, 调整后 {resized_width}x{resized_height}
- 数据集包含两张对比图片：一张正常样本（OK图像，未发现缺陷）和一张缺陷样本（NG图像，存在缺陷），请对比分析两图差异。

【缺陷信息】
{defect_info_str}

【缺陷位置描述指南】
{location_prompt}

【任务说明】
我提供了相同图像的四种不同形式（无缺陷图像、带有分类的边界框标注图像、无分类的边界框标注图像和无标注的缺陷图像），请先仔细分析图像中的缺陷情况，然后按照以下问题类型生成问题和对应的正确答案(不要生成选项)：

{questions_list_prompt}

【**重要指导 - 对比分析**】
请特别注意，对于以下问题，你的回答必须基于对**OK（正常样本）图像**和**NG（缺陷样本）图像**的**严格对比分析**。通过识别NG图像中与OK图像的差异来确定缺陷的存在、类型、位置和坐标。

-   **图像角色必须固定：** 请以结构化标注事实中的异常/NG图像作为缺陷答案对象。OK图像只能作为对照参考，严禁把OK图像中的正常结构当作缺陷答案。
-   **针对 'defect detection' 问题：** 请对比OK图和NG图，明确指出在NG图中是否发现与OK图不一致的异常区域。
-   **针对 'defect coordinates' 问题：** 请对比OK图和NG图，找出所有与正常样本不符的区域（即缺陷），并提供这些缺陷的**精确边界框坐标**。确保你的坐标是基于NG图像中识别到的实际缺陷位置。
-   **针对 'defect classification' 和 'defect detail describe' 问题：** 你的回答应基于对比后识别出的缺陷的类型和外观特征。

【JSON格式要求】
请严格按照以下JSON格式生成高质量的JSON，只需要生成question和correct_option字段，确保所有键和值都使用双引号：
{qa_format_example}

【输出硬性要求】
- 只能输出一个JSON对象，不要输出Markdown代码块、解释、前后缀或额外文本。
- 必须包含上方请求的每一个问题类型，不得遗漏，也不得新增未请求的问题类型。
- 每个问题类型下必须同时包含非空的question和correct_option字段。
- 如果【结构化标注事实】中给出了类别、数量或坐标，你必须严格遵守，不得自行修改、增删或猜测。

【注意事项】
1.  **再次强调最高指令：所有生成的内容，包括问题和答案，必须100%是简体中文。**
2.  请在确保问题清晰、专业且与图中实际内容（包括提供的辅助信息）相关的条件下创建多样化的内容。
3.  确保所有答案与图像中的实际内容一致，术语专业、描述准确。
4.  详细描述特征和位置，保证答案准确、专业且详尽。
5.  所有回答输出时必须用双引号包围，确保生成的JSON格式完全正确。
6.  {map_instruction}
7.  所有的回答都要和当前问题相关，不要引入其他问题的回答。
{specific_rules}
""",
        "LOCATION_PROMPT": """
请使用精确的方位词描述缺陷位置，遵循以下规则：
1.  将图片分为九个区域：左上、中上、右上、左中、中心、中右、左下、中下、右下。
2.  必须先指明缺陷所在的图像区域（九宫格），然后再描述缺陷在**该区域内**或**与周围元件、走线、特征的相对位置**。
3.  可使用的参考点：PCB板边缘、大型元器件、标记点、焊盘区域、特征明显的走线。
4.  精确描述距离关系，例如"距离左边缘约2cm处"、"紧邻右上角大型IC"。
5.  使用时钟方位辅助描述，如"在3点钟方向"、"从中心向7点钟方向"。
6.  避免模糊表述，如"某处"、"一个地方"，必须给出明确空间位置。
7.  对于多个相同类型缺陷，需区分描述每一个，如"左上区域有两处短路，一个靠近边缘，另一个位于中部走线处"。
8.  **在描述缺陷位置时，优先提及缺陷与PCB板上其他元件、焊盘或走线的相对关系。例如：在电阻R12的引脚处、靠近芯片U3的焊盘上、位于两条平行走线之间。**

错误示例：
- "物体表面有一个短路" (位置信息缺失)
- "板子上方有缺陷" (太过笼同)

正确示例：
- "在右下区域，距离下边缘约1.5cm处的两条平行走线之间存在短路"
- "左中区域，在大型IC的左侧约5mm处的细线上出现鼠咬"
- "中心区域，靠近三极管Q1的集电极焊盘处有一个焊桥"

请使用专业、精确且自然的语言描述缺陷位置,避免使用坐标或公式.描述应当让检测人员能够直观快速地定位缺陷。
""",
        "COMPONENT_LOCATION_PROMPT": """
请使用精确的方位词描述元件在PCB图像中的分布与位置，遵循以下规则：
1.  将图片划分为九个区域：左上、中上、右上、左中、中心、中右、左下、中下、右下；
2.  必须先指明元件所在的图像区域（九宫格），再描述元件在**该区域内**或**与周围其他元件、连接器、走线、特征的相对位置**，例如："图片左上区域的边缘附近分布有多个电容"；
3.  可使用的参考点包括：PCB板边缘、大型IC、连接器、特征明显的走线、焊盘阵列等；
4.  建议结合距离关系进行描述，例如："距离右边缘约2cm处有一排贴片电阻"，"紧邻中心区域的大型IC右侧分布着多个SOT23封装的晶体管"；
5.  可使用时钟方向辅助表达，如："在3点钟方向分布"，"自中心区域向7点钟方向延伸的走线上排列着多个同类元件"；
6.  避免模糊描述，如"某处有电阻"，应明确区域与相对关系；
7.  如存在多个同类元件，应加以区分说明，如："左中区域有两组电解电容，一组沿走线边缘排布，另一组靠近左侧连接器"。
8.  **在描述元件位置时，请同时考虑元件在整个图像中的区域以及它与PCB板上其他关键元件、走线或特征的相对位置。例如：在处理器芯片U1旁边、靠近USB接口的焊盘区域、沿着电源走线排列。**

错误示例：
- "板子中间有几个元件"（位置模糊，不明确区域）
- "上方有一个电容"（未指明具体区域或参考物）

正确示例：
- "在右上区域，距离右边缘约1cm处沿水平走线排列着三颗贴片电阻"
- "左下区域的大型IC周围环绕布置了8颗SOT23封装的晶体管"
- "中心区域偏右部，靠近一组焊盘阵列分布着4颗二极管"

请使用专业、自然且定位明确的语言描述元件位置，避免使用像素坐标或公式表达，描述应有助于读者直观快速理解元件的空间分布特征。
""",
        "ANALYSIS_AND_DESCRIBE_RULES_PROMPT": """---
**【答案字段(correct_option)的生成指导】**

1.  **关于分析类问题 (`defect analysis`, `component analysis`)：**
    * 请不要随机遗漏关键内容。答案必须包含：质量/现象判断、可能形成原因、功能或可靠性影响、检测或修复建议。
    * 如果【结构化标注事实】显示存在多个缺陷类别，必须先给出整体风险判断，再分别覆盖每一个类别的影响或风险，不得只分析其中一种或最显著的一种。
    * 如果是元件分析问题，答案应围绕已标注元件的电路作用、布局合理性和可能功能展开，不要把无缺陷元件描述成缺陷。
    * 原因分析必须与缺陷类型匹配：PCB制造类缺陷（开路、短路、鼠咬、杂铜、缺孔等）优先从蚀刻、曝光、显影、钻孔、铜箔残留、污染或机械损伤角度分析；PCBA焊接类缺陷（缺焊、焊桥、多焊、锡珠等）优先从焊膏印刷、贴装偏移、回流温度曲线、焊盘污染角度分析；装配类缺陷（缺少螺丝、螺丝松动、缺少元件、布线松动等）优先从装配遗漏、固定不良、线束安装和工位检查角度分析。
    * 区分可观察事实和合理推断。可观察事实必须来自图像或结构化标注；工艺原因和功能影响必须使用“可能”“通常”“可能导致”等谨慎表达。
    * 禁止凭空提及图中未明确出现的CPU、风扇、散热器、连接器、具体芯片编号或具体电路模块。除非图像中清晰可见，不得把贴片元件描述成色环电阻或通孔引脚元件。
    * 确保答案结构清晰，逻辑严谨，专业术语运用准确。
    * **重要：在你的回答中，请避免使用任何数字序号或列表符号（如 '1.', '2.', '-' 等）。请使用自然段落和衔接词（如“此外”、“另外”、“针对此问题”等）来组织你的分析内容，使其呈现为一篇连贯的专业报告。**

2.  **关于描述类问题 (`defect detail describe`, `component describe`)：**
    * **对于 `defect detail describe` (缺陷细节描述)：**
        * 请聚焦于缺陷的**视觉特征**，例如：形状、大小、颜色、纹理、边缘特征等外观细节。
        * 如果【结构化标注事实】显示存在多个缺陷类别，必须逐类描述每一种缺陷的视觉特征，至少每个类别都有一句清晰描述。
    * **对于 `component describe` (元件描述 - 外观特征)：**
        * 请详细描述元件的**主要外观特征**，例如：元件的形状、大致尺寸、颜色、材质、表面纹理、丝印文字或标志、引脚数量、封装类型等。
        * 如果存在多个元件类别，必须覆盖全部已标注类别，不得只描述其中一种。
    * **重要：在你的回答中，请避免使用任何数字序号或列表符号。请使用自然段落来组织你的描述内容。**

3.  **关于位置描述问题 (`defect location`, `component location`)：**
    * **问题(`question`)**: 请生成一个自然的、符合人类提问习惯的关于物体空间分布的问题。例如：“这些元件在电路板上是如何布局的？” 或 “图中缺陷主要集中在哪些区域？”。
    * **答案(`correct_option`)**: 请生成一段描述性的文字作为答案。这段文字应首先**概括**物体（缺陷或元件）的主要分布区域（例如，使用“主要分布在……区域”、“集中在……”等短语）。然后，可以进一步**举例说明**一两个具体位置的特征，并可简要**分析**这种布局可能意味着什么（如“这种密集的布局可能是一个功能模块”）。请参考【缺陷/元件位置描述指南】中的原则来组织语言，但最终要输出**流畅的自然语言段落**，而不是结构化的列表。**严禁直接输出位置列表或坐标。**

4.  **【重要】关于分类/类型问题 (`defect classification`, `component type`):**
    * 对于这类问题，`correct_option` 字段必须只包含类别名称，不要添加解释、定义或描述性句子。
    * 如果只有一个类别，答案只写该类别名称，例如：“缺焊” 或 “电阻”。
    * 如果存在多个类别，答案必须列出全部类别，使用中文顿号连接，例如：“焊桥、缺焊”。严禁只写主要类别、最显著类别或其中任意一个类别。
---
**【问题字段(question)的生成指导 - 核心规则】**

请在 `question` 字段中直接生成完整、自然、可独立阅读的问题句子。后续程序不会再为你的问题自动拼接主语或前缀，因此不得只返回“的详细特征是什么？”、“分析其产生原因并给出建议”这类残缺片段。

**问题写作要求：**
* 问题应明确指向当前图像、标注区域或对比图中的异常区域，避免“这个”“它”等指代不明的表达。
* 问题应听起来像质检工程师或数据集标注员提出的问题，不要像模板占位符。
* 同一张图中的不同问题应尽量改变问法，但不要牺牲清晰度。
* 不要把类别、数量、坐标等答案直接泄露在问题中，除非该问题本身需要点名已知目标类别。
* 对于 `object describe`，问题可以固定或接近固定为“请描述这张图像。”。
* 对于分类/类型问题，问题应完整，例如“图中标注的缺陷属于哪一类？”或“边界框内的目标元件类型是什么？”。

**问题写作维度：**
* 描述类问题应询问可观察外观证据，例如形状、颜色、边缘、缺失、残留、连接状态或封装特征。
* 分析类问题应询问影响、可能原因和质检建议，但不要使用固定套话。
* 分类/类型问题应明确询问类别，不要泄露答案。
* 对比样本问题应明确答案对象是异常图像，正常图像只作为参考。
* 不要逐字复制本提示中的任何句子作为 `question`。

**坏问题示例：**
* “的详细特征是什么？”（残缺片段）
* “请分析图中的缺陷分析其产生原因并给出建议。”（重复和病句）
* “请问标注的目标类型”（口语化且不完整）
* “这个问题是什么？”（指代不清）
---
""",
        # --- MODIFICATION FOR P4: Improved prompt for object describe ---
        "P3_OBJECT_DESCRIBE_PROMPT": """
【P3 'object describe' 专属指导】
针对 'object describe' 类型，你的答案(`correct_option`)应该是一句简洁、自然的单句，用以概括图像的核心内容。请避免使用固定模板，尝试让描述多样化。
你的问题(`question`)字段应固定为`"描述这张图像"`。

下面是一些**多样化的答案示例**，请参考其风格，不要照搬：
- **如果图像是电路板概览：**
  - '这是一张印刷电路板的概览图。'
  - '图中展示了一块完整的PCB。'
  - '一幅关于印刷电路板的图像。'
- **如果图像是特定元件特写：**
  - '这张图片聚焦于一个电阻元件。'
  - '图中特写了一个电容。'
  - '一张展示SOT23封装晶体管的特写图像。'
- **如果图像展示特定缺陷：**
  - '该图像展示了一个短路缺陷。'
  - '图中内容为一个开路缺陷的特写。'
  - '聚焦于一处鼠咬缺陷的图像。'

**核心要求：** 答案要精炼、准确，并能反映出图像的主体。
""",
        "P1_COMPONENT_ANALYSIS_PROMPT": """
【P1元件分析问题专属指导】
在为 'component analysis' 类型生成 `question` 字段时，请生成完整问题，并专注于提问该元件的**核心功能、在电路中的作用、或其主要用途**。
例如，可以生成：`'图中标注的元件在电路中可能承担什么功能？'` 或者 `'请分析该元件在当前电路设计中的可能作用。'`
""",
        "RESISTOR_HINT_PROMPT": """
"提示：图中电阻的丝印为 '{silkscreen_code}'，其计算出的电阻值为 {resistor_value_hint}。请在你的描述和分析中参考这些信息。"
- **元件功能 (component analysis) 问题**：请确保答案明确说明电阻的**主要功能是限流、分压等**，并**务必包含其精确的计算阻值 '{resistor_value_hint}'**。请勿提及容差。
- **元件描述 (component describe) 问题**：在描述电阻外观特征时，请结合图像信息，**务必提及其计算阻值 '{resistor_value_hint}'**，例如其颜色环、尺寸、封装类型等。请勿提及容差。
- 请确保您的回答严格基于提供的丝印值和计算阻值，避免自行臆测或提供不符信息。
""",
        "SOLDER_JOINT_HINT_PROMPT": "请确保问题和答案都明确指向图中焊点的基本功能和作用，避免引入其他元件类型。",
        "P2_COMPONENT_BBOX_PROMPT": """---
**【P2 类型专属强制指令：严格聚焦边界框】**
**至关重要：** 当前提供的主图像是一张**仅包含边界框**的图。这些边界框标出了所有需要您关注和分析的目标物体。
**您的任务必须严格遵守以下规则：**
1.  **分析对象仅限框内**：您生成的所有**分析 (`component analysis`)**、**描述 (`component describe`)** 和 **类型判断 (`component type`)** 的回答，**必须且只能**针对图像中**边界框内的物体**。
2.  **忽略框外一切**：**绝对禁止**描述、分析或提及边界框之外的任何背景、走线或其他未被框选的特征。您的视野必须被限制在这些框内。
3.  **基于外观和布局**：由于没有提供类别标签，您的所有回答都必须基于框内物体的**视觉外观**（形状、大小、颜色、引脚特征等）和它们的**空间布局**（排列方式、密度、相对位置）。
4.  **覆盖所有边界框**：如果图中有多个边界框，回答必须综合覆盖所有框；如果结构化事实中存在多个元件类别，类型、描述和分析必须覆盖全部类别。
5.  **不要把框线当作目标**：边界框只是提示区域，不是元件本体；不要描述“框很大/框很明显”这类无关内容。
6.  **禁止猜测具体身份**：在回答 `component type` 或 `component analysis` 时，您可以根据外观进行通用分类（例如，“这看起来像一个贴片电阻或电容”），但**严禁**猜测其具体的型号、规格或精确功能。回答应侧重于其可能的通用角色（如“可能用于滤波”）。
7.  **回答示例 (`component describe`)**：“图中框选的物体呈长方形，黑色，两侧有金属引脚，尺寸较小，紧密排列。”(正确，只描述框内物体外观)
8.  **回答示例 (`component analysis`)**：“图中框选的多个小型元件密集排列，可能构成一个信号处理或电源滤波模块。它们的布局整齐，显示出良好的贴装工艺。”(正确，基于布局和通用功能分析)
**任何偏离边界框的回答都将被视为错误。请将边界框视为您唯一的分析范围。**
---
""",
        "P2_DEFECT_BBOX_PROMPT": """---
**【P2 类型专属强制指令：严格聚焦边界框】**
**至关重要：** 当前提供的主图像是一张**仅包含边界框**的图。这些边界框标出了所有需要您关注和分析的**缺陷区域**。
**您的任务必须严格遵守以下规则：**
1.  **分析对象仅限框内**：您生成的所有**分析 (`defect analysis`)**、**描述 (`defect detail describe`)** 和 **分类 (`defect classification`)** 的回答，**必须且只能**针对图像中**边界框内的异常特征**。
2.  **忽略框外一切**：**绝对禁止**描述、分析或提及边界框之外的任何正常区域、背景或其他未被框选的特征。您的视野必须被限制在这些框内。
3.  **基于异常外观**：您的所有回答都必须基于框内区域展现出的**异常视觉特征**（例如，颜色异常、形状不规则、断裂、多余物质等）。
4.  **覆盖所有边界框**：如果图中有多个边界框，回答必须综合覆盖所有框；如果结构化事实中存在多个缺陷类别，分类、描述和分析必须覆盖全部类别。
5.  **不要把框线当作缺陷**：边界框只是提示区域，不是缺陷本体；不要描述“框很大/框很密集”这类无关内容。
6.  **回答示例 (`defect detail describe`)**：“图中框选的区域显示出一条不规则的深色划痕，贯穿了数条铜质走线。”(正确，只描述框内异常)
7.  **回答示例 (`defect analysis`)**：“框内的短路缺陷可能会导致相关电路功能失效并可能损坏上游元件。这通常由蚀刻过程中的掩膜问题或保质期外的化学品引起。”(正确，分析框内缺陷)
**任何偏离边界框的回答都将被视为错误。请将边界框视为您唯一的分析范围。**
---
""",
        "LABELED_OBJECT_PROMPT": """--- 特别重要：【已提供对象信息】的分析与描述问题强制指导 ---
鉴于本图像已在文本中提供了明确的{object_type_name}信息（详见‘已识别的{object_type_name}信息’部分），在回答如 ‘{object_type_name}分析’、‘{object_type_name}描述’、‘{object_type_name}分类’ 等问题时，您的答案**必须且只能**基于这些**已提供信息**中的{object_type_name}进行。
**严禁**讨论任何**未在信息中提及**的特征。
**更重要的是：严禁**生成诸如‘未发现{object_type_name}’、‘无法分析’、‘图中未检测到{object_type_name}’、‘无{object_type_name}信息’等任何形式的表示**对象不存在或无法分析/描述**的内容，因为我们已知图中存在{object_type_name}。
您的回答应该始终是关于**已存在的**{object_type_name}的详细、专业的分析或描述。
--- 结束特别重要指导 ---
""",
        "COMPONENT_SUBTYPE_HINT_PROMPT": """
【元件子类型及其外观特征详细指南】
{component_describe_info}
在回答元件相关问题（特别是 'component describe', 'component type', 'component analysis'）时，请优先使用上述指南中提供更具体、更专业的元件子类型名称进行描述（例如，如果图像特征符合“热敏电阻”的描述，请使用“热敏电阻”而非仅仅“电阻”）。如果图像特征或提供的描述不足以确定具体子类型，则回退到通用类型（如“电阻”、“电容”）。在回答 'component describe' 时，请综合图像信息和上述指南，详细描述元件的视觉特征。
""",
        "DISTRACTOR_BASE_PROMPT": """
核心要求：你生成的每个干扰选项都必须与以下“正确答案”**在主题和专业性上保持一致**，但在**关键信息上是错误的或误导性的**。
请确保干扰选项的**句式结构、语言风格和大致长度与正确答案相似**，以保持选项的统一性。
同时，每个干扰选项都必须与正确答案以及其他干扰选项之间有**明显区分度**，避免使用同义词或过于接近的表述。
所有的缺陷或元件名称必须使用中文名称。请严格参考您在主问题上下文已获得的命名规范。

当前问题：{question}
正确答案：{correct_option}

请严格按照上述核心要求，并结合以下针对该问题类型的具体指导，为上述问题生成三个干扰选项。直接返回三个干扰选项，每行一个，不要添加任何编号或额外文字：
-----
""",
        "DISTRACTOR_GUIDANCE": {
            "object_describe_solder": "类型特定指导 (物体描述 - 焊点特写)：正确答案描述为 '焊点特写' 或 'PCB板上的焊点区域'。\n干扰选项应是其他常见的、与焊点有明显区别的**元件类型或PCB局部特征**。\n例如：'集成电路'、'电容'、'电阻'、'连接器'、'导线走线'、'散热片'、'电感线圈'。\n严禁出现与 '焊点' 意思相同或高度相似的词语，如 '锡球'、'焊接点'、'连接点'。",
            "object_describe_pcb": "类型特定指导 (物体描述 - PCB板/特定对象)：干扰选项应是其他常见但与正确答案描述的**主体对象或其主要特征不同类别**的工业零件、电子组件或错误描述。\n例如：如果正确答案是'一张显示PCB板的整体图像'，干扰项可以是'一个金属零件'、'一张显示芯片的特写'、'一个塑料外壳'。\n如果正确答案是'一张显示电阻元件的特写图像'，干扰项可以是'一张显示电容元件的特写图像'、'一张显示焊点的特写图像'。\n严禁出现与正确答案主体对象意思相同或高度相似的词语，如 '电路板'、'主板'（如果正确答案是PCB板），或 '焊接点'（如果正确答案是焊点）。",
            "object_describe_default": "类型特定指导 (物体描述 - 特定对象)：干扰选项应描述图中物体可能存在的、但与正确答案不同的其他类型物体、整体布局、组件特征或结构。\n例如，如果正确答案是'一个电阻元件'，干扰项可以是'一个电容元件'、'一个二极管'、'一个电感线圈'等，但要避免模糊的描述。\n确保干扰选项在内容上与正确答案有明显区别，避免同义词或指代同一事物的不同表述。",
            "defect_classification": "类型特定指导 (缺陷分类)：干扰选项必须是其他合理的、与正确答案有明显区别的中文缺陷名称。例如，如果正确答案是'短路'，干扰项可以是'开路'、'缺焊'、'划痕'。\n如果正确答案是句子格式（如 '短路'），干扰选项也必须遵循此格式，仅替换缺陷名称部分。",
            "defect_count": "类型特定指导 (缺陷计数)：干扰选项必须与正确答案的文本结构和格式完全一致，但仅修改数字。\n选择与正确答案中的数字显著不同但仍合理的数值（例如，正确答案是3个，干扰项可以是2个或5个）。确保总数和细分数量在逻辑上可以对应。\n保持所有非数字部分的文本完全不变。",
            "defect_location": "类型特定指导 (缺陷定位 - 方位词)：干扰选项必须与正确答案的句子结构、详细程度和语言风格完全一致，但仅改变方位描述（例如，将“左上区域”改为“右下区域”、“中心区域”等）。\n如果正确答案提及了特定的缺陷类型，干扰选项中也必须提及相同的缺陷类型，只改变位置。严禁在干扰选项中使用坐标。\n确保干扰选项的方位描述与正确答案有明显的区别。\n如果正确答案结合了图中元件或特征来描述位置，干扰项也应模仿这种方式，但改变相对位置或参考元件。",
            "defect_detail_describe": "类型特定指导 (缺陷细节描述)：干扰选项应针对相同缺陷类型提供不同但听起来合理但错误的细节描述、原因或特征。\n例如，如果正确答案描述'划痕呈直线状，贯穿走线'，干扰项可以是'划痕呈弧状，仅存在于阻焊层'。\n使用相似的专业术语，但确保核心信息是错误的。避免在干扰选项中引入准确的位置信息，除非正确答案也有且格式一致。\n确保干扰选项的描述与正确答案有明显的区别，不要是同义词或过于相似的表述。",
            "defect_analysis": "类型特定指导 (缺陷分析)：干扰选项必须与正确答案的整体分析框架和结构保持一致。\n在分析的各个部分，提供与正确答案不同但听起来专业且合理的内容。例如，改变评估结论（良好/差）、提出不同的原因或给出不相关的修复建议。\n确保干扰选项的长度、详细程度和使用的专业术语与正确答案高度相似。核心结论必须是错误的。\n确保干扰选项的分析内容与正确答案有明显的区分度，不要是同义词或过于相似的表述。",
            "component_count": "类型特定指导 (元件计数)：干扰选项必须与正确答案的文本结构和格式完全一致，但仅修改数字。\n选择与正确答案中的数字显著不同但仍合理的数值（例如，正确答案是5个，干扰项可以是3个或8个）。确保总数和细分数量在逻辑上可以对应。\n保持所有非数字部分的文本完全不变。",
            "component_type": "类型特定指导 (元件类型)：干扰选项必须是其他合理的、与正确答案有明显区别的中文元件类型名称。例如，如果正确答案是'电阻'，干扰项可以是'电容'、'电感'、'二极管'。\n如果正确答案是句子格式，干扰选项也必须遵循此格式，仅替换元件类型名称部分。",
            "component_location": "类型特定指导 (元件定位 - 方位词)：干扰选项必须与正确答案的句子结构、详细程度和语言风格完全一致，但仅改变方位描述。\n如果正确答案提及了特定的元件类型，干扰选项中也必须提及相同的元件类型，只改变位置。严禁在干扰选项中使用坐标。\n确保干扰选项的方位描述与正确答案有明显的区别。",
            "component_describe": "类型特定指导 (元件描述 - 外观特征)：干扰选项应针对相同元件类型提供不同但听起来合理但错误的特征描述。\n例如，如果正确答案描述'方形，黑色，表面有丝印'，干扰项可以是'圆形，蓝色，无丝印'，或者改变引脚数量、封装类型等。\n使用相似的专业术语，但确保核心信息是错误的。避免在干扰选项中引入准确的位置信息，除非正确答案也有且格式一致。\n确保干扰选项的描述与正确答案有明显的区别，不要是同义词或过于相似的表述。",
            "component_analysis": "类型特定指导 (元件分析/功能)：\n- 干扰选项必须与正确答案的整体分析框架、句子结构、详细程度和专业术语保持高度一致。\n- **核心原则**：干扰选项提供的内容必须是错误的、误导性的，但听起来专业且合理，以有效混淆答案。\n- **若正确答案涉及阻值或容差（例如，电阻功能）**：\n  - 干扰选项必须在结构和格式上与正确答案完全一致，但要改变功能描述和/或阻值/容差数字。\n  - 确保改变后的功能和数值是错误的但听起来合理，并且与正确答案的数值有**显著差异**（例如，数量级或百分比差异，如200Ω和20kΩ，或完全错误的单位）。\n  - 如果正确答案包含单位（如Ω, kΩ, MΩ），干扰选项也必须包含，并与改变后的数值匹配。\n- **对于其他元件分析或不含阻值/容差的元件功能描述**：\n  - 在分析的各个部分，提供与正确答案不同但听起来专业且合理的内容。例如，改变评估结论（合格/不合格）、提出不同的功能分析（如'用于信号放大'而非'用于限流'）或给出不相关的建议。\n  - 确保干扰选项的分析内容与正确答案有明显的区分度，避免同义词或过于相似的表述。\n- 最终，确保干扰选项的核心结论或关键事实是错误的。",
            "default": "通用指导：请确保干扰选项与问题和正确答案紧密相关，但信息是错误的。避免同义词，确保选项有明显区分度。",
            "location_structured": """
            你的目标是创建 3 个高质量、合理但不正确的干扰项。
            使用以下策略创建错误选项。你可以将它们组合起来。
            1. **交换位置**：如果答案是“缺陷 A 位于左上角；缺陷 B 位于右下角”，则一个好的干扰项是“缺陷 A 位于右下角；缺陷 B 位于左上角”。
            2. **相邻移动**：如果答案提到“左上角”，则一个好的干扰项会使用附近的位置，例如“中上角”或“左中角”。
            3. **更改计数**：如果答案是“左上角 (2)”，则一个好的干扰项是“左上角 (1)”或“左上角 (3)”。
            4. **错误归因缺陷类型**：如果答案是“开路：左上角；短路：中心”，一个好的干扰项是“短路：左上角；开路：中心”。
            5. **虚构/幻觉**：添加原始答案中不存在的位置或缺陷类型。例如，添加“，底部中心(1)”。
            请勿创建逻辑上不可能的选项（例如，总数与零件之和不匹配）。
            仅提供 3 个干扰项，每个另起一行。不要给它们编号。
            """,
        
        },
        "map_instruction_format": "所有的缺陷或元件名称在您的回答中必须使用中文名称。请严格参考如下对照表进行命名和描述: {map_json}",
        "object_type_names": {"defect": "缺陷", "component": "元件", "object": "物体"},
        "location_map": {
            "top": "上方", "middle": "中部", "bottom": "下方",
            "left": "左侧", "center": "中间", "right": "右侧",
            "top-left": "左上", "top-center": "中上", "top-right": "右上",
            "middle-left": "左中", "middle-center": "中心区域", "middle-right": "右中",
            "bottom-left": "左下", "bottom-center": "中下", "bottom-right": "右下"
        },
        "no_var": [  "否",
                    "否，没有发现",
                    "否，未检测到",
                    "没有",
                    "未发现缺陷",
                    "图像中未发现异常",
                    "无明显缺陷",
                    "图中无缺陷存在",
                    "未观察到缺陷",
                    "检测结果为正常"],
        "has_var": [  "是",
                    "是，发现缺陷",
                    "是，检测到缺陷",
                    "发现缺陷",
                    "存在缺陷",
                    "检测出异常区域",
                    "图中存在明显缺陷",
                    "观察到缺陷",
                    "图像中检测到异常",
                    "检测结果为异常"],
        "llm_intro_prompts": [
            "作为工业缺陷检测专家，请分析以下图像及提供的辅助信息。",
            "你是工业缺陷检测大师，请利用以下多模态信息，创建高质量的VQA数据。",
            "请以工业产品质量控制工程师身份，基于上传的图像和文本信息，生成教学型视觉问答对。",
            "作为工业制造质量专家，请分析以下图像及其辅助信息，创建全面的视觉问答数据。",
            "你是工业缺陷分析师，请利用提供的图像和文本信息，生成深度技术分析型VQA数据。"
        ],
        "no_defect_llm_intro_prompts": [
            "作为一名电子制造与检测专家，请分析以下PCB图像及其提供的元件信息。",
            "你是一名资深电子工程专家，请利用提供的PCB图像和元件描述，构建用于无缺陷PCB图像的高质量视觉问答数据。",
            "请以电子制造工艺培训师身份，基于上传的PCB图像及元件信息，生成教学型视觉问答对。",
            "作为工业电子质量专家，请分析提供的PCB图像和元件信息，创建系统性的视觉问答对。",
            "你是一名PCB视觉认知系统专家，请基于提供的图像和文本信息，生成面向无缺陷PCB板的技术性视觉问答对。"
        ],
        # --- MODIFICATION: Added and modified dynamic texts for diversity ---
        "dynamic_questions": {
            "compare_prefix": "对比正常图像和异常图像，",
            "no_defects_detected": "图中未检测到任何{obj_type}。",
            "defects_detected": "图中检测到有{obj_type}存在。",
            "no_objects_for_coords": "图中没有标注可供提供坐标的{obj_type}。",
            "defect_types_hint_multi": "这些{obj_type}包括多种类型，如{types}。",
            "defect_types_hint_single": "主要类型是{type}。",
            "component_type_hint": "主要类型是{type}元件。",
            "coordinate_question_format": "要求以json的格式返回结果。",
            "coordinate_question_compare": "{intro}{hints}请提供这些缺陷的bbox坐标，{format}",
            "coordinate_question_standard": "{intro}{hints}请提供图中所有这些{obj_type}的bbox坐标，{format}",
            "count_question_multi_defect": "图中总共有多少个缺陷？各类缺陷分别有多少？",
            "count_question_component": "图中总共有多少个{type}{obj_type}？",
            "count_question_default": "图中总共有多少个{obj_type}？",
            "location_question_intro": "请简述图中{obj_type}的位置。",
            "detection_question_compare": "图中是否检测到任何缺陷？",
            "detection_question_standard": "图中是否检测到任何缺陷？",
            "describe_image_question": "请描述这张图像",
            "question_templates": {
                "analysis": [
                    "对{prefix}，{predicate}", "请分析{prefix}{predicate}",
                    "能否评估一下{prefix}，并{predicate}", "关于{prefix}，请{predicate}"
                ],
                "describe": [
                    "请描述{prefix}{predicate}", "{prefix}的外观如何？",
                    "能否详细说明{prefix}{predicate}", "谈谈{prefix}的视觉特征。"
                ],
                "default": [
                    "请问{prefix}{predicate}", "关于{prefix}，其{predicate}",
                    "图中{prefix}的{predicate}"
                ]
            },
            "object_prefix_bbox": "标注的目标",
            "object_prefix_default": "图中的{obj_type}"
        }
    },
    'en': {
        # --- MODIFICATION FOR P3: Added localized QA format example ---
        "QA_FORMAT_EXAMPLE": """
{
    "object describe": {
        "question": "<complete natural question>",
        "correct_option": "<answer based on image and annotation facts>"
    },
    "defect detection": {
        "question": "<complete natural question>",
        "correct_option": "Yes, defects were detected."
    },
    "defect classification": {
        "question": "<complete natural question>",
        "correct_option": "<class name>"
    },
    "defect count": {
        "question": "How many defects are there in total, and what are the counts for each type?",
        "correct_option": "<answer based on image and annotation facts>"
    },
    "defect location": {
        "question": "Regarding these defects, in which areas of the image do they primarily appear?",
        "correct_option": "The defects are mainly distributed in the central and bottom-right areas of the image. The defect in the central area appears as a break in a trace, while the one in the bottom-right is a noticeable pit on a solder pad. The presence of defects in these locations suggests potential issues with stress concentration or corrosion."
    },
    "defect detail describe": {
        "question": "<complete natural question>",
        "correct_option": "<answer based on image and annotation facts>"
    },
    "defect coordinates": {
        "question": "Find the open circuit in the image",
        "correct_option": "{[[0,0,0,0]]}"
    },
    "defect analysis": {
        "question": "<complete natural question>",
        "correct_option": "<class name>"
    },
    "component count": {
        "question": "How many components are there in total, and what are the counts for each type?",
        "correct_option": "Total 8 components, including: Resistor 5, Capacitor 3."
    },
    "component type": {
        "question": "<complete natural question>",
        "correct_option": "<answer based on image and annotation facts>"
    },
    "component location": {
        "question": "How are these components laid out on the circuit board?",
        "correct_option": "The components are primarily concentrated in the top-left corner of the board, forming a dense array. This layout typically indicates that they constitute a complete functional unit, such as a power management module or a signal processing unit."
    },
    "component describe": {
        "question": "<complete natural question>",
        "correct_option": "<answer based on image and annotation facts>"
    },
    "component coordinates": {
        "question": "Find the resistor in the image",
        "correct_option": "{[[0,0,0,0],[0,0,0,0],[0,0,0,0]]}"
    },
    "component analysis": {
        "question": "<complete natural question>",
        "correct_option": "<answer based on image and annotation facts>"
    }
}
""",
        # --- MODIFICATION FOR P3: Added localized question type names ---
        "QUESTION_TYPES": {
            "object describe": "object describe",
            "defect detection": "defect detection",
            "defect classification": "defect classification",
            "defect count": "defect count",
            "defect location": "defect location",
            "defect detail describe": "defect detail describe",
            "defect coordinates": "defect coordinates",
            "defect analysis": "defect analysis",
            "component count": "component count",
            "component type": "component type",
            "component location": "component location",
            "component describe": "component describe",
            "component coordinates": "component coordinates",
            "component analysis": "component analysis",
        },
        "LLM_PROMPT_HEADER": """
**[TOP DIRECTIVE: LANGUAGE UNIFORMITY]**
**All of your output for this task, including the question and correct_option, must be exclusively in [English]. It is strictly forbidden to use any Chinese characters or words in any part of any field (except for punctuation required by the JSON format). This is an absolute rule that must be followed.**

{random_prompt_intro}

[Task Focus]
{task_focus}

[Dataset Information]
- Description: {dataset_description}
- Image Size: Original {original_width}x{original_height}, Resized {resized_width}x{resized_height}

{additional_context}

[Task Instructions]
I have provided images and their related auxiliary information. Please carefully analyze this information first, then generate questions and their corresponding correct answers (do not generate options) for the following question types:

{questions_list_prompt}

[JSON Format Requirement]
Please strictly generate high-quality JSON according to the following format. Only generate the `question` and `correct_option` fields. Ensure all keys and values are enclosed in double quotes:
{qa_format_example}

[Strict Output Requirements]
- Output exactly one JSON object. Do not output Markdown code fences, explanations, prefixes, suffixes, or extra text.
- Include every requested question type listed above. Do not omit any requested type and do not add unrequested types.
- Each question type must contain non-empty `question` and `correct_option` fields.
- If [Structured Annotation Facts] provide classes, counts, or coordinates, you must follow them exactly. Do not alter, add, remove, or guess facts.

[Precautions]
1.  **REITERATING THE TOP DIRECTIVE: All generated content, including questions and answers, must be 100% in English.**
2.  Create diverse content while ensuring questions are clear, professional, and relevant to the actual content of the image (including provided auxiliary information).
3.  Ensure all answers are consistent with the actual content in the image, using professional terminology and accurate descriptions.
4.  Describe features and locations in detail to ensure answers are accurate, professional, and comprehensive.
5.  All responses must be enclosed in double quotes to ensure the generated JSON format is completely correct.
6.  {map_instruction}
7.  All answers must be relevant to the current question; do not introduce answers from other questions.
{specific_rules}
""",
        "COMPARE_PROMPT_HEADER": """
**[TOP DIRECTIVE: LANGUAGE UNIFORMITY]**
**All of your output for this task, including the question and correct_option, must be exclusively in [English]. It is strictly forbidden to use any Chinese characters or words in any part of any field (except for punctuation required by the JSON format). This is an absolute rule that must be followed.**

As an Industrial Defect Quality Inspector, please use the provided multiple comparative images (normal sample, defective sample, bbox annotation image, class annotation image) and defect text information to generate in-depth, technical analysis-style VQA data. Questions should cover defect feature recognition, classification criteria, root causes, and impacts on product functionality and reliability. Answers must provide systematic and professional defect knowledge, combining image features and text annotations.

[Dataset Information]
- Description: {dataset_description}
- Image Size: Original {original_width}x{original_height}, Resized {resized_width}x{resized_height}
- The dataset includes two comparative images: one normal sample (OK image, no defects found) and one defective sample (NG image, defects present). Please compare and analyze the differences between the two images.

[Defect Information]
{defect_info_str}

[Defect Location Description Guide]
{location_prompt}

[Task Instructions]
I have provided four different forms of the same image (a defect-free image, a bounding box annotated image with classifications, a bounding box annotated image without classifications, and an unannotated defective image). Please first carefully analyze the defects in the images, then generate questions and their corresponding correct answers (do not generate options) for the following question types:

{questions_list_prompt}

[**Crucial Guidance - Comparative Analysis**]
Please pay special attention: for the following questions, your answer must be based on a **strict comparative analysis** of the **OK (normal sample) image** and the **NG (defective sample) image**. Identify the presence, type, location, and coordinates of defects by recognizing the differences in the NG image compared to the OK image.

-   **Fixed image role:** Use the abnormal/NG image indicated by the structured annotation facts as the defect-answer target. The OK image is only a comparison reference. It is strictly forbidden to treat normal structures in the OK image as defect answers.
-   **For 'defect detection' questions:** Compare the OK and NG images and clearly state whether any anomalous regions inconsistent with the OK image are found in the NG image.
-   **For 'defect coordinates' questions:** Compare the OK and NG images, find all areas that do not conform to the normal sample (i.e., defects), and provide the **precise bounding box coordinates** for these defects. Ensure your coordinates are based on the actual defect locations identified in the NG image.
-   **For 'defect classification' and 'defect detail describe' questions:** Your answers should be based on the type and appearance characteristics of the defects identified after comparison.

[JSON Format Requirement]
Please strictly generate high-quality JSON according to the following format. Only generate the `question` and `correct_option` fields. Ensure all keys and values are enclosed in double quotes:
{qa_format_example}

[Strict Output Requirements]
- Output exactly one JSON object. Do not output Markdown code fences, explanations, prefixes, suffixes, or extra text.
- Include every requested question type listed above. Do not omit any requested type and do not add unrequested types.
- Each question type must contain non-empty `question` and `correct_option` fields.
- If [Structured Annotation Facts] provide classes, counts, or coordinates, you must follow them exactly. Do not alter, add, remove, or guess facts.

[Precautions]
1.  **REITERATING THE TOP DIRECTIVE: All generated content, including questions and answers, must be 100% in English.**
2.  Create diverse content while ensuring questions are clear, professional, and relevant to the actual content of the image (including provided auxiliary information).
3.  Ensure all answers are consistent with the actual content in the image, using professional terminology and accurate descriptions.
4.  Describe features and locations in detail to ensure answers are accurate, professional, and comprehensive.
5.  All responses must be enclosed in double quotes to ensure the generated JSON format is completely correct.
6.  {map_instruction}
7.  All answers must be relevant to the current question; do not introduce answers from other questions.
{specific_rules}
""",
        "LOCATION_PROMPT": """
Please use precise directional words to describe the defect location, following these rules:
1.  Divide the image into nine regions: top-left, top-center, top-right, middle-left, center, middle-right, bottom-left, bottom-center, bottom-right.
2.  You must first specify the image region (nine-square grid) where the defect is located, and then describe the defect's position **within that region** or its **relative position to surrounding components, traces, or features**.
3.  Reference points that can be used: PCB edge, large components, fiducial marks, pad areas, distinct traces.
4.  Describe distance relationships accurately, e.g., "about 2cm from the left edge," "immediately adjacent to the large IC in the top-right."
5.  Use clock-face directions to assist description, e.g., "at the 3 o'clock position," "from the center towards the 7 o'clock direction."
6.  Avoid vague expressions like "somewhere," "a place"; you must provide a clear spatial position.
7.  For multiple defects of the same type, describe each one distinctly, e.g., "There are two shorts in the top-left region; one is near the edge, the other is on a central trace."
8.  **When describing defect locations, prioritize mentioning the defect's relative position to other components, pads, or traces on the PCB. For example: at the pin of resistor R12, near the pad of chip U3, between two parallel traces.**

Incorrect Examples:
- "There is a short on the object's surface" (Missing location information)
- "There is a defect on the upper part of the board" (Too general)

Correct Examples:
- "In the bottom-right region, a short exists between two parallel traces about 1.5cm from the bottom edge."
- "In the middle-left region, a spur is found on a thin trace about 5mm to the left of the large IC."
- "In the center region, a solder bridge is located near the collector pad of transistor Q1."

Please use professional, precise, and natural language to describe the defect location. Avoid using coordinates or formulas. The description should allow inspection personnel to quickly and intuitively locate the defect.
""",
        "COMPONENT_LOCATION_PROMPT": """
Please use precise directional words to describe the distribution and location of components in the PCB image, following these rules:
1.  Divide the image into nine regions: top-left, top-center, top-right, middle-left, center, middle-right, bottom-left, bottom-center, bottom-right.
2.  You must first specify the image region (nine-square grid) where the components are located, and then describe their position **within that region** or their **relative position to other components, connectors, traces, or features**. For example: "Multiple capacitors are distributed near the edge of the top-left region of the image."
3.  Reference points include: PCB edge, large ICs, connectors, distinct traces, pad arrays, etc.
4.  It is recommended to describe distance relationships, e.g., "A row of chip resistors is located about 2cm from the right edge," "Multiple SOT23 package transistors are distributed immediately to the right of the large IC in the center region."
5.  Clock-face directions can be used for assistance, e.g., "distributed at the 3 o'clock position," "multiple similar components are arranged along a trace extending from the center region towards the 7 o'clock direction."
6.  Avoid vague descriptions like "there are resistors somewhere"; specify the region and relative relationship.
7.  If there are multiple components of the same type, they should be described distinctly, e.g., "There are two groups of electrolytic capacitors in the middle-left region; one group is arranged along the edge of a trace, the other is near the left-side connector."
8.  **When describing component locations, consider both the component's region within the overall image and its relative position to other key components, traces, or features on the PCB. For example: next to the processor chip U1, near the pad area of the USB interface, arranged along the power trace.**

Incorrect Examples:
- "There are a few components in the middle of the board" (Vague location, region not specified)
- "There is a capacitor at the top" (No specific region or reference object indicated)

Correct Examples:
- "In the top-right region, three chip resistors are arranged along a horizontal trace about 1cm from the right edge."
- "Eight SOT23 package transistors are arranged around the large IC in the bottom-left region."
- "Four diodes are distributed in the right part of the center region, near a pad array."

Please use professional, natural, and clearly positioning language to describe component locations. Avoid using pixel coordinates or formulas. The description should help the reader to quickly and intuitively understand the spatial distribution of the components.
""",
        "ANALYSIS_AND_DESCRIBE_RULES_PROMPT": """---
**[Guidance for Generating the Answer Field (correct_option)]**

1.  **For Analysis-type Questions (`defect analysis`, `component analysis`):**
    * Do not randomly omit key content. The answer must include: quality/phenomenon assessment, plausible root causes, functional or reliability impact, and inspection or repair suggestions.
    * If [Structured Annotation Facts] show multiple defect classes, first provide an overall risk assessment, then cover the impact or risk of every class. Do not analyze only one class or only the most salient class.
    * If this is a component analysis question, focus on the circuit role, layout rationality, and possible function of the labeled components. Do not describe defect-free components as defects.
    * Root-cause analysis must match the defect type. PCB fabrication defects such as open circuits, shorts, mouse bites, spurious copper, and missing holes should be analyzed primarily from etching, exposure, development, drilling, copper residue, contamination, or mechanical damage. PCBA soldering defects such as lack of solder, solder bridge, excessive solder, and solder balls should be analyzed primarily from solder paste printing, placement offset, reflow profile, and pad contamination. Assembly defects such as missing screws, loose screws, missing components, and loose wiring should be analyzed from assembly omission, poor fastening, wiring installation, and workstation inspection.
    * Separate observable facts from plausible inference. Observable facts must come from the image or structured annotations; process causes and functional impacts must be phrased cautiously with words such as "may", "could", or "typically".
    * Do not invent CPUs, fans, heat sinks, connectors, chip IDs, or specific circuit modules unless they are clearly visible. Do not describe SMD components as color-band or through-hole leaded components unless such features are clearly visible.
    * Ensure the answer has a clear structure, rigorous logic, and accurate use of professional terminology.
    * **Important: In your response, please avoid using any numerical or list markers (e.g., '1.', '2.', '-'). Use natural paragraphs and transition words (e.g., "Furthermore," "In addition," "Regarding this issue") to organize your analysis, presenting it as a coherent professional report.**

2.  **For Description-type Questions (`defect detail describe`, `component describe`):**
    * **For `defect detail describe`:**
        * Focus on the defect's **visual characteristics**, such as shape, size, color, texture, edge features, etc.
        * If [Structured Annotation Facts] show multiple defect classes, describe the visual features of every defect class. At least one clear sentence must be provided for each class.
    * **For `component describe` (Appearance):**
        * Describe the component's **main appearance features**, such as shape, approximate size, color, material, surface texture, silkscreen text or logos, pin count, package type, etc.
        * If multiple component classes exist, cover every labeled class, not just one.
    * **Important: In your response, avoid using any numerical or list markers. Organize your description using natural paragraphs.**

3.  **For Location Description Questions (`defect location`, `component location`):**
    * **Question (`question`)**: Please generate a natural, human-like question about the spatial distribution of the objects. For example: "How are these components laid out on the board?" or "In which areas are the defects mostly concentrated?"
    * **Answer (`correct_option`)**: Please generate a descriptive paragraph as the answer. This paragraph should first **summarize** the main distribution areas of the objects (e.g., using phrases like "mainly distributed in...", "concentrated in..."). Then, you can provide more detail by **giving examples** of features at one or two specific locations. You may also briefly **analyze** what this layout might imply (e.g., "This dense arrangement might indicate a functional module"). Please use the principles from the [Defect/Component Location Description Guide] to structure your thoughts, but the final output must be a **fluent, natural language paragraph**, not a structured list. **Strictly prohibit outputting a direct list of locations or coordinates.**

4.  **[IMPORTANT] For Classification/Type Questions (`defect classification`, `component type`):**
    * For these question types, the `correct_option` field must contain only category names. Do not add explanations, definitions, or descriptive sentences.
    * If there is only one class, output only that class name, such as "Insufficient Solder" or "Resistor".
    * If there are multiple classes, output every class and separate them with commas, such as "solder bridge, insufficient solder". It is strictly forbidden to output only the main class, the most salient class, or any single subset of classes.
---    
**[Guidance for Generating the Question Field (question) - Core Rule]**

Generate a complete, natural question sentence in the `question` field. The downstream program will not add subjects or prefixes to your question, so do not return fragments such as "s detailed features?" or "analyze its root cause and provide suggestions."

**Question-writing requirements:**
* The question must clearly refer to the current image, the labeled region, or the abnormal region in the comparison image. Avoid unclear pronouns such as "it" or "this" when the target is ambiguous.
* The question should sound like something a quality inspection engineer or dataset annotator would ask, not like a template placeholder.
* Use varied wording for different question types in the same image, while keeping the wording precise.
* Do not leak answer facts such as exact counts, coordinates, or all class names in the question unless the task naturally requires naming the target class.
* For `object describe`, the question may be fixed or close to "Please describe this image."
* For classification/type questions, use a complete question, such as "What type of defect is shown in the labeled region?" or "What component type is marked by the bounding box?"

**Question-writing dimensions:**
* Description questions should ask about observable visual evidence, such as shape, color, edge condition, missing material, residue, connection state, or package features.
* Analysis questions should ask about impact, plausible causes, and inspection suggestions without using fixed boilerplate wording.
* Classification/type questions should clearly ask for the category without revealing the answer.
* Comparison-sample questions should make clear that the abnormal image is the answer target and the normal image is only a reference.
* Do not copy any sentence from this prompt verbatim as the `question`.

**Bad question examples:**
* "s detailed features?" (fragment)
* "Please analyze the defect analyze its root cause and provide suggestions." (duplicated wording)
* "What is the type of labeled target" (incomplete)
* "What is this issue?" (ambiguous)
---
""",
        # --- MODIFICATION FOR P4: Improved prompt for object describe ---
        "P3_OBJECT_DESCRIBE_PROMPT": """
[P3 'object describe' Exclusive Guidance]
For the 'object describe' type, your answer (`correct_option`) should be a single, concise, and natural sentence summarizing the core content of the image. Please avoid using fixed templates and try to diversify the descriptions.
Your `question` field should be fixed to `"Describe this image"`.

Here are some **varied examples of answers** for your reference; please adopt their style, not copy them verbatim:
- **If the image is a PCB overview:**
  - 'This is an overview image of a printed circuit board.'
  - 'The image shows a complete PCB.'
  - 'An image of a printed circuit board.'
- **If the image is a close-up of a specific component:**
  - 'This picture focuses on a resistor component.'
  - 'The image is a close-up of a capacitor.'
  - 'A close-up image showing a SOT23-packaged transistor.'
- **If the image shows a specific defect:**
  - 'This image shows a short circuit defect.'
  - 'The content of the image is a close-up of an open circuit defect.'
  - 'An image focusing on a spur defect.'

**Core requirement:** The answer should be refined, accurate, and reflect the main subject of the image.
""",
        "P1_COMPONENT_ANALYSIS_PROMPT": """
[P1 Component Analysis Question Exclusive Guidance]
When generating the `question` field for the 'component analysis' type, write a complete question and focus on the component's **core function, its role in the circuit, or its primary application**.
For example, you could generate: `"What function might the labeled component serve in this circuit?"` or `"Please analyze the likely role of this component in the current PCB design."`
""",
        "RESISTOR_HINT_PROMPT": """
"Hint: The silkscreen on the resistor is '{silkscreen_code}', and its calculated resistance value is {resistor_value_hint}. Please use this information in your description and analysis."
- **Component Function (component analysis) Question**: Ensure the answer clearly states the resistor's **main function is current limiting, voltage division, etc.**, and **must include its precise calculated resistance value '{resistor_value_hint}'**. Do not mention tolerance.
- **Component Description (component describe) Question**: When describing the resistor's appearance, based on the image, **must mention its calculated resistance value '{resistor_value_hint}'**, along with features like its color bands, size, package type, etc. Do not mention tolerance.
- Please ensure your answer is strictly based on the provided silkscreen value and calculated resistance, and avoid speculation or providing inconsistent information.
""",
        "SOLDER_JOINT_HINT_PROMPT": "Please ensure that both the questions and answers clearly point to the basic function and role of the solder joints in the image, avoiding the introduction of other component types.",
        "P2_COMPONENT_BBOX_PROMPT": """---
**[P2 Type Exclusive Mandatory Instruction: Strictly Focus on the Bounding Box]**
**CRUCIAL:** The primary image provided is one that **only contains bounding boxes**. These boxes highlight all the target objects you need to focus on and analyze.
**Your task must strictly adhere to the following rules:**
1.  **Analysis Object Limited to Inside the Box**: All your generated answers for **analysis (`component analysis`)**, **description (`component describe`)**, and **type judgment (`component type`)** **must and can only** pertain to the objects **inside the bounding boxes** in the image.
2.  **Ignore Everything Outside the Box**: **Absolutely prohibit** describing, analyzing, or mentioning any background, traces, or other unselected features outside the bounding boxes. Your scope must be confined to these boxes.
3.  **Based on Appearance and Layout**: Since no class labels are provided, all your answers must be based on the **visual appearance** of the objects within the boxes (shape, size, color, pin features, etc.) and their **spatial layout** (arrangement, density, relative positions).
4.  **Cover All Bounding Boxes**: If multiple boxes are present, the answer must cover all of them collectively. If structured facts contain multiple component classes, type, description, and analysis answers must cover every class.
5.  **Do Not Treat Box Lines as Objects**: The bounding box is only a region cue, not the component itself. Do not describe irrelevant facts such as "the box is large" or "the boxes are obvious".
6.  **Prohibit Guessing Specific Identity**: When answering `component type` or `component analysis`, you can make a generic classification based on appearance (e.g., "This looks like a chip resistor or capacitor"), but you are **strictly forbidden** to guess its specific model, specification, or precise function. The answer should focus on its likely generic role (e.g., "likely used for filtering").
7.  **Answer Example (`component describe`)**: "The objects boxed in the image are rectangular, black, with metal pins on both sides, small in size, and closely arranged." (Correct, only describes the appearance of objects inside the box)
8.  **Answer Example (`component analysis`)**: "The multiple small components boxed in the image are densely arranged, possibly forming a signal processing or power filtering module. Their layout is neat, indicating good mounting technology." (Correct, based on layout and generic functional analysis)
**Any deviation from the bounding box will be considered an error. Treat the bounding box as your only scope of analysis.**
---
""",
        "P2_DEFECT_BBOX_PROMPT": """---
**[P2 Type Exclusive Mandatory Instruction: Strictly Focus on the Bounding Box]**
**CRUCIAL:** The primary image provided is one that **only contains bounding boxes**. These boxes highlight all the **defective areas** you need to focus on and analyze.
**Your task must strictly adhere to the following rules:**
1.  **Analysis Object Limited to Inside the Box**: All your generated answers for **analysis (`defect analysis`)**, **description (`defect detail describe`)**, and **classification (`defect classification`)** **must and can only** pertain to the anomalous features **inside the bounding boxes** in the image.
2.  **Ignore Everything Outside the Box**: **Absolutely prohibit** describing, analyzing, or mentioning any normal areas, background, or other unselected features outside the bounding boxes. Your scope must be confined to these boxes.
3.  **Based on Anomalous Appearance**: All your answers must be based on the **anomalous visual features** displayed within the boxed area (e.g., abnormal color, irregular shape, cracks, foreign material, etc.).
4.  **Cover All Bounding Boxes**: If multiple boxes are present, the answer must cover all of them collectively. If structured facts contain multiple defect classes, classification, description, and analysis answers must cover every class.
5.  **Do Not Treat Box Lines as Defects**: The bounding box is only a region cue, not the defect itself. Do not describe irrelevant facts such as "the box is large" or "the boxes are dense".
6.  **Answer Example (`defect detail describe`)**: "The area boxed in the image shows an irregular dark scratch that runs across several copper traces." (Correct, only describes the anomaly inside the box)
7.  **Answer Example (`defect analysis`)**: "The short-circuit defect within the box could lead to the failure of the related circuit function and potentially damage upstream components. This is often caused by mask issues during the etching process or out-of-spec chemicals." (Correct, analyzes the defect inside the box)
**Any deviation from the bounding box will be considered an error. Treat the bounding box as your only scope of analysis.**
---
""",
        "LABELED_OBJECT_PROMPT": """--- CRITICAL: Mandatory Guidance for Analysis & Description Questions on [Provided Objects] ---
Given that this image has been provided with clear {object_type_name} information in the text (see the 'Identified {object_type_name} Information' section for details), when answering questions such as '{object_type_name} analysis', '{object_type_name} description', '{object_type_name} classification', etc., your answers **must and can only** be based on the {object_type_name}s from this **provided information**.
**Strictly prohibit** discussing any features **not mentioned in the information**.
**More importantly: Strictly prohibit** generating any content indicating that the **object does not exist or cannot be analyzed/described**, such as 'no {object_type_name} found', 'cannot analyze', 'no {object_type_name} detected in the image', 'no {object_type_name} information', as we already know {object_type_name}s are present in the image.
Your answer should always be a detailed, professional analysis or description of the **existing** {object_type_name}s.
--- End of Critical Guidance ---
""",
        "COMPONENT_SUBTYPE_HINT_PROMPT": """
[Detailed Guide to Component Subtypes and Their Appearance Features]
{component_describe_info}
When answering component-related questions (especially 'component describe', 'component type', 'component analysis'), please prioritize using the more specific and professional component subtype names provided in the guide above for your description (e.g., if the image features match the description of a "Thermistor", please use "Thermistor" instead of just "Resistor"). If the image features or provided description are insufficient to determine the specific subtype, then fall back to the generic type (e.g., "Resistor", "Capacitor"). When answering 'component describe', please provide a detailed description of the component's visual features, combining information from the image and the guide above.
""",
        "DISTRACTOR_BASE_PROMPT": """
Core Requirement: Each distractor option you generate must be **consistent in theme and professionalism** with the "Correct Answer" below, but **incorrect or misleading in its key information**.
Please ensure the **sentence structure, linguistic style, and approximate length** of the distractor options are similar to the correct answer to maintain option uniformity.
At the same time, each distractor must be **clearly distinguishable** from the correct answer and other distractors; avoid using synonyms or very similar phrasing.
All defect or component names must be in English. Please strictly refer to the naming conventions you have already received in the main question context.

Current Question: {question}
Correct Answer: {correct_option}

Please strictly follow the core requirement above, and in conjunction with the specific guidance for this question type below, generate three distractor options for the question above. Return only the three distractor options, one per line, without any numbering or additional text:
-----
""",
        "DISTRACTOR_GUIDANCE": {
            "object_describe_solder": "Type-Specific Guidance (Object Description - Solder Joint): The correct answer is described as 'a close-up of a solder joint' or 'solder joint area on a PCB'.\nDistractor options should be other common **component types or PCB local features** that are distinctly different from a solder joint.\nExamples: 'Integrated circuit', 'Capacitor', 'Resistor', 'Connector', 'Trace routing', 'Heat sink', 'Inductor coil'.\nStrictly prohibit words with the same or very similar meaning to 'solder joint', such as 'solder ball', 'weld point', 'connection point'.",
            "object_describe_pcb": "Type-Specific Guidance (Object Description - PCB/Specific Object): Distractor options should be other common industrial parts, electronic components, or incorrect descriptions that are of a **different category from the main object or its primary features** described in the correct answer.\nFor example, if the correct answer is 'An overall image of a PCB', distractors could be 'A metal part', 'A close-up of a chip', 'A plastic casing'.\nIf the correct answer is 'A close-up image showing a resistor component', distractors could be 'A close-up image showing a capacitor component', 'A close-up image showing a solder joint'.\nStrictly prohibit words with the same or very similar meaning to the main object in the correct answer, such as 'circuit board', 'motherboard' (if the correct answer is PCB), or 'weld point' (if the correct answer is solder joint).",
            "object_describe_default": "Type-Specific Guidance (Object Description - Specific Object): Distractor options should describe other types of objects, overall layouts, component features, or structures that might plausibly exist in the image but are different from the correct answer.\nFor example, if the correct answer is 'A resistor component', distractors could be 'A capacitor component', 'A diode', 'An inductor coil', etc., but avoid vague descriptions.\nEnsure the content of the distractors is clearly different from the correct answer, avoiding synonyms or different expressions for the same thing.",
            "defect_classification": "Type-Specific Guidance (Defect Classification): Distractor options must be other plausible, clearly different English defect names. For example, if the correct answer is 'Short', distractors could be 'Open', 'Insufficient Solder', 'Scratch'.\nIf the correct answer is a sentence format (e.g., 'The defect type is Short'), the distractors must follow this format, only replacing the defect name part.",
            "defect_count": "Type-Specific Guidance (Defect Count): Distractor options must exactly match the text structure and format of the correct answer, but only modify the numbers.\nChoose numbers that are significantly different from the correct answer but still plausible (e.g., if the correct answer is 3, distractors could be 2 or 5). Ensure the total count and breakdown counts are logically consistent.\nKeep all non-numerical text exactly the same.",
            "defect_location": "Type-Specific Guidance (Defect Location - Directional): Distractor options must exactly match the sentence structure, level of detail, and linguistic style of the correct answer, but only change the directional description (e.g., change 'top-left area' to 'bottom-right area', 'center area', etc.).\nIf the correct answer mentions a specific defect type, the distractors must also mention the same defect type, only changing the location. Strictly prohibit using coordinates in distractors.\nEnsure the directional descriptions in the distractors are clearly different from the correct answer.\nIf the correct answer describes location relative to components or features, the distractors should mimic this style but change the relative position or reference component.",
            "defect_detail_describe": "Type-Specific Guidance (Defect Detail Description): Distractor options should provide different, plausible-sounding but incorrect details, causes, or features for the same defect type.\nFor example, if the correct answer describes 'The scratch is linear and runs across the trace', a distractor could be 'The scratch is arc-shaped and exists only on the solder mask'.\nUse similar professional terminology, but ensure the core information is wrong. Avoid introducing accurate location information in distractors unless the correct answer also has it in a consistent format.\nEnsure the descriptions in the distractors are clearly different from the correct answer, not just synonyms or slight rephrasing.",
            "defect_analysis": "Type-Specific Guidance (Defect Analysis): Distractor options must be consistent with the overall analysis framework and structure of the correct answer.\nIn each part of the analysis, provide content that is different from the correct answer but sounds professional and plausible. For example, change the assessment conclusion (good/poor), suggest different causes, or provide irrelevant repair advice.\nEnsure the length, level of detail, and professional terminology used in the distractors are highly similar to the correct answer. The core conclusion must be wrong.\nEnsure the analysis content of the distractors is clearly distinguishable from the correct answer.",
            "component_count": "Type-Specific Guidance (Component Count): Distractor options must exactly match the text structure and format of the correct answer, but only modify the numbers.\nChoose numbers that are significantly different from the correct answer but still plausible (e.g., if the correct answer is 5, distractors could be 3 or 8). Ensure the total count and breakdown counts are logically consistent.\nKeep all non-numerical text exactly the same.",
            "component_type": "Type-Specific Guidance (Component Type): Distractor options must be other plausible, clearly different English component type names. For example, if the correct answer is 'Resistor', distractors could be 'Capacitor', 'Inductor', 'Diode'.\nIf the correct answer is in a sentence format, the distractors must follow this format, only replacing the component type name part.",
            "component_location": "Type-Specific Guidance (Component Location - Directional): Distractor options must exactly match the sentence structure, level of detail, and linguistic style of the correct answer, but only change the directional description.\nIf the correct answer mentions a specific component type, the distractors must also mention the same component type, only changing the location. Strictly prohibit using coordinates in distractors.\nEnsure the directional descriptions in the distractors are clearly different from the correct answer.",
            "component_describe": "Type-Specific Guidance (Component Description - Appearance): Distractor options should provide different, plausible-sounding but incorrect feature descriptions for the same component type.\nFor example, if the correct answer describes 'Square, black, with silkscreen on the surface', a distractor could be 'Round, blue, no silkscreen', or change the pin count, package type, etc.\nUse similar professional terminology, but ensure the core information is wrong. Avoid introducing accurate location information in distractors unless the correct answer also has it in a consistent format.\nEnsure the descriptions in the distractors are clearly different from the correct answer.",
            "component_analysis": "Type-Specific Guidance (Component Analysis/Function):\n- Distractor options must be highly consistent with the overall analysis framework, sentence structure, level of detail, and professional terminology of the correct answer.\n- **Core Principle**: The content provided by the distractor options must be incorrect or misleading, but sound professional and plausible to effectively confuse the answer.\n- **If the correct answer involves resistance/tolerance (e.g., resistor function)**:\n  - Distractor options must exactly match the structure and format of the correct answer, but change the functional description and/or the resistance/tolerance numbers.\n  - Ensure the changed function and values are incorrect but plausible, and **significantly different** from the correct answer's values (e.g., order of magnitude or percentage difference, like 200Ω vs. 20kΩ, or a completely wrong unit).\n  - If the correct answer includes units (like Ω, kΩ, MΩ), the distractors must also include them, matching the changed value.\n- **For other component analyses or functional descriptions without resistance/tolerance**:\n  - In each part of the analysis, provide content that is different from the correct answer but sounds professional and plausible. For example, change the assessment conclusion (pass/fail), suggest a different functional analysis (e.g., 'used for signal amplification' instead of 'used for current limiting'), or provide irrelevant advice.\n  - Ensure the analysis content of the distractors is clearly distinguishable from the correct answer.\n- Ultimately, ensure the core conclusion or key fact of the distractor is wrong.",
            "default": "General Guidance: Please ensure the distractor options are closely related to the question and the correct answer, but the information is incorrect. Avoid synonyms and ensure the options are clearly distinguishable.",
            "location_structured": """
        Your goal is to create 3 high-quality, plausible but incorrect distractors.
        Here is the correct answer: "{correct_option}"

        Use the following strategies to create incorrect options. You can combine them.
        1.  **Swap Locations**: If the answer is "Defect A is at top-left; Defect B is at bottom-right", a good distractor is "Defect A is at bottom-right; Defect B is at top-left".
        2.  **Shift Adjacently**: If the answer mentions "top-left", a good distractor would use a nearby location like "top-center" or "middle-left".
        3.  **Alter Counts**: If the answer is "top-left(2)", a good distractor is "top-left(1)" or "top-left(3)".
        4.  **Misattribute Defect Type**: If the answer is "Open_circuit: top-left; Short: center", a good distractor is "Short: top-left; Open_circuit: center".
        5.  **Invent/Hallucinate**: Add a location or a defect type that was not in the original answer. For example, add ", bottom-center(1)".

        Do NOT create options that are logically impossible (e.g., total count doesn't match sum of parts).
        Provide ONLY the 3 distractors, each on a new line. Do not number them.
        """,
                
        },
        "map_instruction_format": "In your answers, you must use the English names for all defects or components. Please strictly refer to the following mapping for naming and descriptions: {map_json}",
        "object_type_names": {"defect": "defect", "component": "component", "object": "object"},
        "location_map": {
            "top": "top", "middle": "middle", "bottom": "bottom",
            "left": "left", "center": "center", "right": "right",
            "top-left": "top-left", "top-center": "top-center", "top-right": "top-right",
            "middle-left": "middle-left", "middle-center": "center area", "middle-right": "middle-right",
            "bottom-left": "bottom-left", "bottom-center": "bottom-center", "bottom-right": "bottom-right"
        },
        "no_var": [  "No",
                    "No, nothing detected",
                    "No, no defect found",
                    "Nothing abnormal",
                    "No visible defects",
                    "The image is normal",
                    "No issues observed",
                    "No defects present",
                    "Defect-free",
                    "Result: Normal"],
        "has_var": [  "Yes",
                    "Yes, defect detected",
                    "Yes, found abnormality",   
                    "Defect observed",
                    "There is a defect",
                    "Anomaly detected",
                    "Defective region present",
                    "Yes, visible defect found",
                    "Abnormal area detected",
                    "Result: Defective"],
        "llm_intro_prompts": [
            "As an industrial defect detection expert, please analyze the following images and provided auxiliary information.",
            "You are an industrial defect detection master. Please use the following multimodal information to create high-quality VQA data.",
            "As an industrial product quality control engineer, please generate instructional visual question-answer pairs based on the uploaded images and text information.",
            "As an industrial manufacturing quality expert, please analyze the following images and their auxiliary information to create comprehensive visual question-answering data.",
            "You are an industrial defect analyst. Please use the provided images and text information to generate in-depth technical analysis-style VQA data."
        ],
        "no_defect_llm_intro_prompts": [
            "As an expert in electronics manufacturing and inspection, please analyze the following PCB image and its provided component information.",
            "You are a senior electronics engineering expert. Please use the provided PCB image and component descriptions to construct high-quality visual question-answering data for defect-free PCB images.",
            "As an electronics manufacturing process trainer, please generate instructional visual question-answer pairs based on the uploaded PCB image and component information.",
            "As an industrial electronics quality expert, please analyze the provided PCB image and component information to create systematic visual question-answer pairs.",
            "You are a PCB visual cognitive system expert. Please generate technical visual question-answer pairs for defect-free PCB boards based on the provided images and text information."
        ],
        # --- MODIFICATION: Added and modified dynamic texts for diversity ---
        "dynamic_questions": {
            "compare_prefix": "Comparing the normal and abnormal images, ",
            "no_defects_detected": "No {obj_type}s were detected in the image.",
            "defects_detected": "The image contains {obj_type}s.",
            "no_objects_for_coords": "There are no labeled {obj_type}s in the image to provide coordinates for.",
            "defect_types_hint_multi": "These {obj_type}s include multiple types, such as {types}.",
            "defect_types_hint_single": "The main type is {type}.",
            "component_type_hint": "The main type is {type} components.",
            "coordinate_question_format": "The result is required to be returned in json format.",
            "coordinate_question_compare": "{intro}{hints} please provide the bbox coordinates for these defects, {format}",
            "coordinate_question_standard": "{intro}{hints} please provide the bbox coordinates for all these {obj_type}s in the image, {format}",
            "count_question_multi_defect": "How many defects are there in total in the image? And how many of each type are there?",
            "count_question_component": "How many {type} {obj_type}s are there in total in the image?",
            "count_question_default": "How many {obj_type}s are there in total in the image?",
            "location_question_intro": "Please describe in detail the location of the {obj_type}s in the image.",
            "detection_question_compare": "Are any defects detected in the image?",
            "detection_question_standard": "Are any defects detected in the image?",
            "describe_image_question": "Please describe this image",
            "question_templates": {
                "analysis": [
                    "Regarding {prefix}, {predicate}", "Please analyze {prefix} {predicate}",
                    "Could you evaluate {prefix} and {predicate}", "For {prefix}, please {predicate}"
                ],
                "describe": [
                    "Please describe {prefix}{predicate}", "What are the visual characteristics of {prefix}?",
                    "Could you detail {prefix}{predicate}", "Tell me about the visual features of {prefix}."
                ],
                "default": [
                    "What is {prefix}'s {predicate}", "Regarding {prefix}, what is its {predicate}",
                    "For the {prefix} in the image, what is its {predicate}"
                ]
            },
            "object_prefix_bbox": "the labeled target in the image",
            "object_prefix_default": "the {obj_type} in the image"
        }
    }
}

# The get_text function remains unchanged.
def get_text(key: str, lang: str) -> any:
    keys = key.split('.')
    value = PROMPTS.get(lang)
    if not value:
        value = PROMPTS.get('en')
    try:
        for k in keys:
            value = value[k]
        return value
    except KeyError:
        try:
            value = PROMPTS.get('en')
            for k in keys:
                value = value[k]
            return value
        except KeyError:
            return f"[[Text not found for key: {key} and lang: {lang}]]"

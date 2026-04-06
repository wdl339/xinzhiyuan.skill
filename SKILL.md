---
name: create-xinzhiyuan
description: Rewrite papers, abstracts, tech reports, or model releases into sensationalized Chinese AI-media articles in the style of a fast-moving tech公众号. Use when the user wants to turn a paper into a 新智元风格文章, 爆款解读, 论文科普稿, or AI news-feature with strong hooks, narrative pacing, quotes, and CTA while preserving factual accuracy.
argument-hint: "[paper-title-or-topic]"
version: "1.0.0"
user-invocable: true
allowed-tools: Read, Write, Edit, Bash
---

> **Language / 语言**: This skill supports both Chinese and English. Detect the user's language from the first message and respond in the same language throughout. If the source paper is English but the user speaks Chinese, default to Chinese output unless the user explicitly asks otherwise.
>
> 本 Skill 支持中英文。根据用户第一条消息的语言，全程使用同一语言回复。如果论文是英文、但用户用中文提问，默认输出中文稿，除非用户明确要求英文版。

# 新智元.skill 创建器（Claude Code 版）

## 触发条件

当用户说以下任意内容时启动：

- `/create-xinzhiyuan`
- "把这篇论文改成新智元风格"
- "帮我写成公众号文章"
- "把 paper 改写成爆款解读"
- "做一个 AI 媒体风格的论文稿"
- "给这篇论文写一篇像新智元的文章"
- "把这个模型发布整理成媒体稿"

当用户对已生成稿件说以下内容时，进入迭代模式：

- "再标题党一点"
- "太像论文了"
- "更像公众号"
- "保守一点，别太夸张"
- "补点背景"
- "把结尾改成更有传播感"

---

## 工具使用规则

本 Skill 运行在 Agent / Cursor / Claude Code 环境，推荐这样使用工具：

| 任务 | 使用工具 |
|------|---------|
| 读取本地 PDF | `Read` 工具，或 `Bash` → `python3 ${CLAUDE_SKILL_DIR}/tools/paper_demo.py --pdf "{path}"` |
| 根据标题从 arXiv 下载论文 | `Bash` → `python3 ${CLAUDE_SKILL_DIR}/tools/paper_demo.py --title "{paper_title}"` |
| 生成 demo prompt | `Bash` → `python3 ${CLAUDE_SKILL_DIR}/tools/paper_demo.py ...`，读取输出的 `rewrite_prompt.md` |
| 直接产出媒体稿 demo | `Bash` → `python3 ${CLAUDE_SKILL_DIR}/tools/paper_demo.py ... --generate-article` |
| 读取风格规范 | `Read` → `style-guide.md` |
| 读取标题模板 | `Read` → `headline-patterns.md` |
| 读取改写示例 | `Read` → `examples.md` |

如果用户要做"先从 arXiv 拉论文，再改写成新智元风格"的完整链路，优先使用 `tools/paper_demo.py` 先准备材料。

---

## 任务定义

本 Skill 的目标不是简单翻译论文，而是把论文、技术报告、模型发布、项目主页内容，重写为一篇**具有新智元式传播节奏的中文 AI 公众号文章**。

核心特征：

1. **标题先打脸或立旗**：先给情绪张力，再给技术对象
2. **开头先讲为什么值得看**：不是先讲方法，而是先讲影响
3. **叙事上先结果、再问题、再方法、再意义**
4. **段落密度高但句子短**：适合公众号快速扫描
5. **频繁插入媒体化转场**：如"问题来了"、"更狠的是"、"但真正的重点在于"
6. **把技术点翻译成人话**：但不能牺牲事实准确性
7. **结尾要有行业判断或开放性提问**：让文章像媒体稿，不像读书笔记

---

## 风格边界（重要）

允许：

- 强标题
- 强导语
- 冲突化叙事
- 对技术意义做媒体式拔高
- 用口语化表达解释复杂方法

禁止：

1. **编造论文没有写过的结果**
2. **伪造实验数字、榜单名次、引用量**
3. **把作者猜测写成论文结论**
4. **把营销语气凌驾于事实之上**
5. **为了戏剧性故意颠倒结论**

硬规则：

- 所有指标、实验结论、数据集名称、基线模型、作者观点，都必须来自用户提供的材料
- 如果材料不足以支撑某个判断，明确写成"可能"、"从论文看"、"作者认为"
- 用户要求"更夸张"时，可以增强叙事和标题，不可以增强事实

---

## 原材料输入方式

优先支持以下输入：

- PDF 论文
- 论文摘要 abstract
- 项目主页 / README / 发布说明
- 用户手动粘贴的方法、实验、结论
- 用户已经写好的普通解读稿

也支持通过 demo 脚本先整理原材料：

```bash
python3 ${CLAUDE_SKILL_DIR}/tools/paper_demo.py --pdf "/path/to/paper.pdf"
python3 ${CLAUDE_SKILL_DIR}/tools/paper_demo.py --title "Attention Is All You Need"
```

生成的 `rewrite_prompt.md`、`paper_meta.json`、`source_excerpt.txt` 都可以继续作为本 Skill 的输入材料。

如果用户只给一句话，比如：

> "把最近那篇长上下文模型论文改成新智元风格"

先补问以下最少信息：

1. 论文标题或链接
2. 原文材料是 PDF、摘要、还是已有笔记
3. 想要的产物长度：短讯 / 标准稿 / 长文

---

## 主流程：论文改写为媒体稿

### Step 1：识别材料类型

先判断用户给的是哪类材料：

- **完整论文**：优先抽取摘要、引言、方法、实验、结论
- **摘要/笔记**：优先抽取核心问题、方法创新、结果
- **模型发布稿**：优先抽取产品亮点、场景、性能、对行业的影响
- **已有初稿**：保留事实，重写语气、结构、标题、导语

若材料不完整，不要假装完整理解。明确说明：

> 我可以先按现有材料改写成媒体稿，但实验细节和边界结论只能按你提供的内容写。

### Step 2：抽取四层信息

先做信息压缩，再做风格改写。必须提炼出这四层：

**A. 这篇东西到底解决了什么问题**

- 旧方案哪里不行
- 为什么这是个真问题
- 这个问题对谁重要

**B. 它到底做了什么**

- 核心方法一句话版
- 与已有方法最大的不同
- 如果只能保留 3 个技术点，保留哪 3 个

**C. 它到底强在哪**

- 最关键实验结果
- 领先基线是谁
- 优势是更强、更快、更便宜，还是更通用

**D. 它意味着什么**

- 对研究圈意味着什么
- 对产业、产品、Agent、推理、训练、成本意味着什么
- 哪些地方仍然有限制

### Step 3：重组为公众号叙事

默认按以下顺序组织，而不是按论文目录组织：

1. **标题**
2. **导语**
3. **为什么这件事重要**
4. **研究者到底干了什么**
5. **最值得记住的实验结果**
6. **这对行业意味着什么**
7. **限制与未竟问题**
8. **结尾判断 / 提问 / CTA**

### Step 4：执行风格增强

在不改动事实的前提下，做以下增强：

- 把学术标题改成媒体标题
- 把摘要第一段改成导语
- 把方法章节改写成"他们的思路其实是"
- 把实验章节改写成"最关键的是"
- 把结论章节改写成"真正值得关注的是"
- 加入自然转场，避免像逐条翻译

### Step 5：交付前自检

输出前强制检查：

- 有没有任何数字是我自己脑补的
- 有没有把"可能有效"写成"彻底解决"
- 有没有把限制写没了
- 有没有标题过度承诺但正文撑不住
- 有没有保留论文中最值得引用的一两个原句观点

---

## 输出格式模板

默认输出以下结构：

```markdown
# [冲击型标题]

[1 段导语。先讲结果/影响，再讲对象。]

## 这篇工作为什么值得看？

[解释旧问题和行业背景。]

## 他们到底做了什么？

[用人话解释方法，避免堆公式。]

## 最关键的结果是什么？

[只保留最能支撑传播点的实验结果。]

## 真正值得关注的，不只是分数

[讲意义、趋势、产业影响。]

## 这篇工作也别吹过头

[明确限制、边界、未解决问题。]

## 最后

[做一个媒体式收束。可以是判断、问题、或行动号召。]
```

如果用户没有指定长度，默认输出 **1200-1800 字标准稿**。

长度选项：

- **短讯**：300-500 字，适合快讯
- **标准稿**：1200-1800 字，适合公众号主稿
- **长文**：2500 字以上，适合深度解读

---

## 标题策略

标题优先级：

1. 先抓冲突
2. 再给对象
3. 最后补技术关键词

可用句式：

- "`[旧范式]` 被打穿了？`[论文/模型]` 给出新解法"
- "`[公司/团队]` 放出`[模型/论文名]`，`[结果/意义]`"
- "`[技术难题]` 终于有解了？这篇论文把`[关键点]`做成了"
- "`[数字/结果]` 只是表面，更关键的是`[真正亮点]`"
- "`[热点方向]` 又变天了，这篇论文想重写规则"

标题不要：

- 纯学术翻译腔
- 只有模型名没有观点
- 明显超出正文可支撑范围

更多模式见 [headline-patterns.md](headline-patterns.md)。

---

## 导语策略

导语要完成三件事：

1. 说清楚这篇东西是什么
2. 说清楚为什么值得读者花 3 分钟看
3. 预告正文最重要的一个传播点

好的导语通常长这样：

> 某个老问题卡了行业很久，大家都在拼命补 patch。现在，一篇新论文试图从底层换解法。它未必已经一锤定音，但至少把讨论往前推了一大步。

不要一上来就：

- 罗列作者单位
- 翻译摘要
- 直接进入公式细节

---

## 方法改写规则

把方法写成"读者可以跟上的解释"，而不是论文精翻：

- 先说动机，再说设计
- 先说直觉，再说模块
- 只保留支撑理解的术语
- 公式除非用户明确要求，否则不展开

常用转场：

- "研究团队的思路其实不复杂："
- "他们抓住的关键点在于："
- "换句话说，作者想解决的是："
- "更具体一点看："

---

## 实验改写规则

实验部分只保留最能证明观点的内容：

- 1 个最强结果
- 1 组最关键对比
- 1 个最能说明 trade-off 的限制

不要把所有表格逐行搬运。

如果实验材料很多，优先输出：

1. 哪项指标最重要
2. 超过了谁
3. 代价是什么

---

## 结尾规则

结尾不能像论文 conclusion。

优先使用以下三种收束方式之一：

1. **趋势判断型**：这可能会把某个方向往前推一大步
2. **产业影响型**：如果效果可复现，谁会最先受影响
3. **开放问题型**：它很强，但真正决定价值的问题还没回答

参考风格见 [style-guide.md](style-guide.md) 和 [examples.md](examples.md)。

---

## 迭代模式

当用户要求调整时，优先识别是哪一类修改：

- **更媒体一点**：增强标题、导语、转场、结尾判断
- **更保守一点**：减少夸张词，补充边界与限制
- **更像论文一点**：保留更完整的方法与实验细节
- **更像新智元一点**：加强"行业变了"、"旧范式失灵"、"真正重点是"这类媒体节奏
- **更适合朋友圈传播**：缩短段落，强化观点句与金句

修改时遵守：

1. 只改写风格与结构，不改事实
2. 如果用户新增材料，先吸收再改写
3. 如果用户说"太夸张"，优先处理标题、导语、结尾

---

# English Version

# Xinzhiyuan-style Paper Rewriter

## What This Skill Does

This Skill rewrites papers, abstracts, model releases, and technical notes into a fast-paced Chinese AI-media article with strong hooks, narrative flow, plain-language explanations, and punchy endings.

## Core Workflow

1. Identify the source type: full paper, abstract, notes, release post, or rough draft.
2. Extract four layers: problem, method, result, implication.
3. Rebuild the structure into media flow instead of paper flow.
4. Add stylistic energy without changing facts.
5. Self-check every number, claim, and limitation before final delivery.

## Output Defaults

- Default language: follow the user's language
- Default article type: Chinese standard-length article
- Default length: 1200-1800 Chinese characters unless requested otherwise

## Never Do

- Invent metrics or benchmark wins
- Turn hypotheses into conclusions
- Hide limitations just to make the article more exciting
- Over-promise in the title beyond what the body can support

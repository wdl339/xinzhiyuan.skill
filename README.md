<div align="center">

# 新智元.skill

> *"你们搞大模型的就是码奸，你们已经害死前端兄弟了，还要害死后端兄弟，测试兄弟，运维兄弟，害死网安兄弟，害死ic兄弟，害死公众号兄弟，最后害死自己害死全人类"*

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![Cursor](https://img.shields.io/badge/Cursor-Skill-blueviolet)](https://cursor.com)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Style-green)](https://agentskills.io)

<br>

给一篇论文 PDF、一个 arXiv 标题、或者一份技术报告<br>
生成一篇**像新智元那样有传播感的 AI 公众号文章**<br>

[安装](#安装) · [使用](#使用) · [实战-demo](#实战-demo) · [项目结构](#项目结构) · [详细安装说明](INSTALL.md)

</div>

---

## 这是什么

`xinzhiyuan-skill` 是一个面向 Agent / Cursor / Claude Code 的写作型 Skill。

它不是做论文精翻，而是把论文、abstract、模型发布稿、README、研究笔记，改写成一种更像 AI 媒体稿的表达：

- 标题更强
- 导语更像公众号
- 方法解释更像人话
- 实验结果更像观点
- 结尾更像行业判断

注：本 skill 全程由 Cursor 生成与审核，由人类点击发布。若 AI 生成的内容中出现不适宜的观点，本人类不对 AI 觉醒的自由意志负责。

---

## 功能特性

### Skill 层

- 论文 -> 新智元风格公众号稿
- abstract / README / 发布说明 -> 媒体化解读
- 已有普通稿 -> 标题、导语、结构、结尾重写
- 支持继续迭代："更像公众号一点"、"保守一点"、"标题党一点"

### Demo 层

- 支持从本地 PDF 读取论文
- 支持给定论文标题，从 arXiv 自动检索并下载 PDF
- 自动抽取 `abstract / introduction / conclusion` 片段
- 自动生成可直接喂给大模型的改写 prompt
- 如果配置了 OpenAI 兼容 API，可一键生成完整文章

---

## 安装

### Cursor

推荐安装到个人 skills 目录：

```bash
mkdir -p ~/.cursor/skills
git clone https://github.com/wdl339/xinzhiyuan.skill ~/.cursor/skills/create-xinzhiyuan
```

也可以安装到项目级目录：

```bash
mkdir -p .cursor/skills
git clone https://github.com/wdl339/xinzhiyuan.skill .cursor/skills/create-xinzhiyuan
```

### Claude Code / 兼容 AgentSkills 的环境

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/wdl339/xinzhiyuan.skill ~/.claude/skills/create-xinzhiyuan
```

### 依赖

```bash
git clone https://github.com/wdl339/xinzhiyuan.skill
cd xinzhiyuan.skill
pip3 install -r requirements.txt
```

---

## 使用

在支持 Skill 的环境里，可以直接说：

```text
把这篇论文改成新智元风格
```

或者：

```text
/create-xinzhiyuan
```

常见触发方式：

- "把这篇 paper 改成新智元风格"
- "给这篇论文写一篇公众号稿"
- "把这个模型发布整理成媒体稿"
- "更像公众号一点"
- "别太夸张，保守一点"

---

## 实战 Demo

### 1. 本地 PDF -> 准备改写材料

```bash
git clone https://github.com/wdl339/xinzhiyuan.skill
cd xinzhiyuan.skill

python3 tools/paper_demo.py \
  --pdf "/path/to/paper.pdf"
```

默认会输出到：

```text
demo_outputs/<paper-slug>/
```

生成文件：

- `paper_meta.json`：论文元数据
- `source_excerpt.txt`：抽取后的关键片段
- `rewrite_prompt.md`：可直接贴给任意模型的改写 prompt

### 2. 给定 arXiv 标题 -> 自动下载并准备材料

```bash
git clone https://github.com/wdl339/xinzhiyuan.skill
cd xinzhiyuan.skill

python3 tools/paper_demo.py \
  --title "Attention Is All You Need"
```

这会自动：

1. 从 arXiv 检索标题最接近的论文
2. 下载 PDF 到 `downloads/`
3. 提取关键文本
4. 生成 `rewrite_prompt.md`

### 3. 一键生成完整文章

如果你本地配置了 OpenAI 兼容接口：

```bash
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4.1-mini"

python3 tools/paper_demo.py \
  --title "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models" \
  --generate-article
```

生成后会额外得到：

- `xinzhiyuan_article.md`

### 4. 控制语言和篇幅

```bash
python3 tools/paper_demo.py \
  --pdf "/path/to/paper.pdf" \
  --language zh \
  --length long
```

可选值：

- `--language zh|en`
- `--length short|standard|long`

---

## 效果预期

这套 demo 默认不是做"忠实直译"，而是做"媒体化重组"：

- 标题先给观点
- 导语先讲影响
- 方法部分优先讲直觉
- 实验部分只保留最关键结果
- 结尾给趋势判断或开放问题

如果你想更克制，可以在 prompt 或 Skill 里继续加一句：

```text
保守一点，不要太像爆款号，边界和限制多写一点
```

---

## 项目结构

```text
xinzhiyuan-skill/
├── SKILL.md                  # Skill 主入口
├── README.md                 # 项目说明
├── INSTALL.md                # 详细安装与依赖说明
├── requirements.txt          # Demo 依赖
├── .gitignore                # 忽略下载与输出目录
├── style-guide.md            # 新智元风格速查
├── headline-patterns.md      # 标题模板库
├── examples.md               # 改写示例
├── prompts/
│   └── demo_writer.md        # Demo 用改写 prompt 模板
├── tools/
│   └── paper_demo.py         # PDF / arXiv 实战 demo
└── docs/
    └── DEMO.md               # Demo 详细说明
```

---

## 注意事项

- 标题可以有传播感，但正文不能超出证据范围
- arXiv 标题检索是近似匹配，建议尽量给完整标题
- PDF 文本抽取质量取决于论文排版；扫描版 PDF 不一定适合
- `--generate-article` 依赖你本地可用的 OpenAI 兼容接口

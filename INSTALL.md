# 新智元.skill 安装说明

## 选择安装位置

### A. Cursor（推荐）

个人级安装：

```bash
mkdir -p ~/.cursor/skills
cp -R /root/xxx-skill/xinzhiyuan-skill ~/.cursor/skills/create-xinzhiyuan
```

项目级安装：

```bash
mkdir -p .cursor/skills
cp -R /root/xxx-skill/xinzhiyuan-skill .cursor/skills/create-xinzhiyuan
```

安装后，在 Cursor Agent 里直接说：

```text
把这篇论文改成新智元风格
```

### B. Claude Code / 兼容 AgentSkills 的环境

```bash
mkdir -p ~/.claude/skills
cp -R /root/xxx-skill/xinzhiyuan-skill ~/.claude/skills/create-xinzhiyuan
```

---

## 依赖安装

```bash
cd /root/xxx-skill/xinzhiyuan-skill
pip3 install -r requirements.txt
```

默认依赖只有两类：

- `requests`：访问 arXiv API、下载 PDF、调用 OpenAI 兼容接口
- `pypdf`：提取本地或下载后的 PDF 文本

---

## Demo 环境变量

如果只想准备 prompt，不需要配置任何 API Key。

如果想让 demo 直接生成文章，需要配置 OpenAI 兼容接口：

```bash
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4.1-mini"
```

兼容大多数 OpenAI-style 服务，只要支持：

- `POST /chat/completions`

---

## 快速验证

```bash
cd /root/xxx-skill/xinzhiyuan-skill

python3 tools/paper_demo.py --help
```

如果想验证本地 PDF：

```bash
python3 tools/paper_demo.py --pdf "/path/to/paper.pdf"
```

如果想验证 arXiv 标题下载：

```bash
python3 tools/paper_demo.py --title "Attention Is All You Need"
```

---

## 输出目录说明

每次运行 demo，都会在 `demo_outputs/<paper-slug>/` 下生成：

```text
paper_meta.json
source_excerpt.txt
rewrite_prompt.md
xinzhiyuan_article.md   # 仅在 --generate-article 时生成
```

如果使用了 `--title`，下载的 PDF 会放在：

```text
downloads/
```

---

## 常见问题

### Q: 标题搜不到论文怎么办？

A: 先尝试给完整标题。如果仍然搜不到，建议先从 arXiv 手动下载 PDF，再用 `--pdf` 模式。

### Q: PDF 抽取出来的文本很乱怎么办？

A: 某些双栏、扫描版或图片型 PDF 会导致抽取质量不高。此时建议：

1. 手动补充 abstract 或关键段落
2. 换成 arXiv 源 PDF
3. 让 demo 只做 prompt 准备，再手动修一下源材料

### Q: 为什么只抽前几页？

A: demo 默认优先抽取 abstract、introduction、conclusion 和正文前段，目的是控制 prompt 长度，减少噪声。

### Q: 一定要联网吗？

A: `--pdf` 模式不需要联网。`--title` 模式需要访问 arXiv。`--generate-article` 还需要访问你的模型接口。

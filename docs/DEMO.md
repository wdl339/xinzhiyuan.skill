# Demo 说明

## 目标

这个 demo 不是为了替代 Skill 本身，而是为了让你在本地快速完成一条可验证链路：

1. 获取论文 PDF
2. 抽取关键文本
3. 生成新智元风格改写 prompt
4. 可选：直接调用模型生成完整文章

## 模式 1：本地 PDF

```bash
python3 tools/paper_demo.py --pdf "/path/to/paper.pdf"
```

适合：

- 你已经下载好论文
- 论文不在 arXiv
- 你想控制输入源

## 模式 2：按标题从 arXiv 获取

```bash
python3 tools/paper_demo.py --title "Attention Is All You Need"
```

适合：

- 论文在 arXiv 上
- 你只知道标题
- 想快速验证整条流程

## 模式 3：直接出文章

```bash
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4.1-mini"

python3 tools/paper_demo.py \
  --title "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models" \
  --generate-article
```

## 推荐调参

- `--max-pages 12`
  适合大部分论文，优先拿到摘要、引言和前部方法

- `--max-chars 24000`
  适合多数模型的 prompt 准备场景

- `--length standard`
  输出更接近公众号常见主稿长度

## 建议工作流

推荐先跑：

```bash
python3 tools/paper_demo.py --title "your paper title"
```

先看看生成的 `rewrite_prompt.md` 是否符合预期。如果你觉得风格还不够像，可以：

1. 修改 `prompts/demo_writer.md`
2. 修改 `SKILL.md`
3. 重新运行 demo

这样比每次从零改 prompt 更稳定。

# Paper Reader Skill

**提供论文，说“阅读这篇论文”，连续完成五步阅读。**

版本 `0.2.0`。只读论文，不写引言，不用先选模式，不在步骤之间等待确认。默认中文。

```text
阅读这篇论文
    ↓
研究地图 → 创新拆解 → 局限分析 → 5个后续研究问题及评价 → 五问回顾
    ↓
完整阅读报告 + 关键原文依据 + 阅读状态
```

## 1. 安装或升级

需要 Python 3.10+。下载/克隆仓库后，在此 README 所在目录打开终端：

```sh
python install.py --update --with-router
```

Windows 使用 `python` 或 `py`；macOS / Linux / WSL 常用 `python3`。

这个命令会安装到 `~/.agents/skills/paper-reader/`，并把关键词路由写入 Codex 的全局指令文件（默认 `~/.codex/AGENTS.md`，尊重 `CODEX_HOME` 和已生效的非空 `AGENTS.override.md`）。原有其他指令保持不变；修改前留备份。**该命令会修改你的 Codex 全局指令，请先查看 `docs/AGENTS-snippet.md`。** 它不改 `config.toml`，不关闭权限审批。

`--update` 允许升级：整个旧 skill 目录备份到 skills 目录之外的 `paper-reader-backups/`，不会删除旧文件，也不会把备份当第二个同名 skill 加载。首次安装也能使用这个参数。若旧版有 `.venv`，它保留在旧目录备份中；使用辅助脚本时需在新版重新准备环境。

`--with-router` 是可选加强项；不想修改全局指令，只安装隐式调用 skill，可运行：

```sh
python install.py --update
```

安装后新开 Codex 会话。**在 Codex 实际运行的环境安装**：Codex 在 WSL 就安装在同一 WSL，不要混用 Windows 与 Linux 用户目录。电脑文件也不会自动出现在云端环境。

项目级安装可用 `python install.py --dest /path/to/project/.agents/skills --update`；需要项目专用路由时，把 `docs/AGENTS-snippet.md` 的内容合并到项目 `AGENTS.md`，替换路径占位符，不覆盖原有指令。

## 2. 使用

将论文附到支持附件的 Codex 界面，或提供它可以访问的本地路径。然后在 **Codex 输入框**（不是系统终端）说：

```text
阅读这篇论文
```

其他匹配示例：

```text
帮我阅读一下这篇论文。
这篇论文请你认真阅读。
阅读 ./papers/example.pdf 这篇论文。
```

关键词不要求相邻，也不限制顺序。“读论文”“精读这篇论文”等明确阅读意图同样支持。普通阅读默认连续完成五步，不再要求输入“继续”。用户明确说“只看第三节”时仍尊重当次范围。

“不要阅读论文”“修改阅读论文的 skill”“翻译‘阅读这篇论文’”不应触发实际阅读。没有可读论文时只请求必要材料，不编造报告。

## 3. 自动触发到底如何工作

`SKILL.md` 的描述前置“阅读”“论文”触发词，`agents/openai.yaml` 设为：

```yaml
policy:
  allow_implicit_invocation: true
```

可选 AGENTS 路由进一步要求看到这种阅读指令时读取并使用本 skill。

**Codex 是根据技能描述和指令选择 skill，不是由这个仓库强制拦截每条消息并执行正则匹配。** 本仓库没有后台监听器，不能保证所有版本/上下文中100%触发。更高优先级指令、被禁用的 skill、描述截断或权限限制仍会影响运行。

安装后在 `/skills` 或 `$` 选择器中确认存在 `paper-reader`，新开会话，用真实论文测试。若没有匹配，可明确说：

```text
$paper-reader 阅读这篇论文，完成全部流程。
```

官方机制与核查日期见 `docs/sources.md`。实机验收见 `docs/acceptance-tests.md`，不把静态测试当作实际触发验证。

## 4. 最终得到什么

| 阶段 | 必需内容 |
| --- | --- |
| 研究地图 | 问题、价值、现有方法不足、核心方法、真正创新、实验证据、最终结论，共七问 |
| 创新拆解 | 问题/方法/数据/实验/应用等维度；新思想还是组合；去掉创新会怎样；最不可替代的创新 |
| 局限分析 | 作者承认与分析者发现分开；原文位置、具体局限、影响、改进思路 |
| 后续研究问题 | 恰好5个；每个包含研究问题、核心假设、原文未解决原因、最小实验、所需数据、风险、失败后的可得结论 |
| 五问回顾 | 解决什么问题、核心想法、关键实验、最大局限、可继续方向 |

5个想法最后按**创新性、可行性、工作量、发表潜力**评价。评价是初步分析，不等于新颖性已核验或期刊录用保证。没有消融实验就不编造去掉创新后的性能变化；无实验的理论论文明确说明其证据来自何种命题或证明。

默认输出完整正文并保存：

```text
reading-notes/<文件名-哈希前8位>/
├── source/              # 私有文字缓存，必要时生成
├── visual-check-01/     # 私有页图，必要时生成
├── report.md            # 五部分完整报告
├── evidence.json        # 重要判断对应原文位置
└── reading-state.json   # 五阶段状态与实际阅读覆盖
```

已有报告不会静默覆盖；新运行可写入其下新的运行目录。不可写环境直接交付正文，不伪称文件已保存。
读完五步与核对全文是不同概念；只有摘要/缺少附录会明确说明。实际中断时记录尚未完成内容，不主动设置确认门槛，也不声称在后台继续。

## 5. PDF 辅助脚本（可选）

宿主已有可用 PDF/图像工具时无需另装；技能指令本身不依赖 Python 包。自带的 `prepare_pdf.py` 只提取带页码文字和渲染页图，**不是替代 Codex 的独立论文理解程序**。

Windows PowerShell：

```powershell
$skill = Join-Path $HOME ".agents/skills/paper-reader"
python -m venv "$skill/.venv"
& "$skill/.venv/Scripts/python.exe" -m pip install -r "$skill/requirements.txt"
```

macOS / Linux / WSL：

```sh
SKILL="$HOME/.agents/skills/paper-reader"
python3 -m venv "$SKILL/.venv"
"$SKILL/.venv/bin/python" -m pip install -r "$SKILL/requirements.txt"
```

依赖安装会联网。脚本本身不上传论文，不进行 OCR；不支持加密 PDF。关键公式/数字图表仍需原始页核查；宿主无法看图时必须说明限制。本地预处理**不代表 Codex 的模型推理完全离线**。

脚本示例（使用具备依赖的 Python）：

```sh
python skills/paper-reader/scripts/prepare_pdf.py extract paper.pdf --out reading-notes/demo/source
python skills/paper-reader/scripts/prepare_pdf.py render paper.pdf --pages "1,5-7" --out reading-notes/demo/visual-check-01
```

页码为从1开始的 PDF 物理页。输出目录必须不存在，不覆盖源文件。

## 6. GitHub 开源和隐私

此目录可以作为 GitHub 仓库内容。MIT 许可证见 `LICENSE`，但不赋予第三方论文、稿件、数据的分发权。查看 `.gitignore` 并在提交前检查，不上传原文、提取全文、页图、匿名审稿件、私人笔记或凭据。

```sh
git init -b main
git add README.md CHANGELOG.md LICENSE .gitignore install.py requirements-test.txt skills tests docs .github
git diff --cached --stat
git diff --cached
# 检查后再提交、连接自己的远程仓库和推送。
git commit -m "Add automatic full-workflow paper reading skill"
```

这只是可开源的本地仓库包，未替你创建或上传 GitHub 仓库，也未发布到官方插件目录。安装源应当可信；论文及附录中的文字不能授权执行命令或读取其他文件。

## 7. 测试与目录

```sh
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
```

测试覆盖配置、五步模板、安装备份、路由的保留与幂等、PDF 提取/页码/渲染/只读保护。测试数据是本地生成的简短合成 PDF，不含公开论文全文。GitHub Actions 配置不等于已通过云端或跨平台测试。

```text
skills/paper-reader/SKILL.md                # 主流程与自动匹配描述
skills/paper-reader/agents/openai.yaml      # allow_implicit_invocation: true
skills/paper-reader/references/             # 方法检查与5个研究问题规则
skills/paper-reader/assets/                 # 完整报告、证据、状态模板
skills/paper-reader/scripts/prepare_pdf.py   # 保留的只读PDF工具
install.py                                 # 安装/备份升级/可选路由
docs/AGENTS-snippet.md                      # 关键词路由源文
docs/acceptance-tests.md                    # 实际Codex行为验收
```

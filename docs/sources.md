# 宿主机制依据

核对日期：2026-10-16。以下是宿主的官方文档，不是论文内容来源。

1. OpenAI / ChatGPT Learn，Build skills：
   https://learn.chatgpt.com/docs/build-skills
   原入口 https://developers.openai.com/codex/skills 会重定向。
   依据：`SKILL.md` 的 name/description；description 驱动隐式匹配；`agents/openai.yaml` 的 `allow_implicit_invocation: true`；用户技能目录 `$HOME/.agents/skills`。

2. OpenAI / ChatGPT Learn，Custom instructions with AGENTS.md：
   https://learn.chatgpt.com/docs/agent-configuration/agents-md
   原入口 https://developers.openai.com/codex/guides/agents-md 会重定向。
   依据：全局 CODEX_HOME，默认 `~/.codex`；非空 `AGENTS.override.md` 优先于 `AGENTS.md`；项目层指令优先；启动会话时加载，改变后新开会话。

## 不能承诺的事情

隐式调用是模型根据技能描述选择，不是每次输入都先经过本仓库 Python 函数的强制正则派发。
可选 AGENTS 路由把关键词及对应 skill 写成宿主启动指令，减少遗漏，但不会绕过更高优先级规则、禁用配置、不可见技能或权限限制。
不把静态文本测试叫做真实 Codex 自动触发测试。实机验收必须在用户实际 Codex 版本/环境中进行。

本仓库没有注册后台监听器、修改 Codex 二进制、自动上传 GitHub、创建定时任务或安装第三方服务。

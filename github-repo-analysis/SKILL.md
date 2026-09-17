---
name: "GitHub 仓库深度分析"
description: "对 GitHub 仓库进行多维度深度分析：技术栈、代码结构、活跃度、社区健康度与风险评估，输出结构化分析报告"
alwaysAllow: ["Bash"]
---

# GitHub 仓库深度分析

当用户要求分析一个 GitHub 仓库时，按照本指南执行系统化的深度分析，并输出结构化的中文分析报告。

## 输入识别

用户可能提供以下任一形式的输入：
- 完整 URL：`https://github.com/owner/repo`
- 简写形式：`owner/repo`
- 仅仓库描述（此时需先用 web 搜索定位目标仓库，并与用户确认）

如缺少必要信息（例如分析侧重点），可以提问澄清，但若用户意图明确则直接开始分析。

## 数据收集

优先使用可用的 GitHub source / MCP 工具；若不可用，使用以下替代方案：

1. **GitHub REST API（无需认证，有限流）**：
   ```bash
   curl -s "https://api.github.com/repos/{owner}/{repo}"
   curl -s "https://api.github.com/repos/{owner}/{repo}/languages"
   curl -s "https://api.github.com/repos/{owner}/{repo}/contributors?per_page=10"
   curl -s "https://api.github.com/repos/{owner}/{repo}/commits?per_page=30"
   curl -s "https://api.github.com/repos/{owner}/{repo}/releases?per_page=5"
   curl -s "https://api.github.com/repos/{owner}/{repo}/community/profile"
   ```
2. **web_fetch**：抓取仓库主页、README、Issues/PR 页面获取定性信息。
3. **浅克隆（需要深入代码结构时）**：
   ```bash
   git clone --depth 1 https://github.com/{owner}/{repo}.git
   ```
   克隆后分析目录结构、依赖清单（package.json / pyproject.toml / go.mod / Cargo.toml 等）、测试覆盖情况和代码规模（可用 `tokei` 或 `cloc`，若未安装则用 `find` + `wc -l` 估算）。分析完成后清理临时克隆目录。

注意遵守 API 速率限制；如遇到 403 限流，改用 web_fetch 抓取网页信息。

## 分析维度

报告应覆盖以下维度（可根据仓库实际情况裁剪）：

### 1. 仓库概览
- 名称、描述、主页、许可证
- Star / Fork / Watch / Open Issues 数量及趋势
- 创建时间、最近提交时间、默认分支

### 2. 技术栈
- 语言占比（通过 languages API）
- 框架、运行时、构建工具、包管理器
- 关键依赖及其版本健康度（是否过时、是否存在知名漏洞依赖）

### 3. 代码结构与质量
- 顶层目录结构（用 Mermaid 或树状图展示核心模块划分）
- 代码组织模式（单体 / monorepo / 插件化等）
- **基于代码结构解释代码**：按模块/分层/包结构梳理核心类、函数、接口的职责，说明调用链路、数据流转与关键流程（可用 Mermaid 序列图或流程图辅助）
- **解释核心原理**：对关键算法、状态机、事件机制、协议实现、并发模型、持久化策略等进行说明，避免只罗列文件名
- **阐述设计理念**：分析项目采用的设计模式、架构风格（如 MVC、微内核、事件驱动、CQRS、DDD 等），以及可维护性、扩展性、性能之间的取舍，是否体现 SOLID、KISS、YAGNI、DRY 等原则
- 测试配置与覆盖迹象、CI/CD 配置（GitHub Actions 等）
- 代码规范工具（linter / formatter / 类型检查）

### 4. 活跃度与维护状况
- 提交频率（近 3 个月 / 近一年）
- 最近 release 节奏与版本策略（语义化版本？）
- Issue / PR 的中位响应与关闭情况
- 维护者数量与集中度风险（是否依赖单一核心维护者，"巴士因子"）

### 5. 社区健康度
- README 完整度、贡献指南、行为准则、安全策略
- 文档质量与站点
- 社区互动氛围（讨论区、issue 语气）

### 6. 综合评估
- 优势（3-5 条）
- 风险与隐患（3-5 条，如维护停滞、依赖陈旧、许可证风险）
- 适用场景建议：生产可用 / 试用 / 学习参考 / 不建议采用
- 总体评分（可选，10 分制，需说明评分依据）

## 输出要求

- 使用**中文**输出报告，结构清晰，合理使用标题、列表和表格。
- 结构化数据（如语言占比、指标汇总、版本历史）使用 `datatable` 块渲染，不要只用纯文本。
- 仓库结构、模块关系等适合图形化的内容使用 **Mermaid 图**。
- 所有关键数字须标注数据来源（API / 页面抓取）与统计时间；无法获取的数据明确说明"数据不可用"，**禁止编造**。
- 结论须基于证据，避免主观臆断；区分"事实"与"推断"。
- 报告结尾给出 3-5 条可执行的后续建议（如值得关注的 issue、替代方案对比、本地试跑步骤）。

## Obsidian Vault 输出规范

分析完成后，必须将内容写入 Obsidian vault 的单一 Markdown 文件中：

1. **Github 分类目录**：在 Obsidian vault 根目录下创建 `Github` 文件夹（如不存在），用于集中存放所有 GitHub 仓库分析。
2. **新建仓库专属目录**：在 `Github` 文件夹内创建以 `owner-repo`（仓库全名）命名的子文件夹，例如 `Github/facebook-react`、`Github/microsoft-vscode`。
3. **单一分析文件**：在该仓库目录下只创建一个主分析文件，命名为 `{owner-repo}.md`（空格用 `-` 替换），例如 `facebook-react.md`。
4. **文件内分类**：在该单一 Markdown 文件中，使用二级及以上标题将所有分析内容按以下结构分类：
   - `## 1. 概览` — 仓库基础信息、核心指标、许可证、评分。
   - `## 2. 技术栈` — 语言占比、框架、构建工具、依赖健康度。
   - `## 3. 代码结构` — 目录结构、模块关系、核心原理解析、Mermaid 图。
   - `## 4. 活跃度与维护` — 提交频率、版本策略、Issue/PR 统计、维护者风险。
   - `## 5. 社区健康度` — README、贡献指南、文档、互动氛围。
   - `## 6. 综合评估与建议` — 优势、风险、适用场景、后续建议。
4. **附件目录**：在同一目录下创建 `assets/` 子目录，存放 Mermaid 图、截图、导出表格等附件，并在主文件中使用相对路径引用，例如 `![结构图](./assets/architecture.svg)`。
5. **目录导航**：在文件开头添加 Obsidian 可识别的目录（TOC），例如：
   ```markdown
   - [[#1. 概览]]
   - [[#2. 技术栈]]
   - [[#3. 代码结构]]
   - [[#4. 活跃度与维护]]
   - [[#5. 社区健康度]]
   - [[#6. 综合评估与建议]]
   ```

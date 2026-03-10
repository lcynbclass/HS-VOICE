# HS-VOICE: Honkai Star Rail Voice Analyst

### 🌟 项目简介
HS-VOICE 是一款针对《崩坏：星穹铁道》社区设计的 AI 舆情分析工具。
利用 LLM (Gemini 2.5) 实现对海量玩家反馈的**自动化打标、情绪定性、痛点提取**，并生成可落地的**运营策略建议**。

### 🚀 核心功能
- **一键清洗**: 自动处理非结构化评论。
- **业务归因**: 自动识别 [角色强度, 美术演出, 福利抽卡] 等讨论维度。
- **高危预警**: 自动拦截负面舆情并产出应对建议。
- **数据可视化**: 实时生成情绪健康度看板。

### 🛠️ 快速开始
1. 克隆项目: `git clone https://github.com/你的用户名/HS-VOICE.git`
2. 安装依赖: `pip install -r requirements.txt`
3. 运行: `streamlit run app.py`
import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import time
import os

# ==========================================
# 1. 页面与全局配置
# ==========================================
st.set_page_config(
    page_title="HS-VOICE | 星铁舆情分析助手",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 HS-VOICE：星铁玩家舆情分析助手")
st.markdown("---")

# ==========================================
# 2. 侧边栏：系统配置 (解耦代理与 API)
# ==========================================
with st.sidebar:
    st.header("⚙️ 系统配置中心")
    st.info("请完成以下配置以启动 AI 引擎")

    # API Key 输入
    api_key = st.text_input("1. Google API Key", type="password", help="从 Google AI Studio 获取的 API 密钥")

    # 代理设置 (针对国内环境)
    proxy_port = st.text_input("2. 本地代理端口 (可选)", placeholder="例如: 7890",
                               help="若在中国大陆运行，请输入 Clash/v2ray 的本地端口")

    if proxy_port:
        os.environ['HTTP_PROXY'] = f'http://127.0.0.1:{proxy_port}'
        os.environ['HTTPS_PROXY'] = f'http://127.0.0.1:{proxy_port}'
        st.success(f"已挂载代理端口: {proxy_port}")

    st.divider()
    st.caption("Developed by HS-VOICE Project Team")

# 初始化模型逻辑
if api_key:
    try:
        genai.configure(api_key=api_key)
        # 使用 Gemini 2.5 系列最新模型
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"模型初始化失败: {e}")


# ==========================================
# 3. AI 分析引擎 (核心 Prompt 逻辑)
# ==========================================
def analyze_comment(comment_text):
    """
    调用大模型进行业务归因与情绪分析
    """
    prompt = f"""
    你是一个资深的游戏产品运营专家。请分析以下《崩坏：星穹铁道》玩家评论，并严格输出 JSON 格式。
    不要输出任何说明文字或 Markdown 格式，仅输出纯 JSON 字符串。

    JSON 字段定义：
    - "category": 业务维度，限选 [角色与强度, 美术与演出, 福利与抽卡, 玩法与机制, 基础优化]
    - "sentiment": 情绪倾向，限选 [正面, 负面, 中立]
    - "summary": 10字以内提炼核心痛点
    - "suggestion": 针对该反馈，给运营/策划团队提一句具体的 Action Item

    玩家评论：{comment_text}
    """
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()

        # 稳健性处理：移除可能的 Markdown 标记
        for tag in ["```json", "```"]:
            if raw_text.startswith(tag): raw_text = raw_text.replace(tag, "", 1)
            if raw_text.endswith(tag): raw_text = raw_text.rsplit(tag, 1)[0]

        return json.loads(raw_text.strip())
    except Exception as e:
        # 捕获 429 频率限制或网络超时
        return {"category": "分析失败", "sentiment": "未知", "summary": "API调用异常", "suggestion": str(e)}


# ==========================================
# 4. 前端交互与可视化大屏
# ==========================================
uploaded_file = st.file_uploader("📂 上传玩家反馈数据 (支持 CSV 格式)", type="csv")

if uploaded_file is not None:
    raw_df = pd.read_csv(uploaded_file)

    if '评论内容' not in raw_df.columns:
        st.error("错误：CSV 文件必须包含名为【评论内容】的列！")
    else:
        st.write("### 📥 原始数据预览")
        st.dataframe(raw_df.head(5), use_container_width=True)

        if st.button("🚀 启动 HS-VOICE 智能解析"):
            if not api_key:
                st.warning("⚠️ 请先在侧边栏配置 API Key")
            else:
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()

                # 开始循环处理
                for index, row in raw_df.iterrows():
                    status_text.text(f"正在处理第 {index + 1}/{len(raw_df)} 条反馈...")
                    analysis = analyze_comment(row['评论内容'])
                    analysis['用户名'] = row.get('用户名', '匿名用户')
                    analysis['原始评论'] = row['评论内容']
                    results.append(analysis)

                    # 更新进度
                    progress_bar.progress((index + 1) / len(raw_df))
                    # 🚨 遵守免费版 API 的每分钟频率限制 (Rate Limit)
                    time.sleep(5)

                status_text.text("✅ 舆情打标与分析完成")
                res_df = pd.DataFrame(results)

                # --- 渲染分析大盘 ---
                st.divider()
                st.header("📈 HS-VOICE 舆情看板")

                # 顶部指标卡
                m1, m2, m3 = st.columns(3)
                m1.metric("分析样本总数", len(res_df))
                m2.metric("负面情绪占比", f"{(len(res_df[res_df['sentiment'] == '负面']) / len(res_df) * 100):.1f}%")
                m3.metric("需关注建议数", len(res_df[res_df['sentiment'] != '正面']))

                # 图表分栏
                c1, c2 = st.columns(2)
                with c1:
                    st.write("**业务维度分布 (Category)**")
                    st.bar_chart(res_df['category'].value_counts())
                with c2:
                    st.write("**情绪健康度 (Sentiment)**")
                    st.bar_chart(res_df['sentiment'].value_counts())

                # 重点预警区
                st.divider()
                st.subheader("🚨 高危舆情与运营建议")
                neg_df = res_df[res_df['sentiment'] == '负面']
                if not neg_df.empty:
                    st.dataframe(neg_df[['category', 'summary', 'suggestion', '原始评论']], use_container_width=True)
                else:
                    st.success("暂未发现显著负面舆情，版本口碑良好。")

                # 全量导出
                st.subheader("🗄️ 全量结构化数据导出")
                st.dataframe(res_df, use_container_width=True)
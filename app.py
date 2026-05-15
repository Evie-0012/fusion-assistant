import streamlit as st
import sqlite3
from openai import OpenAI

# ===== 页面配置 =====
st.set_page_config(
    page_title="聚变行业智能助手",
    page_icon="⚡",
    layout="centered"
)

# ===== 样式：模仿 MBTI 首页的清爽风格 =====
st.markdown("""
<style>
    .main-title {
        text-align: center;
        font-size: 2.8rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stChatMessage {
        border-radius: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ===== 标题 =====
st.markdown('<div class="main-title">⚡ 聚变行业智能助手</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">基于大模型的核聚变企业与投资机构查询系统</div>', unsafe_allow_html=True)

# ===== 侧边栏：配置 =====
with st.sidebar:
    st.header("⚙️ 设置")
    api_key = st.text_input("DeepSeek API Key", type="password", placeholder="sk-...")
    db_path = st.text_input("数据库路径", value="fusion_industry.db")
    
    st.divider()
    st.caption("💡 提示：可以查询企业信息、投资机构、融资动态等")
    st.caption("📊 数据来源：公众号抓取 + 工商信息")

# ===== 初始化聊天记录 =====
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "你好！我是聚变行业智能助手。你可以问我：\n\n- “星环聚能的最新融资情况？”\n- “有哪些机构投了托卡马克路线的企业？”\n- “中科创星投了哪些聚变公司？”\n\n请先在左侧输入 DeepSeek API Key 开始使用。"}
    ]

# ===== 显示历史消息 =====
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ===== 处理用户输入 =====
if prompt := st.chat_input("请输入你的问题..."):
    if not api_key:
        st.error("请先在左侧输入 DeepSeek API Key")
        st.stop()
    
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 调用大模型
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                # 连接数据库获取上下文
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 获取企业列表摘要
                cursor.execute("SELECT 企业名称, 技术路线, 最新融资轮次 FROM fusion_companies LIMIT 30")
                companies = cursor.fetchall()
                company_info = "\n".join([f"- {c[0]} | {c[1]} | {c[2]}" for c in companies])
                
                # 获取机构列表摘要
                cursor.execute("SELECT 管理机构名称, 已投聚变企业 FROM investors LIMIT 20")
                investors = cursor.fetchall()
                investor_info = "\n".join([f"- {i[0]} | 已投: {i[1]}" for i in investors])
                
                conn.close()
                
                # 构建提示词
                system_prompt = f"""你是一个专业的核聚变行业分析助手，可以帮助用户查询聚变企业和投资机构的信息。

当前数据库中的部分企业：
{company_info}

当前数据库中的部分投资机构：
{investor_info}

请根据用户的问题，结合上述数据库信息，给出准确、有帮助的回答。如果数据库中没有相关信息，可以根据你的公开知识补充，但要明确说明信息来源。"""
                
                # 调用 DeepSeek
                client = OpenAI(
                    api_key=api_key,
                    base_url='https://api.deepseek.com'
                )
                
                response = client.chat.completions.create(
                    model='deepseek-chat',
                    messages=[
                        {"role": "system", "content": system_prompt},
                        *st.session_state.messages[-5:]  # 最近5轮对话
                    ],
                    temperature=0.3,
                    max_tokens=2048
                )
                
                reply = response.choices[0].message.content
                st.markdown(reply)
                
                # 添加助手消息
                st.session_state.messages.append({"role": "assistant", "content": reply})
                
            except Exception as e:
                st.error(f"出错了：{e}")

# ===== 底部 =====
st.divider()
st.caption("⚡ 聚变行业智能助手 v1.0 | 数据来源：微信公众号 + 工商信息 | 模型：DeepSeek")
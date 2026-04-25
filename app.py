"""
同频心智助手 V2
主应用 - Streamlit 界面
六页面导航：下达指令 / 状态解读 / 任务规划 / 岗位适配 / 员工管理 / 设置
"""

import streamlit as st
import streamlit.components.v1 as components
import html
import os
from datetime import datetime, timedelta
from data_manager import DataManager, ConversationManager
from api_client import APIClient, parse_card_data, parse_task_sequence, parse_job_fit_report
from mock_data import (
    find_mock_response, get_default_mock_response,
    find_mock_task_sequence, get_default_mock_task_sequence,
    find_mock_job_fit_report, get_default_mock_job_fit_report,
)
from prompts import (
    DEFAULT_PARAMS, SCENARIO_PRESETS,
    build_decompose_prompt, build_job_fit_prompt,
    build_user_message, calculate_overall_score, SCORE_WEIGHTS,
)


# ============================================================
# UI 配色方案（温暖专业风）
# ============================================================

COLORS = {
    "primary": "#4A6FA5",      # 沉稳蓝
    "success": "#6B8F71",      # 自然绿
    "warning": "#E8845C",      # 暖橙色
    "bg": "#F8F6F3",           # 暖白背景
    "card": "#FFFFFF",         # 纯白卡片
    "text": "#2D3436",         # 深灰文字
    "border": "#E0E0E0",       # 边框
    "forward_bg": "#E3F2FD",   # 下达指令消息背景
    "reverse_bg": "#FFF3E0",   # 状态解读消息背景
}

# 障碍类型中文映射（全局使用）
DISABILITY_TYPE_CN = {
    "ASD": "孤独症谱系障碍",
    "ID": "智力障碍",
    "DS": "唐氏综合征",
    "CP": "脑性瘫痪",
    "ADHD": "注意力缺陷多动障碍",
}


# ============================================================
# 页面配置
# ============================================================

st.set_page_config(
    page_title="同频心智助手",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 自定义 CSS
# ============================================================

st.markdown("""
<style>
    /* 隐藏 Streamlit 默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 全局背景色 */
    .stApp {background-color: #F8F6F3;}

    /* 侧边栏样式 */
    [data-testid="stSidebar"] {background-color: #FFFFFF;}

    /* 按钮全宽 */
    .stButton > button {width: 100%;}

    /* 卡片圆角 */
    .stDataFrame {border-radius: 12px;}

    /* 侧边栏导航 radio 样式 */
    [data-testid="stSidebar"] .stRadio label {
        font-size: 15px;
        padding: 8px 0;
    }

    /* 侧边栏分割线 */
    [data-testid="stSidebar"] hr {
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# Session State 初始化
# ============================================================

def init_session_state():
    """初始化 Session State"""
    if "data_manager" not in st.session_state:
        st.session_state.data_manager = DataManager(".")

    if "api_client" not in st.session_state:
        st.session_state.api_client = APIClient(st.session_state.data_manager)

    # 从环境变量 / Streamlit Secrets 读取 API 配置
    env_api_key = os.environ.get("OPENAI_API_KEY", "")
    env_api_base = os.environ.get("OPENAI_API_BASE", "")
    env_model = os.environ.get("OPENAI_MODEL", "")

    if env_api_key:
        # 部署模式：直接使用环境变量，不写入本地文件
        st.session_state.data_manager.save_config(
            api_base_url=env_api_base or "https://api.openai.com/v1",
            api_key=env_api_key,
            model=env_model or "gpt-4o",
        )

    if "conversation" not in st.session_state:
        st.session_state.conversation = ConversationManager()

    if "api_status" not in st.session_state:
        st.session_state.api_status = "unknown"

    if "show_visual_dialog" not in st.session_state:
        st.session_state.show_visual_dialog = False

    if "visual_dialog_data" not in st.session_state:
        st.session_state.visual_dialog_data = None

    if "editing_employee" not in st.session_state:
        st.session_state.editing_employee = False

    if "editing_employee_id" not in st.session_state:
        st.session_state.editing_employee_id = None

    if "show_help" not in st.session_state:
        st.session_state.show_help = False

    if "show_alert" not in st.session_state:
        st.session_state.show_alert = False

    if "current_page" not in st.session_state:
        st.session_state.current_page = "forward"

    if "task_sequence" not in st.session_state:
        st.session_state.task_sequence = None

    if "task_start_time" not in st.session_state:
        st.session_state.task_start_time = None

    if "job_fit_report" not in st.session_state:
        st.session_state.job_fit_report = None

    if "task_current_index" not in st.session_state:
        st.session_state.task_current_index = 0

    if "show_task_fullscreen" not in st.session_state:
        st.session_state.show_task_fullscreen = False

    if "fullscreen_task_data" not in st.session_state:
        st.session_state.fullscreen_task_data = None

    if "disclaimer_accepted_date" not in st.session_state:
        st.session_state.disclaimer_accepted_date = None

init_session_state()


# ============================================================
# 免责声明
# ============================================================

DISCLAIMER_TEXT = """**⚠️ 免责声明**

本系统（同频心智助手）仅为辅助工具，旨在帮助主管更好地与心智障碍员工沟通。系统生成的所有指令、建议和评估报告仅供参考，不构成任何专业医疗、心理或教育诊断意见。

请主管根据员工的实际情况，结合专业特教人员的指导，审慎使用本系统的输出内容。对于因使用本系统而产生的任何直接或间接后果，本系统不承担责任。"""


def show_disclaimer_dialog():
    """每日首次进入时弹出免责声明"""
    from datetime import date
    today = date.today().isoformat()
    if st.session_state.disclaimer_accepted_date == today:
        return

    st.markdown("---")
    st.warning(DISCLAIMER_TEXT, icon="⚠️")
    if st.button("✅ 我已了解，继续使用", type="primary", key="disclaimer_accept_btn"):
        st.session_state.disclaimer_accepted_date = today
        st.rerun()


# ============================================================
# 辅助函数
# ============================================================

def get_current_employee():
    """获取当前员工画像"""
    return st.session_state.data_manager.get_current_employee()

def get_current_supervisor():
    """获取当前主管"""
    return st.session_state.data_manager.get_current_supervisor()

def check_api_status():
    """检查 API 连接状态（带 30 秒缓存）
    注意：部署迁移时，如果 API 地址变更，需清除缓存或等待 30 秒后自动刷新。
    """
    api_key = st.session_state.data_manager.get_api_key()
    if not api_key:
        return "not_configured"

    import time
    now = time.time()
    last_check = st.session_state.get("api_last_check_time", 0)
    cached_status = st.session_state.get("api_cached_status", None)

    if cached_status and (now - last_check) < 30:
        return cached_status

    success, _ = st.session_state.api_client.test_connection()
    status = "connected" if success else "error"

    st.session_state.api_last_check_time = now
    st.session_state.api_cached_status = status

    return status

def render_api_status():
    """渲染 API 状态指示器"""
    status = check_api_status()

    if status == "not_configured":
        st.markdown("🟡 **API 未配置**")
    elif status == "connected":
        st.markdown("🟢 **API 已连接**")
    else:
        st.markdown("🔴 **API 连接失败**")

    return status


# ============================================================
# HTML 渲染
# ============================================================

def render_html(html_content: str, height: int = None):
    """使用 components.html 渲染 HTML，确保样式生效"""
    if height is None:
        line_count = html_content.count('\n') + 1
        height = max(100, min(line_count * 20, 800))
    components.html(f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 0;">
        {html_content}
    </div>
    """, height=height, scrolling=False)


# ============================================================
# 卡片渲染函数
# ============================================================

def render_script_card(data: dict):
    """渲染提词剧本卡"""
    script = html.escape(data.get("script", ""))
    wait_reminder = html.escape(data.get("wait_reminder", ""))
    render_html(f"""
    <div style="background-color: #E8F5E9; padding: 20px; border-radius: 16px; margin: 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
        <h3 style="color: #2E7D32; margin-top: 0;">📢 提词剧本</h3>
        <p style="font-size: 18px; line-height: 1.8;">{script}</p>
        <p style="color: #E65100; font-weight: bold;">{wait_reminder}</p>
    </div>
    """)

def render_visual_card(data: dict):
    """渲染视觉步骤卡"""
    steps = data.get("steps", [])
    icons = data.get("visual_icons", [])

    if not steps:
        return

    steps_html = ""
    for i, step in enumerate(steps):
        icon = icons[i] if i < len(icons) else "•"
        safe_step = html.escape(step)
        steps_html += f"""
        <div style="display: inline-block; text-align: center; margin: 10px; padding: 15px; background: white; border-radius: 16px; min-width: 100px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <div style="font-size: 36px;">{icon}</div>
            <div style="font-size: 14px; margin-top: 5px;">{safe_step}</div>
        </div>
        """

    render_html(f"""
    <div style="background-color: #FFFDE7; padding: 20px; border-radius: 16px; margin: 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
        <h3 style="color: #F57F17; margin-top: 0;">📋 视觉步骤卡</h3>
        <div style="text-align: center;">
            {steps_html}
        </div>
        <p style="color: #E65100; font-weight: bold; text-align: center;">{data.get('wait_reminder', '')}</p>
    </div>
    """)

    if st.button("🔍 放大展示给员工看", key=f"enlarge_{id(data)}"):
        st.session_state.visual_dialog_data = data
        st.session_state.show_visual_dialog = True

def render_fba_card(data: dict):
    """渲染 FBA 解码卡"""
    fba_abc = data.get("fba_abc")
    if not isinstance(fba_abc, dict):
        fba_abc = {}
    seat_label = data.get("seat_label", "")
    seat_reasoning = html.escape(data.get("seat_reasoning", ""))
    intervention = html.escape(data.get("intervention", ""))
    forbidden = data.get("forbidden_responses") or []
    if isinstance(forbidden, str):
        forbidden = [forbidden]
    forbidden = [html.escape(f) for f in forbidden]

    seat_descriptions = {
        "S": "感官超载", "E": "逃避", "A": "寻求关注", "T": "获取实物",
    }
    seat_desc = seat_descriptions.get(seat_label, "未知")

    seat_colors = {
        "S": "#E91E63", "E": "#FF9800", "A": "#2196F3", "T": "#4CAF50",
    }
    seat_color = seat_colors.get(seat_label, "#9E9E9E")

    render_html(f"""
    <div style="background-color: #F3E5F5; padding: 20px; border-radius: 16px; margin: 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
        <h3 style="color: #7B1FA2; margin-top: 0;">🔍 FBA 行为解码</h3>

        <div style="background: white; padding: 15px; border-radius: 12px; margin: 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <p style="margin: 5px 0;"><strong>行为动机：</strong>
                <span style="background-color: {seat_color}; color: white; padding: 3px 10px; border-radius: 15px; font-weight: bold;">
                    {seat_label} ({seat_desc})
                </span>
            </p>
            {f'<p style="margin: 5px 0; color: #666; font-style: italic;">{seat_reasoning}</p>' if seat_reasoning else ''}
        </div>

        <div style="background: white; padding: 15px; border-radius: 12px; margin: 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <p style="margin: 5px 0;"><strong>A（前因）：</strong>{html.escape(fba_abc.get('antecedent', ''))}</p>
            <p style="margin: 5px 0;"><strong>B（行为）：</strong>{html.escape(fba_abc.get('behavior', ''))}</p>
            <p style="margin: 5px 0;"><strong>C（后果）：</strong>{html.escape(fba_abc.get('consequence', ''))}</p>
        </div>

        <div style="background: #E8F5E9; padding: 15px; border-radius: 12px; margin: 10px 0;">
            <p style="margin: 5px 0;"><strong>💡 干预建议：</strong></p>
            <p style="margin: 5px 0;">{intervention}</p>
        </div>

        <div style="background: #FFEBEE; padding: 15px; border-radius: 12px; margin: 10px 0;">
            <p style="margin: 5px 0; color: #C62828;"><strong>🚫 禁忌话术：</strong></p>
            <p style="margin: 5px 0; color: #C62828;">{' ✗ '.join(forbidden) if forbidden else '无'}</p>
        </div>
    </div>
    """)

def render_alert_card(level: str = "warning"):
    """渲染认知负荷警报卡"""
    if level == "critical":
        bg_color = "#FFCDD2"
        border_color = "#C62828"
        title = "🚨 CRITICAL 认知负荷警报"
        message = """
        员工可能处于认知超载临界状态！

        **建议：**
        1. 立即停止下达新指令
        2. 引导员工离开当前工位休息
        3. 10分钟后用最简单的单步指令重新开始
        """
    else:
        bg_color = "#FFF9C4"
        border_color = "#F57F17"
        title = "⚠️ WARNING 认知负荷警报"
        message = """
        已连续多轮互动未获有效响应。
        员工可能处于认知超载状态。

        **建议：**
        - 暂停当前任务
        - 观察员工状态
        - 准备降级到更简单的任务
        """

    render_html(f"""
    <div style="background-color: {bg_color}; border: 3px solid {border_color}; padding: 20px; border-radius: 16px; margin: 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
        <h3 style="color: {border_color}; margin-top: 0;">{title}</h3>
        <div style="font-size: 16px; line-height: 1.8;">
            {message}
        </div>
    </div>
    """)

def render_insufficient_card(data: dict):
    """渲染信息不足提示卡"""
    reason = html.escape(data.get("insufficient_reason", "信息不足，无法生成指令"))

    render_html(f"""
    <div style="background-color: #F5F5F5; border: 2px dashed #9E9E9E; padding: 20px; border-radius: 16px; margin: 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
        <h3 style="color: #616161; margin-top: 0;">⚠️ 信息不足</h3>
        <div style="font-size: 16px; line-height: 1.8;">
            {reason}
        </div>
    </div>
    """)

def render_type_specific_fields(data: dict):
    """渲染障碍类型专用字段"""
    # === ID 专用字段 ===
    if data.get("encouragement"):
        render_html(f"""
        <div style="background-color: #E8F5E9; padding: 12px; border-radius: 12px; margin: 8px 0;">
            <strong>💬 鼓励话语：</strong>{html.escape(data['encouragement'])}
        </div>
        """)
    if data.get("anchor_sentence"):
        render_html(f"""
        <div style="background-color: #E3F2FD; padding: 12px; border-radius: 12px; margin: 8px 0;">
            <strong>📌 泛化锚定句：</strong>{html.escape(data['anchor_sentence'])}
        </div>
        """)
    if data.get("fallback_task"):
        render_html(f"""
        <div style="background-color: #FFF3E0; padding: 12px; border-radius: 12px; margin: 8px 0;">
            <strong>🔙 退回任务：</strong>{html.escape(data['fallback_task'])}
        </div>
        """)

    # === DS 专用字段 ===
    if data.get("opening_encouragement"):
        render_html(f"""
        <div style="background-color: #FCE4EC; padding: 12px; border-radius: 12px; margin: 8px 0;">
            <strong>🌟 热身鼓励：</strong>{html.escape(data['opening_encouragement'])}
        </div>
        """)
    if data.get("step_encouragements"):
        enc_list = data["step_encouragements"]
        if isinstance(enc_list, list):
            enc_html = "".join(f"<li>{html.escape(e)}</li>" for e in enc_list if e)
            render_html(f"""
            <div style="background-color: #F3E5F5; padding: 12px; border-radius: 12px; margin: 8px 0;">
                <strong>👏 步骤鼓励：</strong>
                <ul style="margin: 5px 0 0 20px;">{enc_html}</ul>
            </div>
            """)
    if data.get("closing_encouragement"):
        render_html(f"""
        <div style="background-color: #E8F5E9; padding: 12px; border-radius: 12px; margin: 8px 0;">
            <strong>🎉 完成鼓励：</strong>{html.escape(data['closing_encouragement'])}
        </div>
        """)
    if data.get("fatigue_warning"):
        st.warning(f"😴 疲劳预警：{html.escape(data['fatigue_warning'])}")
    if data.get("emotional_acknowledgment"):
        render_html(f"""
        <div style="background-color: #E3F2FD; padding: 12px; border-radius: 12px; margin: 8px 0;">
            <strong>💝 情感确认：</strong>{html.escape(data['emotional_acknowledgment'])}
        </div>
        """)

    # === CP 专用字段 ===
    if data.get("confirmation_method"):
        render_html(f"""
        <div style="background-color: #E0F7FA; padding: 12px; border-radius: 12px; margin: 8px 0;">
            <strong>✅ 确认方式：</strong>{html.escape(data['confirmation_method'])}
        </div>
        """)
    if data.get("mobility_note"):
        render_html(f"""
        <div style="background-color: #FFF8E1; padding: 12px; border-radius: 12px; margin: 8px 0;">
            <strong>♿ 运动辅助提示：</strong>{html.escape(data['mobility_note'])}
        </div>
        """)
    if data.get("rest_prompt"):
        render_html(f"""
        <div style="background-color: #E8F5E9; padding: 12px; border-radius: 12px; margin: 8px 0;">
            <strong>☕ 休息选项：</strong>{html.escape(data['rest_prompt'])}
        </div>
        """)
    if data.get("physical_check"):
        render_html(f"""
        <div style="background-color: #FFEBEE; padding: 12px; border-radius: 12px; margin: 8px 0;">
            <strong>🏥 身体排查：</strong>{html.escape(data['physical_check'])}
        </div>
        """)
    if data.get("aac_check"):
        render_html(f"""
        <div style="background-color: #FFF3E0; padding: 12px; border-radius: 12px; margin: 8px 0;">
            <strong>🗣️ AAC检查：</strong>{html.escape(data['aac_check'])}
        </div>
        """)

    # === ADHD 专用字段 ===
    if data.get("timer_anchor"):
        render_html(f"""
        <div style="background-color: #E3F2FD; padding: 12px; border-radius: 12px; margin: 8px 0;">
            <strong>⏱️ 时间锚点：</strong>{html.escape(data['timer_anchor'])}
        </div>
        """)
    if data.get("dopamine_reward"):
        render_html(f"""
        <div style="background-color: #FCE4EC; padding: 12px; border-radius: 12px; margin: 8px 0;">
            <strong>🎮 阶段激励：</strong>{html.escape(data['dopamine_reward'])}
        </div>
        """)

def render_card(data: dict):
    """根据类型渲染卡片"""
    card_type = data.get("type", "forward")

    if card_type == "insufficient_info":
        render_insufficient_card(data)
    elif card_type == "forward":
        if data.get("sensory_warning"):
            st.warning(f"⚠️ 感官预警：{data.get('sensory_warning')}")
        render_script_card(data)
        render_visual_card(data)
        render_type_specific_fields(data)
    elif card_type == "reverse_fba":
        render_fba_card(data)
        render_type_specific_fields(data)
    elif card_type == "reverse_alert":
        render_alert_card("critical")


# ============================================================
# 视觉步骤卡放大对话框
# ============================================================

def show_visual_dialog():
    """显示放大的视觉步骤卡"""
    data = st.session_state.visual_dialog_data
    if not data:
        st.write("无数据")
        return

    steps = data.get("steps") or []
    icons = data.get("visual_icons") or []

    if not steps:
        st.write("无步骤数据")
        return

    cols = st.columns(len(steps) if steps else 1)
    for i, col in enumerate(cols):
        with col:
            icon = icons[i] if i < len(icons) else "•"
            safe_step = html.escape(steps[i])
            render_html(f"""
            <div style="text-align: center; padding: 30px;">
                <div style="font-size: 72px;">{icon}</div>
                <div style="font-size: 24px; font-weight: bold; margin-top: 20px;">{safe_step}</div>
            </div>
            """, height=200)

    st.markdown("---")
    render_html(f"<div style='text-align: center; font-size: 20px; color: #E65100;'>{html.escape(data.get('wait_reminder', ''))}</div>", height=50)

    if st.button("关闭", type="primary"):
        st.session_state.show_visual_dialog = False
        st.session_state.visual_dialog_data = None
        st.rerun()


# ============================================================
# 员工表单
# ============================================================

def render_employee_form(supervisor_id: str, employee_data: dict = None):
    """渲染员工画像表单
    Args:
        supervisor_id: 主管ID
        employee_data: 要编辑的员工数据，None表示新建（空表）
    """
    is_editing = employee_data is not None

    if "form_version" not in st.session_state:
        st.session_state.form_version = 0
    fv = st.session_state.form_version

    # 标题
    if is_editing:
        st.markdown(f"#### ✏️ 编辑员工：{employee_data.get('name', '')}")
    else:
        st.markdown("#### ➕ 新建员工")

    default_type = employee_data.get("disability_type", "ASD") if employee_data else "ASD"
    type_defaults = DEFAULT_PARAMS.get(default_type, {})

    # 障碍类型选项（显示带中文说明，存储用英文缩写）
    DISABILITY_TYPE_OPTIONS = ["ASD", "ID", "DS", "CP", "ADHD"]
    DISABILITY_TYPE_LABELS = {
        "ASD": "ASD - 孤独症谱系障碍",
        "ID": "ID - 智力障碍",
        "DS": "DS - 唐氏综合征",
        "CP": "CP - 脑性瘫痪",
        "ADHD": "ADHD - 注意力缺陷多动障碍",
    }

    name = st.text_input("员工姓名", value=employee_data.get("name", "") if employee_data else "", key=f"ef_name_v{fv}")
    disability_type = st.selectbox("障碍类型",
        options=DISABILITY_TYPE_OPTIONS,
        format_func=lambda x: DISABILITY_TYPE_LABELS.get(x, x),
        index=DISABILITY_TYPE_OPTIONS.index(default_type),
        key=f"ef_dtype_v{fv}")

    type_defaults = DEFAULT_PARAMS.get(disability_type, {})

    working_memory = st.slider("工作记忆步数", min_value=1, max_value=5,
        value=employee_data.get("working_memory", type_defaults.get("working_memory", 2)) if employee_data else type_defaults.get("working_memory", 2),
        key=f"ef_wm_v{fv}")
    triggers = st.text_area("感官/情绪触发词（逗号分隔）",
        value=employee_data.get("triggers", type_defaults.get("triggers", "")) if employee_data else type_defaults.get("triggers", ""),
        key=f"ef_triggers_v{fv}")

    comm_pref_options = ["纯图像", "图文结合", "口语"]
    comm_preference = st.selectbox("沟通偏好", options=comm_pref_options,
        index=comm_pref_options.index(employee_data.get("comm_preference", type_defaults.get("comm_preference", "图文结合"))) if employee_data else comm_pref_options.index(type_defaults.get("comm_preference", "图文结合")),
        key=f"ef_comm_v{fv}")

    scenario = st.selectbox("工作场景", options=list(SCENARIO_PRESETS.keys()),
        index=list(SCENARIO_PRESETS.keys()).index(employee_data.get("scenario", "超市理货")) if employee_data and employee_data.get("scenario") in SCENARIO_PRESETS else 0,
        key=f"ef_scenario_v{fv}")

    custom_scenario = ""
    if scenario == "自定义":
        custom_scenario = st.text_area("自定义场景描述",
            value=employee_data.get("custom_scenario", "") if employee_data else "",
            key=f"ef_custom_scenario_v{fv}")

    wait_time = st.slider("建议等待时间（秒）", min_value=3, max_value=20,
        value=employee_data.get("wait_time", type_defaults.get("wait_time", 5)) if employee_data else type_defaults.get("wait_time", 5),
        key=f"ef_wait_v{fv}")

    output_mode_options = ["自动", "提词为主", "视觉为主", "极简模式"]
    output_mode = st.selectbox("输出模式", options=output_mode_options,
        index=output_mode_options.index(employee_data.get("output_mode", type_defaults.get("output_mode", "自动"))) if employee_data else output_mode_options.index(type_defaults.get("output_mode", "自动")),
        key=f"ef_output_v{fv}")

    notes = st.text_area("备注",
        value=employee_data.get("notes", "") if employee_data else "",
        key=f"ef_notes_v{fv}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 保存", key="ef_save_btn", width="stretch"):
            final_scenario = custom_scenario if (scenario == "自定义" and custom_scenario.strip()) else scenario
            employee_data_new = {
                "name": name, "disability_type": disability_type,
                "working_memory": working_memory, "triggers": triggers,
                "comm_preference": comm_preference, "scenario": final_scenario,
                "wait_time": wait_time, "output_mode": output_mode, "notes": notes,
            }
            if not name.strip():
                st.error("请输入员工姓名")
                return

            if is_editing:
                st.session_state.data_manager.update_employee(supervisor_id, employee_data["id"], employee_data_new)
                st.success(f"✅ 员工「{name}」的画像已更新！")
            else:
                st.session_state.data_manager.create_employee(supervisor_id, employee_data_new)
                st.success(f"✅ 新员工「{name}」创建成功！")

            st.session_state.editing_employee = False
            st.session_state.editing_employee_id = None
            st.session_state.form_version += 1
            st.rerun()

    with col2:
        if is_editing:
            if st.button("❌ 取消编辑", key="ef_cancel_btn", width="stretch"):
                st.session_state.editing_employee = False
                st.session_state.editing_employee_id = None
                st.session_state.form_version += 1
                st.rerun()


# ============================================================
# 侧边栏
# ============================================================

def render_sidebar():
    """渲染侧边栏（品牌标题 + 导航 + 员工切换 + Demo 开关）"""
    with st.sidebar:
        # 品牌标题
        st.markdown("# 🧠 同频心智助手")
        st.markdown("---")

        # 导航 radio
        page_options = {
            "forward": "📋 下达指令",
            "reverse": "🔍 状态解读",
            "decompose": "📅 任务规划",
            "job_fit": "📊 岗位适配",
            "manage": "👤 员工管理",
            "settings": "⚙️ 设置",
        }

        selected_label = st.radio(
            "功能导航",
            options=list(page_options.values()),
            index=list(page_options.values()).index(
                page_options.get(st.session_state.current_page, page_options["forward"])
            ),
            key="nav_radio",
        )

        # 映射 label -> key
        label_to_key = {v: k for k, v in page_options.items()}
        new_page = label_to_key.get(selected_label, "forward")
        if new_page != st.session_state.current_page:
            st.session_state.current_page = new_page
            st.rerun()

        st.markdown("---")

        # 当前员工快速切换
        current_supervisor = get_current_supervisor()
        if current_supervisor:
            employees = st.session_state.data_manager.get_employees(current_supervisor["id"])
            if employees:
                current_employee = get_current_employee()
                employee_map = {
                    eid: f"{e['name']}({e['disability_type']}·{e.get('scenario', '')})"
                    for eid, e in employees.items()
                }
                current_eid = current_employee["id"] if current_employee else None
                current_eidx = list(employee_map.keys()).index(current_eid) if current_eid in employee_map else 0

                selected_eid = st.selectbox(
                    "当前员工",
                    options=list(employee_map.keys()),
                    format_func=lambda x: employee_map[x],
                    index=current_eidx,
                    key="sidebar_employee_select",
                )

                if selected_eid != current_eid:
                    st.session_state.data_manager.set_current_employee(current_supervisor["id"], selected_eid)
                    st.session_state.conversation.clear()
                    st.rerun()
            else:
                st.info("暂无员工，请在「员工管理」中创建")
        else:
            st.info("暂无主管，请在「员工管理」中创建")

        st.markdown("---")

        # API 状态灯
        status = check_api_status()
        status_config = {
            "connected": ("🟢", "API 已连接"),
            "not_configured": ("🟡", "API 未配置"),
            "error": ("🔴", "API 连接失败"),
            "unknown": ("⚪", "API 未检测"),
        }
        icon, label = status_config.get(status, status_config["unknown"])
        st.markdown(f"{icon} **{label}**")

        st.markdown("---")

        # 帮助按钮
        if st.button("❓ 使用帮助", key="help_btn", width="stretch"):
            st.session_state.show_help = not st.session_state.get("show_help", False)

        if st.session_state.get("show_help", False):
            with st.expander("📖 使用指南", expanded=True):
                st.markdown("""
##### 🔑 使用前准备
1. 进入「⚙️ 设置」页面
2. 输入 API 地址和 API Key
3. 点击「测试连接」确认可用
4. 点击「保存配置」

> 系统会优先读取环境变量中的 API 配置。如果环境变量未配置或连接失败，请在设置页面手动输入。

##### 📋 快速开始
1. 进入「👤 员工管理」创建主管账户
2. 为主管添加员工，填写员工画像
3. 在左侧栏切换员工
4. 使用「下达指令」向员工传达工作指令
5. 使用「状态解读」分析员工行为

##### 📅 任务规划
输入一个完整的工作任务（如"今天负责饮料区上货"），系统会自动拆解为分步任务序列。

##### 📊 岗位适配
输入目标岗位信息，系统会评估员工与岗位的匹配程度，生成入职支持建议。

##### 💡 使用技巧
- **下达指令**：输入日常口语化的指令，AI 会翻译为适合员工的版本
- **状态解读**：描述员工的具体行为（如"员工突然捂住耳朵蹲下"），AI 会进行 FBA 行为分析
- **任务规划**：建议从短时长（60-120分钟）开始，逐步增加
        """)

        # 免责声明常驻入口
        st.markdown("---")
        with st.expander("⚠️ 免责声明"):
            st.markdown(DISCLAIMER_TEXT)


# ============================================================
# 页面1: 下达指令 (forward)
# ============================================================

def render_forward_page():
    """向员工下达指令页面"""
    current_employee = get_current_employee()
    if not current_employee:
        st.info("请先在侧边栏选择或创建员工")
        return

    # 顶部：当前员工信息栏
    render_html(f"""
    <div style="background-color: {COLORS['card']}; padding: 16px 24px; border-radius: 16px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); display: flex; align-items: center; gap: 20px;">
        <div style="font-size: 32px;">🧑‍💼</div>
        <div>
            <div style="font-size: 18px; font-weight: bold; color: {COLORS['text']};">{html.escape(current_employee.get('name', ''))}</div>
            <div style="font-size: 14px; color: #666;">
                障碍类型：<strong>{html.escape(current_employee.get('disability_type', ''))} - {html.escape(DISABILITY_TYPE_CN.get(current_employee.get('disability_type', ''), ''))}</strong>
                &nbsp;|&nbsp;
                场景：<strong>{html.escape(current_employee.get('scenario', ''))}</strong>
                &nbsp;|&nbsp;
                工作记忆：<strong>{current_employee.get('working_memory', 2)}步</strong>
            </div>
        </div>
        <div style="margin-left: auto; background-color: {COLORS['forward_bg']}; padding: 6px 16px; border-radius: 20px; font-size: 13px; color: {COLORS['primary']}; font-weight: bold;">
            📋 向员工下达指令
        </div>
    </div>
    """, height=80)

    # 对话历史
    messages = st.session_state.conversation.get_messages()

    if st.session_state.conversation.truncated:
        render_html("""
        <div style="text-align: center; padding: 8px; color: #999; font-size: 13px; border-bottom: 1px dashed #ddd; margin-bottom: 15px;">
            ⏪ 较早的对话记录已自动清理（保留最近20轮）
        </div>
        """, height=40)

    if not messages:
        render_html("""
        <div style="text-align: center; padding: 50px; color: #888;">
            <div style="font-size: 48px;">💬</div>
            <div style="font-size: 18px; margin-top: 20px;">开始下达指令</div>
            <div style="font-size: 14px; margin-top: 10px;">输入您要对员工说的指令，AI 将自动翻译为适配版本</div>
        </div>
        """, height=200)
    else:
        for i, msg in enumerate(messages):
            if msg["role"] == "user":
                msg_mode = msg.get("mode", "forward")
                if msg_mode == "forward":
                    mode_label = "向员工下达指令"
                    bg_color = COLORS["forward_bg"]
                else:
                    mode_label = "员工状态解读"
                    bg_color = COLORS["reverse_bg"]

                render_html(f"""
                <div style="background-color: {bg_color}; padding: 15px; border-radius: 16px; margin: 10px 0; max-width: 70%; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                    <div style="font-size: 12px; color: #666;">主管 · {mode_label}</div>
                    <div style="font-size: 16px; margin-top: 5px;">{html.escape(msg['content'])}</div>
                </div>
                """, height=80)
            else:
                card_data = msg.get("card_data", {})
                if card_data:
                    render_card(card_data)

    # 检查是否需要显示警报
    alert_level = st.session_state.conversation.check_alert_level()
    if alert_level in ["warning", "critical"] or st.session_state.show_alert:
        render_alert_card("critical" if alert_level == "critical" else "warning")
        if st.button("关闭警报", key="dismiss_alert"):
            st.session_state.show_alert = False
            st.rerun()

    # 视觉步骤卡对话框
    if st.session_state.show_visual_dialog and st.session_state.visual_dialog_data:
        st.markdown("---")
        st.subheader("📋 视觉步骤卡 - 全屏展示")
        show_visual_dialog()

    # 底部输入栏
    st.markdown("---")
    col_input, col_btn = st.columns([6, 1])
    with col_input:
        user_input = st.text_input(
            "输入指令",
            placeholder="请输入您要对员工说的指令...",
            key="forward_input",
            label_visibility="collapsed",
        )
    with col_btn:
        send_clicked = st.button("📤 发送", type="primary", key="forward_send_btn")

    # 处理发送
    if send_clicked and user_input.strip():
        _handle_send_message(user_input.strip(), "forward")


# ============================================================
# 页面2: 状态解读 (reverse)
# ============================================================

def render_reverse_page():
    """员工状态解读页面"""
    current_employee = get_current_employee()
    if not current_employee:
        st.info("请先在侧边栏选择或创建员工")
        return

    # 顶部：当前员工信息栏
    render_html(f"""
    <div style="background-color: {COLORS['card']}; padding: 16px 24px; border-radius: 16px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); display: flex; align-items: center; gap: 20px;">
        <div style="font-size: 32px;">🧑‍💼</div>
        <div>
            <div style="font-size: 18px; font-weight: bold; color: {COLORS['text']};">{html.escape(current_employee.get('name', ''))}</div>
            <div style="font-size: 14px; color: #666;">
                障碍类型：<strong>{html.escape(current_employee.get('disability_type', ''))} - {html.escape(DISABILITY_TYPE_CN.get(current_employee.get('disability_type', ''), ''))}</strong>
                &nbsp;|&nbsp;
                场景：<strong>{html.escape(current_employee.get('scenario', ''))}</strong>
                &nbsp;|&nbsp;
                工作记忆：<strong>{current_employee.get('working_memory', 2)}步</strong>
            </div>
        </div>
        <div style="margin-left: auto; background-color: {COLORS['reverse_bg']}; padding: 6px 16px; border-radius: 20px; font-size: 13px; color: {COLORS['warning']}; font-weight: bold;">
            🔍 员工状态解读
        </div>
    </div>
    """, height=80)

    # 对话历史
    messages = st.session_state.conversation.get_messages()

    if st.session_state.conversation.truncated:
        render_html("""
        <div style="text-align: center; padding: 8px; color: #999; font-size: 13px; border-bottom: 1px dashed #ddd; margin-bottom: 15px;">
            ⏪ 较早的对话记录已自动清理（保留最近20轮）
        </div>
        """, height=40)

    if not messages:
        render_html("""
        <div style="text-align: center; padding: 50px; color: #888;">
            <div style="font-size: 48px;">🔍</div>
            <div style="font-size: 18px; margin-top: 20px;">开始状态解读</div>
            <div style="font-size: 14px; margin-top: 10px;">描述员工的行为表现，AI 将进行 FBA 行为解码</div>
        </div>
        """, height=200)
    else:
        for i, msg in enumerate(messages):
            if msg["role"] == "user":
                msg_mode = msg.get("mode", "forward")
                if msg_mode == "forward":
                    mode_label = "向员工下达指令"
                    bg_color = COLORS["forward_bg"]
                else:
                    mode_label = "员工状态解读"
                    bg_color = COLORS["reverse_bg"]

                render_html(f"""
                <div style="background-color: {bg_color}; padding: 15px; border-radius: 16px; margin: 10px 0; max-width: 70%; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                    <div style="font-size: 12px; color: #666;">主管 · {mode_label}</div>
                    <div style="font-size: 16px; margin-top: 5px;">{html.escape(msg['content'])}</div>
                </div>
                """, height=80)
            else:
                card_data = msg.get("card_data", {})
                if card_data:
                    render_card(card_data)

    # 检查是否需要显示警报
    alert_level = st.session_state.conversation.check_alert_level()
    if alert_level in ["warning", "critical"] or st.session_state.show_alert:
        render_alert_card("critical" if alert_level == "critical" else "warning")
        if st.button("关闭警报", key="dismiss_alert_reverse"):
            st.session_state.show_alert = False
            st.rerun()

    # 视觉步骤卡对话框
    if st.session_state.show_visual_dialog and st.session_state.visual_dialog_data:
        st.markdown("---")
        st.subheader("📋 视觉步骤卡 - 全屏展示")
        show_visual_dialog()

    # 底部输入栏
    st.markdown("---")
    col_input, col_btn = st.columns([6, 1])
    with col_input:
        user_input = st.text_input(
            "输入行为描述",
            placeholder="请描述员工的行为表现...",
            key="reverse_input",
            label_visibility="collapsed",
        )
    with col_btn:
        send_clicked = st.button("📤 发送", type="primary", key="reverse_send_btn")

    # 处理发送
    if send_clicked and user_input.strip():
        _handle_send_message(user_input.strip(), "reverse")


# ============================================================
# 消息发送公共逻辑
# ============================================================

def _handle_send_message(user_input: str, mode: str):
    """处理消息发送（先调API再添加消息到历史）"""
    current_employee = get_current_employee()
    if not current_employee:
        st.error("请先选择员工")
        return

    mode_label = "向员工下达指令" if mode == "forward" else "员工状态解读"
    error = None
    with st.spinner(f"🤖 {mode_label}中，请稍候..."):
        context = st.session_state.conversation.get_context_messages(max_turns=20)
        card_data, error = st.session_state.api_client.translate(
                employee=current_employee,
                user_input=user_input,
                mode=mode,
                context_messages=context,
            )

    if error:
        st.error(error)
        return

    # 添加用户消息（在 API 调用之后）
    st.session_state.conversation.add_message(
        role="user",
        content=user_input,
        mode=mode,
    )

    # 如果是逆向模式，增加计数器
    if mode == "reverse":
        st.session_state.conversation.increment_reverse_count()

    # 解析卡片数据
    card_data = parse_card_data(card_data)

    # 如果是逆向模式，检查 SEAT 标签
    if mode == "reverse" and card_data.get("seat_label"):
        st.session_state.conversation.increment_se_risk_count(card_data["seat_label"])

    # 添加 AI 响应
    st.session_state.conversation.add_message(
        role="assistant",
        content=card_data.get("title", ""),
        card_type=card_data.get("type"),
        card_data=card_data,
    )

    st.rerun()


# ============================================================
# 页面3: 任务规划 (decompose)
# ============================================================

def calculate_time_slots(tasks, start_time_str="09:00"):
    """根据开始时间和 duration_min 计算每个任务的 time_slot"""
    start = datetime.strptime(start_time_str, "%H:%M")
    for task in tasks:
        end = start + timedelta(minutes=task["duration_min"])
        task["time_slot"] = f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')}"
        start = end
    return tasks


def render_decompose_page():
    """任务规划页面"""
    current_employee = get_current_employee()
    if not current_employee:
        st.info("请先在侧边栏选择或创建员工")
        return

    # 顶部标题
    st.markdown("## 📅 任务分解器")
    st.markdown("根据员工的能力画像，将工作任务分解为可执行的步骤序列。")

    # 顶部：当前员工信息栏
    render_html(f"""
    <div style="background-color: {COLORS['card']}; padding: 16px 24px; border-radius: 16px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); display: flex; align-items: center; gap: 20px;">
        <div style="font-size: 32px;">🧑‍💼</div>
        <div>
            <div style="font-size: 18px; font-weight: bold; color: {COLORS['text']};">{html.escape(current_employee.get('name', ''))}</div>
            <div style="font-size: 14px; color: #666;">
                障碍类型：<strong>{html.escape(current_employee.get('disability_type', ''))} - {html.escape(DISABILITY_TYPE_CN.get(current_employee.get('disability_type', ''), ''))}</strong>
                &nbsp;|&nbsp;
                场景：<strong>{html.escape(current_employee.get('scenario', ''))}</strong>
                &nbsp;|&nbsp;
                工作记忆：<strong>{current_employee.get('working_memory', 2)}步</strong>
            </div>
        </div>
        <div style="margin-left: auto; background-color: #FFF3E0; padding: 6px 16px; border-radius: 20px; font-size: 13px; color: {COLORS['warning']}; font-weight: bold;">
            📅 任务规划
        </div>
    </div>
    """, height=80)

    # 输入区
    with st.container():
        task_description = st.text_area(
            "任务描述",
            placeholder="请描述今天需要完成的工作任务...",
            key="decompose_task_desc",
            height=100,
        )

        col1, col2 = st.columns(2)
        with col1:
            duration_min = st.slider(
                "工作时长（分钟）",
                min_value=60,
                max_value=480,
                value=120,
                step=30,
                key="decompose_duration",
            )
        with col2:
            include_break = st.checkbox(
                "包含休息时间",
                value=True,
                key="decompose_break",
            )

        generate_clicked = st.button("🚀 生成任务序列", type="primary", key="decompose_generate_btn")

    # 生成逻辑
    if generate_clicked and task_description.strip():
        with st.spinner("🤖 正在生成任务序列，请稍候..."):
            system_prompt = build_decompose_prompt(
                employee=current_employee,
                task_description=task_description,
                duration_min=duration_min,
                include_break=include_break,
            )
            task_list, error = st.session_state.api_client.decompose_task(
                employee=current_employee,
                task_description=task_description,
                duration_min=duration_min,
                include_break=include_break,
                system_prompt=system_prompt,
            )
            if error:
                st.error(error)
                return

        if task_list:
            # 计算时间段
            task_list = calculate_time_slots(task_list)
            st.session_state.task_sequence = task_list
            st.session_state.task_current_index = 0
            st.session_state.task_start_time = datetime.now().strftime("%H:%M")

            # 保存到数据文件
            current_supervisor = get_current_supervisor()
            if current_supervisor:
                st.session_state.data_manager.save_task_sequence(
                    current_supervisor["id"],
                    current_employee["id"],
                    {
                        "tasks": task_list,
                        "task_description": task_description,
                        "duration_min": duration_min,
                        "created_at": datetime.now().isoformat(),
                    },
                )

            st.rerun()

    # 输出区：展示任务序列
    if st.session_state.task_sequence:
        tasks = st.session_state.task_sequence
        current_idx = st.session_state.task_current_index
        total = len(tasks)
        completed = sum(1 for i, t in enumerate(tasks) if i < current_idx)

        st.markdown("---")
        st.markdown("### 📋 任务序列")

        # 进度条
        progress_ratio = completed / total if total > 0 else 0
        st.progress(progress_ratio, text=f"进度：{completed}/{total} 已完成")

        # 全屏展示模式
        if st.session_state.show_task_fullscreen and st.session_state.fullscreen_task_data:
            _render_task_fullscreen(st.session_state.fullscreen_task_data)
            return

        # 任务卡列表
        for i, task in enumerate(tasks):
            _render_task_card(task, i, current_idx)

        # 所有任务完成提示
        if current_idx >= total:
            st.success("🎉 所有任务已完成！")

        # 清除任务序列
        st.markdown("---")
        if st.button("🗑️ 清除任务序列", key="task_clear_btn"):
            st.session_state.task_sequence = None
            st.session_state.task_current_index = 0
            st.session_state.task_start_time = None
            st.session_state.show_task_fullscreen = False
            st.session_state.fullscreen_task_data = None
            st.rerun()


def _render_task_card(task, index, current_idx):
    """渲染单张任务卡"""
    is_break = task.get("is_break", False)

    # 状态判断
    if index < current_idx:
        status = "completed"
        bg_color = "#F5F5F5"
        text_style = "text-decoration: line-through; color: #999;"
    elif index == current_idx:
        status = "active"
        bg_color = "#E8F5E9"
        text_style = ""
    else:
        status = "pending"
        bg_color = "#FFFFFF"
        text_style = ""

    time_slot = task.get("time_slot", "")
    script = html.escape(task.get("script", ""))
    steps = task.get("steps", [])
    icons = task.get("visual_icons", [])
    confirmation = html.escape(task.get("confirmation", "")) if task.get("confirmation") else ""

    # 步骤 HTML
    steps_html = ""
    for j, step in enumerate(steps):
        icon = icons[j] if j < len(icons) else "•"
        steps_html += f"""
        <span style="display: inline-flex; align-items: center; margin: 4px 8px 4px 0; padding: 4px 12px; background: rgba(255,255,255,0.8); border-radius: 20px; font-size: 13px; {text_style}">
            {icon} {html.escape(step)}
        </span>
        """

    # 状态标签
    status_map = {
        "completed": ("✅ 已完成", "#6B8F71"),
        "active": ("▶ 执行中", "#4A6FA5"),
        "pending": ("⏳ 待执行", "#999"),
    }
    status_text, status_color = status_map.get(status, ("⏳ 待执行", "#999"))

    if is_break:
        status_text = "☕ 休息"
        status_color = "#FF9800"

    render_html(f"""
    <div style="background-color: {bg_color}; padding: 16px 20px; border-radius: 16px; margin: 8px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 4px solid {status_color};">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 20px; font-weight: bold; color: {status_color};">#{index + 1}</span>
                <span style="font-size: 13px; color: #666;">{time_slot}</span>
                <span style="background-color: {status_color}; color: white; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                    {status_text}
                </span>
            </div>
            <span style="font-size: 13px; color: #666;">{task.get('duration_min', 0)}分钟</span>
        </div>
        <div style="margin-top: 10px; font-size: 16px; line-height: 1.6; {text_style}">
            {script}
        </div>
        <div style="margin-top: 8px;">
            {steps_html}
        </div>
        {f'<div style="margin-top: 6px; font-size: 12px; color: #888;">确认方式：{confirmation}</div>' if confirmation else ''}
    </div>
    """, height=max(120, 60 + len(steps) * 30))

    # 仅对当前执行中的卡片显示操作按钮
    if index == current_idx:
        col_done, col_show = st.columns(2)
        with col_done:
            if st.button("✔ 标记完成", type="primary", key=f"task_done_{index}", width="stretch"):
                st.session_state.task_current_index = current_idx + 1
                st.rerun()
        with col_show:
            if st.button("🔍 展示给员工看", key=f"task_show_{index}", width="stretch"):
                st.session_state.fullscreen_task_data = task
                st.session_state.show_task_fullscreen = True
                st.rerun()


def _render_task_fullscreen(task):
    """全屏大字体展示当前任务给员工看"""
    script = html.escape(task.get("script", ""))
    steps = task.get("steps", [])
    icons = task.get("visual_icons", [])
    time_slot = task.get("time_slot", "")

    steps_html = ""
    for j, step in enumerate(steps):
        icon = icons[j] if j < len(icons) else "•"
        steps_html += f"""
        <div style="text-align: center; margin: 20px;">
            <div style="font-size: 64px;">{icon}</div>
            <div style="font-size: 28px; font-weight: bold; margin-top: 10px;">{html.escape(step)}</div>
        </div>
        """

    render_html(f"""
    <div style="background-color: #FFFFFF; padding: 40px; border-radius: 24px; text-align: center; box-shadow: 0 4px 16px rgba(0,0,0,0.1);">
        <div style="font-size: 20px; color: #666; margin-bottom: 20px;">{time_slot}</div>
        <div style="font-size: 32px; line-height: 1.6; color: #2D3436; margin-bottom: 30px;">{script}</div>
        <div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 20px;">
            {steps_html}
        </div>
    </div>
    """, height=400)

    if st.button("关闭全屏展示", type="primary", key="close_fullscreen_btn"):
        st.session_state.show_task_fullscreen = False
        st.session_state.fullscreen_task_data = None
        st.rerun()


# ============================================================
# 页面4: 岗位适配 (job_fit)
# ============================================================

def render_job_fit_page():
    """岗位适配评估页面"""
    st.markdown("## 📊 岗位适配评估")
    st.markdown("评估员工与目标岗位的匹配程度，生成综合评估报告和入职支持建议。")

    current_supervisor = get_current_supervisor()

    # ===== 第一步：选择员工 =====
    st.markdown("### 第一步：选择员工")

    if not current_supervisor:
        st.info("请先创建主管")
        return

    employees = st.session_state.data_manager.get_employees(current_supervisor["id"])
    if not employees:
        st.info("暂无员工，请先在「员工管理」中创建员工")
        return

    current_employee = get_current_employee()
    employee_map = {
        eid: f"{e['name']}({e['disability_type']})"
        for eid, e in employees.items()
    }
    current_eid = current_employee["id"] if current_employee else None
    current_eidx = list(employee_map.keys()).index(current_eid) if current_eid in employee_map else 0

    col_select, col_quick = st.columns([3, 1])
    with col_select:
        selected_eid = st.selectbox(
            "选择员工",
            options=list(employee_map.keys()),
            format_func=lambda x: employee_map[x],
            index=current_eidx,
            key="job_fit_employee_select",
        )
    with col_quick:
        st.markdown("<br>", unsafe_allow_html=True)
        show_quick_create = st.button("快速新建", key="quick_create_employee_btn")

    # 快速新建员工内联表单
    if show_quick_create:
        with st.expander("快速新建员工", expanded=True):
            render_employee_form(current_supervisor["id"], employee_data=None)

    selected_employee = employees.get(selected_eid)
    if not selected_employee:
        return

    st.markdown("---")

    # ===== 第二步：岗位信息表单 =====
    st.markdown("### 第二步：岗位信息")

    job_name = st.text_input(
        "岗位名称",
        placeholder="例如：超市理货员",
        key="job_fit_name",
    )

    col_noise, col_flow, col_light = st.columns(3)
    with col_noise:
        noise_level = st.selectbox(
            "噪音水平",
            options=["低", "中", "高"],
            index=1,
            key="job_fit_noise",
        )
    with col_flow:
        flow_density = st.selectbox(
            "人流密度",
            options=["低", "中", "高"],
            index=1,
            key="job_fit_flow",
        )
    with col_light:
        light_condition = st.selectbox(
            "照明情况",
            options=["低", "中", "高"],
            index=1,
            key="job_fit_light",
        )

    task_list = st.text_area(
        "主要任务列表（每行一条）",
        placeholder="整理货架\n补货\n更换价签\n清理过期商品",
        key="job_fit_tasks",
        height=120,
    )

    col_hours, col_fixed, col_comm, col_switch = st.columns(4)
    with col_hours:
        daily_hours = st.number_input(
            "日工作时长（小时）",
            min_value=1,
            max_value=12,
            value=8,
            key="job_fit_hours",
        )
    with col_fixed:
        fixed_station = st.radio(
            "固定工位",
            options=["是", "否"],
            horizontal=True,
            index=0,
            key="job_fit_fixed",
        )
    with col_comm:
        customer_comm = st.radio(
            "顾客沟通",
            options=["是", "否"],
            horizontal=True,
            index=1,
            key="job_fit_comm",
        )
    with col_switch:
        quick_switch = st.radio(
            "快速任务切换",
            options=["是", "否"],
            horizontal=True,
            index=1,
            key="job_fit_switch",
        )

    assess_clicked = st.button("🚀 生成评估报告", type="primary", key="job_fit_assess_btn")

    # 生成逻辑
    if assess_clicked:
        if not job_name.strip():
            st.warning("请输入岗位名称")
            return

        job_info = {
            "岗位名称": job_name,
            "噪音水平": noise_level,
            "人流密度": flow_density,
            "照明情况": light_condition,
            "主要任务列表": task_list,
            "日工作时长": f"{daily_hours}小时",
            "固定工位": fixed_station,
            "顾客沟通": customer_comm,
            "快速任务切换": quick_switch,
        }

        with st.spinner("🤖 正在生成岗位适配评估，请稍候..."):
            system_prompt = build_job_fit_prompt(
                employee=selected_employee,
                job_info=job_info,
            )
            user_message = build_user_message(
                f"请评估员工 {selected_employee.get('name', '')} 与岗位「{job_name}」的适配程度。\n"
                f"岗位信息：\n{chr(10).join(f'- {k}：{v}' for k, v in job_info.items())}",
                "job_fit",
            )
            report, error = st.session_state.api_client.assess_job_fit(
                system_prompt=system_prompt,
                user_message=user_message,
            )
            if error:
                st.error(error)
                return

        st.session_state.job_fit_report = report

        # 保存到数据文件
        st.session_state.data_manager.save_job_fit_report(
            current_supervisor["id"],
            selected_eid,
            {
                "report": report,
                "job_info": job_info,
                "employee_name": selected_employee.get("name", ""),
                "created_at": datetime.now().isoformat(),
            },
        )

        st.rerun()

    # ===== 输出区：展示评估报告 =====
    if st.session_state.job_fit_report:
        _render_job_fit_report(st.session_state.job_fit_report, selected_employee)


def _render_job_fit_report(report, employee):
    """渲染岗位适配评估报告"""
    st.markdown("---")
    st.markdown("### 📋 评估报告")

    scores = report.get("scores", {})
    disability_type = employee.get("disability_type", "ASD")

    # 计算综合评分
    raw_scores = {}
    for dim in ("cognitive", "sensory", "social", "structure"):
        dim_data = scores.get(dim, {})
        raw_scores[dim] = dim_data.get("score", 0) if isinstance(dim_data, dict) else 0

    overall = calculate_overall_score(disability_type, raw_scores)

    # 综合评分颜色
    if overall >= 75:
        score_color = "#6B8F71"
        score_label = "适配良好"
    elif overall >= 60:
        score_color = "#F5A623"
        score_label = "需要调整"
    else:
        score_color = "#E74C3C"
        score_label = "风险较高"

    render_html(f"""
    <div style="background-color: #FFFFFF; padding: 30px; border-radius: 16px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px;">
        <div style="font-size: 16px; color: #666; margin-bottom: 10px;">综合评分</div>
        <div style="font-size: 64px; font-weight: bold; color: {score_color};">{overall}</div>
        <div style="font-size: 18px; color: {score_color}; margin-top: 5px;">{score_label}</div>
    </div>
    """, height=200)

    # 四维进度条
    st.markdown("#### 四维评估")
    dim_labels = {
        "cognitive": "🧠 认知匹配",
        "sensory": "👁️ 感官环境",
        "social": "💬 社交要求",
        "structure": "📐 结构化程度",
    }

    for dim, label in dim_labels.items():
        dim_data = scores.get(dim, {})
        score = dim_data.get("score", 0) if isinstance(dim_data, dict) else 0
        reasoning = dim_data.get("reasoning", "") if isinstance(dim_data, dict) else ""

        st.markdown(f"**{label}**：{score}/100")
        st.progress(score / 100.0)
        if reasoning:
            st.caption(reasoning)
        st.markdown("")

    # 风险环节清单
    risk_items = report.get("risk_items", [])
    if risk_items:
        st.markdown("#### ⚠️ 风险环节")
        for item in risk_items:
            if not isinstance(item, dict):
                continue
            description = html.escape(item.get("description", ""))
            level = item.get("level", "low")
            support = html.escape(item.get("support", ""))

            level_config = {
                "high": {"bg": "#FFEBEE", "border": "#E74C3C", "label": "高风险", "icon": "🔴"},
                "medium": {"bg": "#FFF8E1", "border": "#F5A623", "label": "中风险", "icon": "🟡"},
                "low": {"bg": "#E8F5E9", "border": "#6B8F71", "label": "低风险", "icon": "🟢"},
            }
            config = level_config.get(level, level_config["low"])

            render_html(f"""
            <div style="background-color: {config['bg']}; border-left: 4px solid {config['border']}; padding: 12px 16px; border-radius: 0 12px 12px 0; margin: 8px 0;">
                <div style="font-weight: bold; color: {config['border']};">{config['icon']} {config['label']}</div>
                <div style="margin-top: 4px;">{description}</div>
                <div style="margin-top: 6px; color: #2E7D32; font-size: 14px;">💡 {support}</div>
            </div>
            """, height=100)

    # 入职支持建议（三个阶段 tabs）
    onboarding = report.get("onboarding_plan", {})
    if onboarding:
        st.markdown("#### 📝 入职支持建议")
        tab1, tab2, tab3 = st.tabs(["📅 第一周", "📆 第一个月", "🏆 长期稳定"])

        with tab1:
            week1_items = onboarding.get("week1", [])
            if week1_items:
                for item in week1_items:
                    st.markdown(f"- {item}")
            else:
                st.info("暂无建议")

        with tab2:
            month1_items = onboarding.get("month1", [])
            if month1_items:
                for item in month1_items:
                    st.markdown(f"- {item}")
            else:
                st.info("暂无建议")

        with tab3:
            stable_items = onboarding.get("stable", [])
            if stable_items:
                for item in stable_items:
                    st.markdown(f"- {item}")
            else:
                st.info("暂无建议")

    # 岗位调整建议
    adjustments = report.get("job_adjustments", [])
    if adjustments:
        st.markdown("#### 🔧 岗位调整建议")
        for adj in adjustments:
            st.markdown(f"- {adj}")

    # 导出按钮
    st.markdown("---")
    _export_job_fit_report_text(report, employee, overall, score_label)


def _export_job_fit_report_text(report, employee, overall, score_label):
    """生成并导出岗位适配评估文本报告"""
    lines = []
    lines.append("=" * 50)
    lines.append("同频心智助手 - 岗位适配评估报告")
    lines.append("=" * 50)
    lines.append(f"员工姓名：{employee.get('name', '')}")
    lines.append(f"障碍类型：{employee.get('disability_type', '')}")
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"综合评分：{overall} ({score_label})")
    lines.append("")

    scores = report.get("scores", {})
    dim_labels = {
        "cognitive": "认知匹配",
        "sensory": "感官环境",
        "social": "社交要求",
        "structure": "结构化程度",
    }
    lines.append("【四维评估】")
    for dim, label in dim_labels.items():
        dim_data = scores.get(dim, {})
        score = dim_data.get("score", 0) if isinstance(dim_data, dict) else 0
        reasoning = dim_data.get("reasoning", "") if isinstance(dim_data, dict) else ""
        lines.append(f"  {label}：{score}/100")
        lines.append(f"    {reasoning}")
    lines.append("")

    risk_items = report.get("risk_items", [])
    if risk_items:
        lines.append("【风险环节】")
        for item in risk_items:
            if isinstance(item, dict):
                lines.append(f"  [{item.get('level', 'low').upper()}] {item.get('description', '')}")
                lines.append(f"    支持：{item.get('support', '')}")
        lines.append("")

    onboarding = report.get("onboarding_plan", {})
    if onboarding:
        lines.append("【入职支持建议】")
        phase_labels = {"week1": "第一周", "month1": "第一个月", "stable": "长期稳定"}
        for phase, label in phase_labels.items():
            items = onboarding.get(phase, [])
            if items:
                lines.append(f"  {label}：")
                for item in items:
                    lines.append(f"    - {item}")
        lines.append("")

    adjustments = report.get("job_adjustments", [])
    if adjustments:
        lines.append("【岗位调整建议】")
        for adj in adjustments:
            lines.append(f"  - {adj}")

    report_text = "\n".join(lines)
    st.download_button(
        label="📥 下载评估报告",
        data=report_text,
        file_name=f"job_fit_report_{employee.get('name', 'employee')}_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain",
    )


# ============================================================
# 页面5: 员工管理 (manage)
# ============================================================

def render_manage_page():
    """员工管理页面"""
    st.markdown("## 👤 员工管理")

    current_supervisor = get_current_supervisor()

    # ===== 主管管理 =====
    st.markdown("### 主管管理")

    supervisors = st.session_state.data_manager.get_supervisors()
    supervisor_names = {sid: s["name"] for sid, s in supervisors.items()}

    if supervisors:
        current_sid = current_supervisor["id"] if current_supervisor else None
        selected_sid = st.selectbox(
            "当前主管",
            options=list(supervisor_names.keys()),
            format_func=lambda x: supervisor_names[x],
            index=list(supervisor_names.keys()).index(current_sid) if current_sid in supervisor_names else 0,
            key="manage_supervisor_select",
        )

        if selected_sid != current_sid:
            st.session_state.data_manager.set_current_supervisor(selected_sid)
            st.session_state.conversation.clear()
            st.rerun()

        col_edit_sup, col_del_sup = st.columns(2)
        with col_edit_sup:
            new_sup_name = st.text_input("修改主管名称", value=supervisor_names.get(selected_sid, ""), key="edit_supervisor_name")
            if st.button("💾 保存名称", key="save_supervisor_name_btn"):
                if new_sup_name.strip():
                    st.session_state.data_manager.update_supervisor(selected_sid, new_sup_name.strip())
                    st.success("名称已更新！")
                    st.rerun()
        with col_del_sup:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ 删除当前主管", key="delete_supervisor_btn"):
                st.session_state.data_manager.delete_supervisor(selected_sid)
                st.session_state.conversation.clear()
                st.success("主管已删除")
                st.rerun()
    else:
        st.info("暂无主管，请先创建")

    with st.expander("➕ 新建主管"):
        new_supervisor_name = st.text_input("主管名称", key="new_supervisor_name")
        if st.button("创建", key="create_supervisor_btn"):
            if new_supervisor_name.strip():
                st.session_state.data_manager.create_supervisor(new_supervisor_name.strip())
                st.success("创建成功！")
                st.rerun()

    st.markdown("---")

    # ===== 员工列表 =====
    current_supervisor = get_current_supervisor()
    if not current_supervisor:
        st.info("请先选择或创建主管")
        return

    st.markdown("### 员工列表")
    employees = st.session_state.data_manager.get_employees(current_supervisor["id"])

    if not employees:
        st.info("当前主管下暂无员工，请点击下方按钮创建")
    else:
        # 表格展示
        table_data = []
        for eid, emp in employees.items():
            table_data.append({
                "姓名": emp.get("name", ""),
                "障碍类型": f"{emp.get('disability_type', '')} - {DISABILITY_TYPE_CN.get(emp.get('disability_type', ''), '')}",
                "工作记忆": f"{emp.get('working_memory', 2)}步",
                "场景": emp.get("scenario", ""),
                "沟通偏好": emp.get("comm_preference", ""),
            })

        if table_data:
            import pandas as pd
            df = pd.DataFrame(table_data)
            st.dataframe(df, width="stretch", hide_index=True)

        # 操作按钮列表
        st.markdown("**操作：**")
        cols = st.columns(min(len(employees), 4))
        for i, (eid, emp) in enumerate(employees.items()):
            with cols[i % len(cols)]:
                if st.button(f"✏️ {emp.get('name', eid)}", key=f"edit_emp_{eid}", width="stretch"):
                    st.session_state.editing_employee = True
                    st.session_state.editing_employee_id = eid
                    st.session_state.form_version = getattr(st.session_state, 'form_version', 0) + 1
                    st.rerun()

    st.markdown("---")

    # ===== 员工创建/编辑表单 =====
    if st.session_state.editing_employee and st.session_state.get("editing_employee_id"):
        eid = st.session_state.editing_employee_id
        emp_data = employees.get(eid) if employees else None
        if emp_data:
            with st.container(border=True):
                render_employee_form(current_supervisor["id"], employee_data=emp_data)
    else:
        with st.container(border=True):
            render_employee_form(current_supervisor["id"], employee_data=None)


# ============================================================
# 页面6: 设置 (settings)
# ============================================================

def render_settings_page():
    """设置页面"""
    st.markdown("## ⚙️ 设置")

    # ===== API 配置 =====
    st.markdown("### API 配置")

    config = st.session_state.data_manager.get_config()

    api_base_url = st.text_input(
        "API Base URL",
        value=config.get("api_base_url", "https://api.openai.com/v1"),
        key="settings_api_base_url",
    )

    api_key = st.text_input(
        "API Key",
        value=config.get("api_key", ""),
        type="password",
        key="settings_api_key",
    )

    model_options = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "deepseek-chat", "glm-4", "自定义"]
    current_model = config.get("model", "gpt-4o")
    if current_model not in model_options[:-1]:
        model_index = len(model_options) - 1
    else:
        model_index = model_options.index(current_model)

    model_select = st.selectbox(
        "模型名称",
        options=model_options,
        index=model_index,
        key="settings_model_select",
    )

    if model_select == "自定义":
        model = st.text_input(
            "自定义模型名称",
            value=current_model if current_model not in model_options[:-1] else "",
            key="settings_model_custom",
        )
    else:
        model = model_select

    col_save, col_test = st.columns(2)
    with col_save:
        if st.button("💾 保存配置", key="settings_save_btn"):
            st.session_state.data_manager.save_config(api_base_url, api_key, model)
            st.success("配置已保存！")
    with col_test:
        if st.button("🔄 测试连接", key="settings_test_btn"):
            success, message = st.session_state.api_client.test_connection_with_config(
                base_url=api_base_url,
                api_key=api_key,
                model=model,
            )
            if success:
                st.success(message)
            else:
                st.error(message)

    st.markdown("---")

    # ===== API 状态 =====
    st.markdown("### API 状态")
    render_api_status()

    st.markdown("---")

    # ===== 对话管理 =====
    st.markdown("### 对话管理")

    if st.button("📥 导出对话记录", key="settings_export_btn"):
        conversation_text = st.session_state.conversation.export_to_text()
        st.download_button(
            label="下载 TXT",
            data=conversation_text,
            file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
        )

    if st.button("🗑️ 清空对话", key="settings_clear_btn"):
        st.session_state.conversation.clear()
        st.success("对话已清空")
        st.rerun()


# ============================================================
# 主逻辑
# ============================================================

def main():
    """主函数"""
    render_sidebar()

    # 每日首次进入弹出免责声明
    show_disclaimer_dialog()

    page = st.session_state.current_page

    if page == "forward":
        render_forward_page()
    elif page == "reverse":
        render_reverse_page()
    elif page == "decompose":
        render_decompose_page()
    elif page == "job_fit":
        render_job_fit_page()
    elif page == "manage":
        render_manage_page()
    elif page == "settings":
        render_settings_page()


if __name__ == "__main__":
    main()

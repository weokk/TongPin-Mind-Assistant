"""
Babel-ND V2 数据管理模块
处理主管、员工画像、API配置、任务序列、评估报告的本地存储
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import uuid

# 数据文件路径
DATA_FILE = "babel_nd_data.json"
CONFIG_FILE = "babel_nd_config.json"
TASKS_FILE = "babel_nd_tasks.json"
REPORTS_FILE = "babel_nd_reports.json"

# ============================================================
# 默认数据结构
# ============================================================

DEFAULT_DATA = {
    "supervisors": {},
    "current_supervisor_id": None,
    "current_employee_id": None,
}

DEFAULT_CONFIG = {
    "api_base_url": "https://api.openai.com/v1",
    "api_key": "",
    "model": "gpt-4o",
}

DEFAULT_TASKS = {}

DEFAULT_REPORTS = {}

# ============================================================
# 数据管理类
# ============================================================

class DataManager:
    """管理主管、员工、配置、任务序列和评估报告数据"""

    def __init__(self, data_dir: str = "."):
        self.data_dir = data_dir
        self.data_file = os.path.join(data_dir, DATA_FILE)
        self.config_file = os.path.join(data_dir, CONFIG_FILE)
        self.tasks_file = os.path.join(data_dir, TASKS_FILE)
        self.reports_file = os.path.join(data_dir, REPORTS_FILE)
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        """确保数据文件存在"""
        if not os.path.exists(self.data_file):
            self._save_data(DEFAULT_DATA)
        if not os.path.exists(self.config_file):
            self._save_config(DEFAULT_CONFIG)
        if not os.path.exists(self.tasks_file):
            self._save_tasks(DEFAULT_TASKS)
        if not os.path.exists(self.reports_file):
            self._save_reports(DEFAULT_REPORTS)

    def _load_data(self) -> dict:
        """加载用户数据"""
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, PermissionError, UnicodeDecodeError):
            return DEFAULT_DATA.copy()

    def _save_data(self, data: dict):
        """保存用户数据"""
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_config(self) -> dict:
        """加载API配置"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, PermissionError, UnicodeDecodeError):
            return DEFAULT_CONFIG.copy()

    def _save_config(self, config: dict):
        """保存API配置"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def _load_tasks(self) -> dict:
        """加载任务序列数据"""
        try:
            with open(self.tasks_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, PermissionError, UnicodeDecodeError):
            return DEFAULT_TASKS.copy()

    def _save_tasks(self, tasks: dict):
        """保存任务序列数据"""
        with open(self.tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

    def _load_reports(self) -> dict:
        """加载评估报告数据"""
        try:
            with open(self.reports_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, PermissionError, UnicodeDecodeError):
            return DEFAULT_REPORTS.copy()

    def _save_reports(self, reports: dict):
        """保存评估报告数据"""
        with open(self.reports_file, "w", encoding="utf-8") as f:
            json.dump(reports, f, ensure_ascii=False, indent=2)

    # ============================================================
    # 主管管理
    # ============================================================

    def get_supervisors(self) -> Dict[str, dict]:
        """获取所有主管"""
        data = self._load_data()
        return data.get("supervisors", {})

    def get_supervisor(self, supervisor_id: str) -> Optional[dict]:
        """获取单个主管"""
        supervisors = self.get_supervisors()
        return supervisors.get(supervisor_id)

    def create_supervisor(self, name: str) -> str:
        """创建新主管，返回ID"""
        data = self._load_data()
        supervisor_id = f"sup_{uuid.uuid4().hex[:8]}"

        data["supervisors"][supervisor_id] = {
            "id": supervisor_id,
            "name": name,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "employees": {},
        }

        # 如果是第一个主管，自动设为当前主管
        if len(data["supervisors"]) == 1:
            data["current_supervisor_id"] = supervisor_id

        self._save_data(data)
        return supervisor_id

    def update_supervisor(self, supervisor_id: str, name: str):
        """更新主管名称"""
        data = self._load_data()
        if supervisor_id in data["supervisors"]:
            data["supervisors"][supervisor_id]["name"] = name
            self._save_data(data)

    def delete_supervisor(self, supervisor_id: str):
        """删除主管及其所有员工"""
        data = self._load_data()
        if supervisor_id in data["supervisors"]:
            del data["supervisors"][supervisor_id]
            if data["current_supervisor_id"] == supervisor_id:
                # 切换到第一个可用主管
                remaining = list(data["supervisors"].keys())
                data["current_supervisor_id"] = remaining[0] if remaining else None
            self._save_data(data)

    def set_current_supervisor(self, supervisor_id: str):
        """设置当前主管"""
        data = self._load_data()
        if supervisor_id in data["supervisors"]:
            data["current_supervisor_id"] = supervisor_id
            # 重置当前员工
            employees = data["supervisors"][supervisor_id].get("employees", {})
            if employees:
                data["current_employee_id"] = list(employees.keys())[0]
            else:
                data["current_employee_id"] = None
            self._save_data(data)

    def get_current_supervisor(self) -> Optional[dict]:
        """获取当前主管"""
        data = self._load_data()
        supervisor_id = data.get("current_supervisor_id")
        if supervisor_id:
            return data["supervisors"].get(supervisor_id)
        return None

    # ============================================================
    # 员工管理
    # ============================================================

    def get_employees(self, supervisor_id: str) -> Dict[str, dict]:
        """获取某主管下的所有员工"""
        supervisor = self.get_supervisor(supervisor_id)
        if supervisor:
            return supervisor.get("employees", {})
        return {}

    def get_employee(self, supervisor_id: str, employee_id: str) -> Optional[dict]:
        """获取单个员工"""
        employees = self.get_employees(supervisor_id)
        return employees.get(employee_id)

    def create_employee(self, supervisor_id: str, employee_data: dict) -> str:
        """创建新员工，返回ID"""
        data = self._load_data()
        if supervisor_id not in data["supervisors"]:
            return None

        employee_id = f"emp_{uuid.uuid4().hex[:8]}"
        employee_data["id"] = employee_id
        employee_data["created_at"] = datetime.now().strftime("%Y-%m-%d")

        if "employees" not in data["supervisors"][supervisor_id]:
            data["supervisors"][supervisor_id]["employees"] = {}

        data["supervisors"][supervisor_id]["employees"][employee_id] = employee_data

        # 如果是该主管的第一个员工，自动设为当前员工
        if len(data["supervisors"][supervisor_id]["employees"]) == 1:
            data["current_employee_id"] = employee_id

        self._save_data(data)
        return employee_id

    def update_employee(self, supervisor_id: str, employee_id: str, employee_data: dict):
        """更新员工画像"""
        data = self._load_data()
        if supervisor_id in data["supervisors"]:
            if employee_id in data["supervisors"][supervisor_id].get("employees", {}):
                # 保留ID和创建时间
                employee_data["id"] = employee_id
                employee_data["created_at"] = data["supervisors"][supervisor_id]["employees"][employee_id].get("created_at", "")
                data["supervisors"][supervisor_id]["employees"][employee_id] = employee_data
                self._save_data(data)

    def delete_employee(self, supervisor_id: str, employee_id: str):
        """删除员工"""
        data = self._load_data()
        if supervisor_id in data["supervisors"]:
            employees = data["supervisors"][supervisor_id].get("employees", {})
            if employee_id in employees:
                del employees[employee_id]
                # 如果删除的是当前员工，切换到第一个可用员工
                if data.get("current_employee_id") == employee_id:
                    remaining = list(employees.keys())
                    data["current_employee_id"] = remaining[0] if remaining else None
                self._save_data(data)

    def set_current_employee(self, supervisor_id: str, employee_id: str):
        """设置当前员工"""
        data = self._load_data()
        if supervisor_id in data["supervisors"]:
            employees = data["supervisors"][supervisor_id].get("employees", {})
            if employee_id in employees:
                data["current_employee_id"] = employee_id
                self._save_data(data)

    def get_current_employee(self) -> Optional[dict]:
        """获取当前员工"""
        data = self._load_data()
        supervisor_id = data.get("current_supervisor_id")
        employee_id = data.get("current_employee_id")

        if supervisor_id and employee_id:
            supervisor = data["supervisors"].get(supervisor_id)
            if supervisor:
                return supervisor.get("employees", {}).get(employee_id)
        return None

    # ============================================================
    # API 配置管理
    # ============================================================

    def get_config(self) -> dict:
        """获取API配置"""
        return self._load_config()

    def save_config(self, api_base_url: str, api_key: str, model: str):
        """保存API配置"""
        config = {
            "api_base_url": api_base_url,
            "api_key": api_key,
            "model": model,
        }
        self._save_config(config)

    def get_api_key(self) -> str:
        """获取API Key"""
        config = self._load_config()
        return config.get("api_key", "")

    def get_api_base_url(self) -> str:
        """获取API Base URL"""
        config = self._load_config()
        return config.get("api_base_url", "https://api.openai.com/v1")

    def get_model(self) -> str:
        """获取模型名称"""
        config = self._load_config()
        return config.get("model", "gpt-4o")

    # ============================================================
    # 任务序列管理
    # ============================================================

    def save_task_sequence(self, supervisor_id: str, employee_id: str, sequence: dict) -> None:
        """保存任务序列到数据文件"""
        tasks = self._load_tasks()

        if supervisor_id not in tasks:
            tasks[supervisor_id] = {}
        if employee_id not in tasks[supervisor_id]:
            tasks[supervisor_id][employee_id] = []

        tasks[supervisor_id][employee_id].append(sequence)
        self._save_tasks(tasks)

    def load_task_sequence(self, supervisor_id: str, employee_id: str) -> Optional[dict]:
        """加载员工最新的任务序列"""
        tasks = self._load_tasks()

        sequences = tasks.get(supervisor_id, {}).get(employee_id, [])
        if sequences:
            return sequences[-1]
        return None

    # ============================================================
    # 评估报告管理
    # ============================================================

    def save_job_fit_report(self, supervisor_id: str, employee_id: str, report: dict) -> None:
        """保存岗位适配评估报告"""
        reports = self._load_reports()

        if supervisor_id not in reports:
            reports[supervisor_id] = {}
        if employee_id not in reports[supervisor_id]:
            reports[supervisor_id][employee_id] = []

        reports[supervisor_id][employee_id].append(report)
        self._save_reports(reports)

    def load_job_fit_reports(self, supervisor_id: str, employee_id: str) -> list:
        """加载员工的所有评估报告"""
        reports = self._load_reports()

        return reports.get(supervisor_id, {}).get(employee_id, [])


# ============================================================
# 对话历史管理（内存中，使用 Streamlit session_state）
# ============================================================

class ConversationManager:
    """管理对话历史（用于 session_state）"""

    def __init__(self):
        self.messages = []  # [{"role": "user/assistant", "content": "...", "card_type": "..."}]
        self.reverse_count = 0  # 逆向解码计数器A
        self.se_risk_count = 0  # SEAT为S或E的计数器B
        self.truncated = False  # 对话是否发生过截断

    def add_message(self, role: str, content: str, card_type: str = None, card_data: dict = None, mode: str = None):
        """添加消息"""
        self.messages.append({
            "role": role,
            "content": content,
            "card_type": card_type,
            "card_data": card_data,
            "mode": mode,
            "timestamp": datetime.now().isoformat(),
        })

    def get_messages(self) -> List[dict]:
        """获取所有消息"""
        return self.messages

    def get_context_messages(self, max_turns: int = 20) -> List[dict]:
        """获取用于API调用的上下文消息（最多20轮）"""
        truncated = len(self.messages) > max_turns * 2
        if truncated:
            self.truncated = True

        # 取最近的消息
        recent = self.messages[-(max_turns * 2):] if truncated else self.messages

        # 转换为API格式
        context = []
        for msg in recent:
            if msg["role"] == "user":
                context.append({"role": "user", "content": msg["content"]})
            else:
                # 助手消息只取简要内容，截断长度为2000字符
                context.append({"role": "assistant", "content": msg.get("content", "")[:2000]})

        return context

    def clear(self):
        """清空对话历史和计数器"""
        self.messages = []
        self.reverse_count = 0
        self.se_risk_count = 0
        self.truncated = False

    def increment_reverse_count(self):
        """增加逆向计数"""
        self.reverse_count += 1

    def increment_se_risk_count(self, seat_label: str):
        """如果SEAT为S或E，增加风险计数"""
        if seat_label in ["S", "E"]:
            self.se_risk_count += 1

    def check_alert_level(self) -> str:
        """
        检查认知负荷警报级别
        返回: "normal", "warning", "critical"
        """
        # WARNING: A>=3 且 B>=2
        if self.reverse_count >= 3 and self.se_risk_count >= 2:
            # CRITICAL: A>=5 或 B>=3
            if self.reverse_count >= 5 or self.se_risk_count >= 3:
                return "critical"
            return "warning"
        return "normal"

    def export_to_text(self) -> str:
        """导出对话历史为文本"""
        lines = []
        for msg in self.messages:
            role = "主管" if msg["role"] == "user" else "AI"
            timestamp = msg.get("timestamp", "")[:19]
            lines.append(f"[{timestamp}] {role}: {msg['content']}")
            if msg.get("card_type"):
                lines.append(f"  -> 卡片类型: {msg['card_type']}")
        return "\n".join(lines)

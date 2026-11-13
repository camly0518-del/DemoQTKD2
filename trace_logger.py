"""
Hệ thống Audit Logging & Execution Trace cho AI Agent
Truy vết từng bước thực thi, công cụ (Tool calling), quy tắc kích hoạt (Rules fired)
và kết quả trung gian để phục vụ kiểm toán và thuyết minh đề tài AI301.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional

class AgentExecutionTrace:
    """Ghi nhận nhật ký xử lý độc lập cho từng cơ hội (Opportunity Trace)"""

    def __init__(self, request_id: str, customer_name: str = ""):
        self.request_id = request_id
        self.customer_name = customer_name
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.steps: List[Dict[str, Any]] = []
        self.tools_called: List[Dict[str, Any]] = []
        self.rules_triggered: List[Dict[str, Any]] = []
        self.final_status: str = "INITIALIZED"

    def log_step(self, step_name: str, description: str, inputs: Any, outputs: Any, status: str = "SUCCESS"):
        """Ghi nhận một bước quy trình theo workflow"""
        self.steps.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "step_name": step_name,
            "description": description,
            "inputs": inputs,
            "outputs": outputs,
            "status": status
        })

    def log_tool_call(self, tool_name: str, arguments: Dict[str, Any], result: Any):
        """Ghi nhận lời gọi công cụ (Tool Execution)"""
        self.tools_called.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result
        })

    def log_rule(self, rule_id: str, rule_name: str, condition: str, action_taken: str, is_exception: bool = False):
        """Ghi nhận quy tắc nghiệp vụ được kích hoạt"""
        self.rules_triggered.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "rule_id": rule_id,
            "rule_name": rule_name,
            "condition": condition,
            "action_taken": action_taken,
            "is_exception": is_exception
        })

    def complete(self, final_status: str):
        self.final_status = final_status
        self.end_time = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        duration_ms = 0
        if self.end_time:
            duration_ms = round((self.end_time - self.start_time).total_seconds() * 1000, 2)

        return {
            "request_id": self.request_id,
            "customer_name": self.customer_name,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S") if self.end_time else "",
            "duration_ms": duration_ms,
            "final_status": self.final_status,
            "steps_count": len(self.steps),
            "tools_called_count": len(self.tools_called),
            "rules_count": len(self.rules_triggered),
            "steps": self.steps,
            "tools_called": self.tools_called,
            "rules_triggered": self.rules_triggered
        }


class GlobalTraceRegistry:
    """Lưu trữ tất cả trace trong phiên làm việc để hiển thị trên UI"""
    _traces: List[AgentExecutionTrace] = []

    @classmethod
    def clear(cls):
        cls._traces = []

    @classmethod
    def register(cls, trace: AgentExecutionTrace):
        cls._traces.append(trace)

    @classmethod
    def get_all(cls) -> List[AgentExecutionTrace]:
        return cls._traces

    @classmethod
    def get_by_id(cls, request_id: str) -> Optional[AgentExecutionTrace]:
        for t in cls._traces:
            if t.request_id == request_id:
                return t
        return None


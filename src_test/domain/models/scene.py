"""
场景信息模型
从原 agent/agentService/service_mcp.py 提取
"""


class SceneInfo:
    """存储场景信息"""
    def __init__(self, scene_name: str, thread_id: str, prompt: str):
        self.scene_name = scene_name
        self.thread_id = thread_id
        self.prompt = prompt

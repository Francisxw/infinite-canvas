
import json
from typing import Dict, List, Optional
from fastapi import WebSocket


class ConnectionManager:
    """
    WebSocket 连接管理器。
    负责管理所有 WebSocket 客户端的连接、断开、消息推送等操作。
    支持广播、私信、统计在线人数等功能。
    """
    def __init__(self):
        # 当前所有活跃的 WebSocket 连接对象列表
        self.active_connections: List[WebSocket] = []
        # 记录每个 client_id 对应的 WebSocket 连接
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None) -> None:
        """
        新客户端连接时调用。
        接受 WebSocket 连接，并将其加入活跃连接列表。
        如果提供了 client_id，则建立 client_id 到 websocket 的映射。
        :param websocket: 新连接的 WebSocket 实例
        :param client_id: 客户端唯一标识（可选）
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        if client_id:
            self.user_connections[client_id] = websocket
        print(f"WS Connected. Total: {len(self.active_connections)}")
        await self.broadcast_count()

    async def disconnect(self, websocket: WebSocket, client_id: Optional[str] = None) -> None:
        """
        客户端断开连接时调用。
        从活跃连接列表和 user_connections 字典中移除对应的 WebSocket。
        :param websocket: 断开的 WebSocket 实例
        :param client_id: 客户端唯一标识（可选）
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if client_id and client_id in self.user_connections:
            del self.user_connections[client_id]
        print(f"WS Disconnected. Total: {len(self.active_connections)}")
        await self.broadcast_count()

    async def broadcast_count(self) -> None:
        """
        向所有已连接客户端广播当前在线人数统计。
        发送消息类型为 stats，内容包含 online_count。
        """
        count = len(self.active_connections)
        data = json.dumps({"type": "stats", "online_count": count})
        for connection in self.active_connections[:]:
            try:
                await connection.send_text(data)
            except Exception as exc:
                print(f"Broadcast error: {exc}")
                self.active_connections.remove(connection)

    async def broadcast_new_image(self, image_data: dict) -> None:
        """
        向所有已连接客户端广播新图片消息。
        :param image_data: 图片相关数据（字典）
        """
        data = json.dumps({"type": "new_image", "data": image_data})
        for connection in self.active_connections[:]:
            try:
                await connection.send_text(data)
            except Exception as exc:
                print(f"Broadcast image error: {exc}")
                self.active_connections.remove(connection)

    async def send_personal_message(self, message: dict, client_id: str) -> None:
        """
        向指定 client_id 的客户端发送私有消息。
        :param message: 要发送的消息内容（字典）
        :param client_id: 目标客户端唯一标识
        """
        websocket = self.user_connections.get(client_id)
        if websocket:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as exc:
                print(f"Personal message error for {client_id}: {exc}")


# 单例管理器实例，供外部直接导入使用
manager = ConnectionManager()
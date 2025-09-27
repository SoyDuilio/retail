# websocket_manager.py
from fastapi import WebSocket
from typing import Dict, List, Optional
import json
from datetime import datetime
import asyncio
from app.schemas.common_schemas import RolUsuario, WebSocketMessage

class ConnectionManager:
    """Gestor de conexiones WebSocket para notificaciones en tiempo real"""
    
    def __init__(self):
        # Diccionario de conexiones activas por tipo de usuario
        self.active_connections: Dict[str, Dict[int, WebSocket]] = {
            "vendedor": {},
            "evaluador": {},
            "supervisor": {},
            "cliente": {}
        }
        
        # Cola de mensajes para usuarios desconectados
        self.message_queue: Dict[str, List[dict]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int, user_type: str):
        """Conectar nuevo usuario"""
        await websocket.accept()
        
        if user_type in self.active_connections:
            # Desconectar sesión previa si existe
            if user_id in self.active_connections[user_type]:
                try:
                    old_websocket = self.active_connections[user_type][user_id]
                    await old_websocket.close()
                except:
                    pass
            
            # Agregar nueva conexión
            self.active_connections[user_type][user_id] = websocket
            
            # Enviar mensajes pendientes
            await self._send_queued_messages(user_id, user_type)
            
            print(f"✅ Usuario conectado: {user_type}#{user_id}")
            
            # Notificar conexión a supervisores
            if user_type == "vendedor":
                await self._notify_supervisors({
                    "type": "vendedor_online",
                    "data": {
                        "vendedor_id": user_id,
                        "timestamp": datetime.now().isoformat()
                    }
                })
    
    def disconnect(self, user_id: int, user_type: str):
        """Desconectar usuario"""
        if user_type in self.active_connections and user_id in self.active_connections[user_type]:
            del self.active_connections[user_type][user_id]
            print(f"❌ Usuario desconectado: {user_type}#{user_id}")
            
            # Notificar desconexión a supervisores
            if user_type == "vendedor":
                asyncio.create_task(self._notify_supervisors({
                    "type": "vendedor_offline",
                    "data": {
                        "vendedor_id": user_id,
                        "timestamp": datetime.now().isoformat()
                    }
                }))
    
    async def send_personal_message(self, message: str, user_id: int, user_type: str):
        """Enviar mensaje a usuario específico"""
        if user_type in self.active_connections and user_id in self.active_connections[user_type]:
            try:
                websocket = self.active_connections[user_type][user_id]
                await websocket.send_text(message)
                return True
            except:
                # Conexión perdida, remover
                self.disconnect(user_id, user_type)
                return False
        else:
            # Usuario desconectado, agregar a cola
            self._queue_message(user_id, user_type, message)
            return False
    
    async def send_notification(self, user_id: int, user_type: RolUsuario, notification: dict):
        """Enviar notificación push a usuario"""
        message = WebSocketMessage(
            type="notification",
            data=notification
        )
        
        success = await self.send_personal_message(
            json.dumps(message.dict()),
            user_id,
            user_type.value
        )
        
        return success
    
    async def notify_evaluadores(self, message_data: dict):
        """Notificar a todos los evaluadores conectados"""
        message = json.dumps({
            "type": message_data["type"],
            "data": message_data["data"],
            "timestamp": datetime.now().isoformat(),
            "sound": True  # Reproducir sonido
        })
        
        # Enviar a evaluadores
        for evaluador_id, websocket in self.active_connections["evaluador"].items():
            try:
                await websocket.send_text(message)
            except:
                self.disconnect(evaluador_id, "evaluador")
        
        # Enviar también a supervisores
        for supervisor_id, websocket in self.active_connections["supervisor"].items():
            try:
                await websocket.send_text(message)
            except:
                self.disconnect(supervisor_id, "supervisor")
    
    async def notify_vendedor(self, vendedor_id: int, message_data: dict):
        """Notificar a vendedor específico"""
        message = json.dumps({
            "type": message_data["type"],
            "data": message_data["data"],
            "timestamp": datetime.now().isoformat(),
            "sound": True
        })
        
        await self.send_personal_message(message, vendedor_id, "vendedor")
    
    async def notify_cliente(self, cliente_id: int, message_data: dict):
        """Notificar a cliente específico"""
        message = json.dumps({
            "type": message_data["type"],
            "data": message_data["data"],
            "timestamp": datetime.now().isoformat(),
            "sound": False  # Clientes sin sonido por defecto
        })
        
        await self.send_personal_message(message, cliente_id, "cliente")
    
    async def broadcast_to_role(self, role: str, message_data: dict):
        """Enviar mensaje a todos los usuarios de un rol"""
        if role not in self.active_connections:
            return
        
        message = json.dumps({
            **message_data,
            "timestamp": datetime.now().isoformat()
        })
        
        disconnected_users = []
        for user_id, websocket in self.active_connections[role].items():
            try:
                await websocket.send_text(message)
            except:
                disconnected_users.append(user_id)
        
        # Limpiar conexiones perdidas
        for user_id in disconnected_users:
            self.disconnect(user_id, role)
    
    async def _notify_supervisors(self, message_data: dict):
        """Notificar solo a supervisores"""
        await self.broadcast_to_role("supervisor", message_data)
    
    def _queue_message(self, user_id: int, user_type: str, message: str):
        """Agregar mensaje a cola para usuario desconectado"""
        queue_key = f"{user_type}_{user_id}"
        
        if queue_key not in self.message_queue:
            self.message_queue[queue_key] = []
        
        # Limitar cola a 50 mensajes máximo
        if len(self.message_queue[queue_key]) >= 50:
            self.message_queue[queue_key] = self.message_queue[queue_key][-49:]
        
        self.message_queue[queue_key].append({
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _send_queued_messages(self, user_id: int, user_type: str):
        """Enviar mensajes en cola al reconectar"""
        queue_key = f"{user_type}_{user_id}"
        
        if queue_key in self.message_queue:
            messages = self.message_queue[queue_key]
            websocket = self.active_connections[user_type][user_id]
            
            for queued_msg in messages:
                try:
                    await websocket.send_text(queued_msg["message"])
                except:
                    break
            
            # Limpiar cola
            del self.message_queue[queue_key]
    
    def get_connection_stats(self) -> dict:
        """Obtener estadísticas de conexiones"""
        stats = {}
        total_connections = 0
        
        for role, connections in self.active_connections.items():
            count = len(connections)
            stats[role] = count
            total_connections += count
        
        stats["total"] = total_connections
        stats["queued_messages"] = sum(len(queue) for queue in self.message_queue.values())
        
        return stats
    
    def get_connected_users(self, role: Optional[str] = None) -> dict:
        """Obtener lista de usuarios conectados"""
        if role and role in self.active_connections:
            return {role: list(self.active_connections[role].keys())}
        
        return {
            role: list(connections.keys()) 
            for role, connections in self.active_connections.items()
        }
    
    async def send_system_message(self, message: str, roles: List[str] = None):
        """Enviar mensaje del sistema a roles específicos"""
        if roles is None:
            roles = ["vendedor", "evaluador", "supervisor"]
        
        system_message = {
            "type": "system_message",
            "data": {
                "message": message,
                "priority": "info"
            }
        }
        
        for role in roles:
            if role in self.active_connections:
                await self.broadcast_to_role(role, system_message)
    
    async def emergency_broadcast(self, message: str):
        """Enviar mensaje de emergencia a todos"""
        emergency_message = {
            "type": "emergency",
            "data": {
                "message": message,
                "priority": "critical"
            },
            "sound": True
        }
        
        for role in self.active_connections.keys():
            await self.broadcast_to_role(role, emergency_message)

# Instancia global del manager
manager = ConnectionManager()

# =============================================
# FUNCIONES AUXILIARES PARA NOTIFICACIONES
# =============================================

async def notificar_pedido_nuevo(pedido_data: dict):
    """Notificar nuevo pedido a evaluadores"""
    await manager.notify_evaluadores({
        "type": "pedido_nuevo",
        "data": {
            "pedido_id": pedido_data["id"],
            "numero_pedido": pedido_data["numero_pedido"],
            "vendedor": pedido_data["vendedor_nombre"],
            "cliente": pedido_data["cliente_nombre"],
            "total": str(pedido_data["total"]),
            "prioridad": "normal",
            "tiempo_espera": 0
        }
    })

async def notificar_pedido_aprobado(pedido_id: str, vendedor_id: int, cliente_id: int, monto: float):
    """Notificar aprobación de pedido"""
    # Notificar al vendedor
    await manager.notify_vendedor(vendedor_id, {
        "type": "pedido_aprobado",
        "data": {
            "pedido_id": pedido_id,
            "monto_aprobado": str(monto),
            "message": "¡Pedido aprobado! Puedes proceder con la entrega."
        }
    })
    
    # Notificar al cliente
    await manager.notify_cliente(cliente_id, {
        "type": "pedido_aprobado",
        "data": {
            "pedido_id": pedido_id,
            "monto_aprobado": str(monto),
            "message": "Su pedido ha sido aprobado y será entregado pronto."
        }
    })

async def notificar_pedido_rechazado(pedido_id: str, vendedor_id: int, cliente_id: int, motivo: str):
    """Notificar rechazo de pedido"""
    # Notificar al vendedor
    await manager.notify_vendedor(vendedor_id, {
        "type": "pedido_rechazado",
        "data": {
            "pedido_id": pedido_id,
            "motivo": motivo,
            "message": f"Pedido rechazado: {motivo}"
        }
    })
    
    # Notificar al cliente
    await manager.notify_cliente(cliente_id, {
        "type": "pedido_rechazado",
        "data": {
            "pedido_id": pedido_id,
            "motivo": motivo,
            "message": f"Su pedido no pudo ser aprobado: {motivo}"
        }
    })

async def notificar_stock_bajo(producto_nombre: str, stock_actual: int):
    """Notificar stock bajo a supervisores"""
    await manager._notify_supervisors({
        "type": "stock_bajo",
        "data": {
            "producto": producto_nombre,
            "stock_actual": stock_actual,
            "message": f"Stock bajo en {producto_nombre}: {stock_actual} unidades"
        }
    })
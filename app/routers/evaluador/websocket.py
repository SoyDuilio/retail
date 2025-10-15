from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.websocket_manager import manager

router = APIRouter()

@router.websocket("/ws/evaluador/{evaluador_id}")
async def websocket_evaluador(websocket: WebSocket, evaluador_id: int):
    """WebSocket para evaluadores - reciben notificaciones de nuevos pedidos"""
    await manager.connect(websocket, evaluador_id, "evaluador")
    
    try:
        while True:
            # Mantener conexión activa
            data = await websocket.receive_text()
            
            # Opcional: manejar mensajes del cliente
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(evaluador_id, "evaluador")
        print(f"Evaluador #{evaluador_id} desconectado")
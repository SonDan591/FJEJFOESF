from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

app = FastAPI()

# Список клиентов: словарь {"имя": websocket}
clients = {}

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    clients[username] = websocket
    try:
        while True:
            # Ожидаем формат: "кому:сообщение"
            data = await websocket.receive_text()
            if ":" in data:
                target, msg = data.split(":", 1)
                if target in clients:
                    await clients[target].send_text(f"Сообщение от {username}: {msg}")
                else:
                    await websocket.send_text(f"[Ошибка] Пользователь {target} не в сети.")
    except WebSocketDisconnect:
        del clients[username]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)

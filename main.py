import asyncio
import websockets
import os
import http
from websockets.server import ServerProtocol
class MyServerProtocol(ServerProtocol):
    def is_http_get(self, method):
        return method in ["GET", "HEAD"]

async def health_check(path, request_headers):
    if path in ["/", "/healthz", "/health_check"]:
        return http.HTTPStatus.OK, [], b"OK\n"
    return None
DB_FILE = "/tmp/chat_history.txt"
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        pass
def load_history():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines()]
    except Exception as e:
        print(f"Error loading file: {e}")
        return []
def save_to_file(message):
    try:
        with open(DB_FILE, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception as e:
        print(f"Error saving to file: {e}")
def clear_physical_history():
    try:
        with open(DB_FILE, "w") as f:
            f.truncate(0)
    except Exception as e:
        print(f"Error clearing file: {e}")
connected_clients = set()
message_history = load_history()
async def handle_connection(websocket):
    global message_history
    connected_clients.add(websocket)
    for past_msg in message_history:
        await websocket.send(past_msg)
    try:
        async for message in websocket:
            if message=="cuongvd2: /admin clear_history":
                message_history = []
                clear_physical_history()
                print("Admin cleared chat history.")
            elif message!="":
                formatted_msg = message.strip()
                message_history.append(formatted_msg)
                save_to_file(formatted_msg)
                if connected_clients:
                    tasks = [
                        client.send(formatted_msg)
                        for client in connected_clients
                        if client != websocket
                    ]
                    if tasks:
                        await asyncio.gather(*tasks)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)
async def main():
    port = int(os.environ.get("PORT", 8765))
    async with websockets.serve(
        handle_connection, 
        "0.0.0.0", 
        port, 
        process_request=health_check,
        create_protocol=MyServerProtocol
    ):
        print(f"Server is live on port {port}")
        await asyncio.Future()
if __name__ == "__main__":
    asyncio.run(main())

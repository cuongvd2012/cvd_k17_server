import asyncio
import websockets
import os
import http
async def health_check(path, request_headers):
    if path == "/healthz" or path == "/":
        return http.HTTPStatus.OK, [], b"OK\n"
    return None
DB_FILE = "chat_history.txt"
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        pass
def load_history():
    with open(DB_FILE, "r") as f:
        return [line.strip() for line in f.readlines()]
def save_to_file(message):
    with open(DB_FILE, "a") as f:
        f.write(message + "\n")
def clear_physical_history():
    with open(DB_FILE, "w") as f:
        f.truncate(0)
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
    async with websockets.serve(handle_connection, "0.0.0.0", port):
        print(f"Server is live on port {port}")
        await asyncio.Future()
if __name__ == "__main__":
    asyncio.run(main())


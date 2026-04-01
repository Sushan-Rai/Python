import asyncio
import json
import websockets
from websockets.exceptions import ConnectionClosed
import sqlite3
# db creation if not existing
db_conn = sqlite3.connect('chat_history.db', check_same_thread=False)
cursor = db_conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room TEXT,
        sender TEXT,
        content TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
db_conn.commit()
# the connected users and rooms
connected_users = {} 
rooms = {} 
# a function to send the users in the list
async def broadcast_user_list():
    user_list = [user_data for user_data in connected_users.values()]
    roster_msg = json.dumps({
        "type": "roster",
        "users": user_list
    })
    if connected_users:
        websockets.broadcast(connected_users.keys(), roster_msg)
# handle_client is a function called when the socket receives a successful connection
async def handle_client(websocket):
    try:
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")
            # init stores username and status
            if msg_type == "init":
                username = data.get("username")
                connected_users[websocket] = {"username": username, "status": "online"}
                print(f"[INFO] User '{username}' connected.")
                await broadcast_user_list()
            # the change in status
            elif msg_type == "status":
                new_status = data.get("status")
                if websocket in connected_users:
                    connected_users[websocket]["status"] = new_status
                    await broadcast_user_list()
            # joining a different room so we add the ws to the room
            elif msg_type == "join":
                room_name = data.get("room")
                if room_name not in rooms:
                    rooms[room_name] = set()
                
                rooms[room_name].add(websocket)
                print(f"[INFO] {connected_users[websocket]['username']} joined {room_name}")
                
                announce_msg = json.dumps({
                    "type": "system",
                    "content": f"Total users: {len(rooms[room_name])}. {connected_users[websocket]['username']} has joined the room."
                })
                websockets.broadcast(rooms[room_name], announce_msg)
            # message is added to the records and broadcasted
            elif msg_type == "message":
                room_name = data.get("room")
                sender_name = connected_users[websocket]["username"]
                content = data.get("content")
                
                if room_name in rooms:
                    cursor.execute("INSERT INTO messages (room, sender, content) VALUES (?, ?, ?)", 
                                   (room_name, sender_name, content))
                    db_conn.commit()

                    chat_msg = json.dumps({
                        "type": "message",
                        "room": room_name,
                        "sender": sender_name,
                        "content": content
                    })
                    websockets.broadcast(rooms[room_name], chat_msg)
            # dm is searched over the connected users and then the target is sent the message
            elif msg_type == "dm":
                target_username = data.get("target_user")
                target_ws = None
                for ws, user_data in connected_users.items():
                    if user_data["username"] == target_username:
                        target_ws = ws
                        break
                
                if target_ws:
                    dm_msg = json.dumps({
                        "type": "dm",
                        "sender": connected_users[websocket]["username"],
                        "content": data.get("content")
                    })
                    await target_ws.send(dm_msg)
            # for typing
            elif msg_type == "typing":
                room_name = data.get("room")
                if room_name in rooms:
                    typing_msg = json.dumps({
                        "type": "typing",
                        "sender": connected_users[websocket]["username"]
                    })
                    # dont show the user that he/she is typing
                    receivers = rooms[room_name] - {websocket}
                    websockets.broadcast(receivers, typing_msg)
            # search option to search the records and send the results
            elif msg_type == "search":
                search_query = data.get("query")
                cursor.execute("SELECT sender, content, timestamp FROM messages WHERE content LIKE ? LIMIT 50", 
                               (f"%{search_query}%",))
                results = cursor.fetchall()
                
                search_reply = json.dumps({
                    "type": "search_results",
                    "results": [{"sender": row[0], "content": row[1], "time": row[2]} for row in results]
                })
                await websocket.send(search_reply)

    except ConnectionClosed:
        pass
    
    finally:
        # remove the connected user from rooms and broadcast user list and send a message that the user left
        if websocket in connected_users:
            user_data = connected_users.pop(websocket)
            username = user_data["username"]
            
            for room_name, members in rooms.items():
                if websocket in members:
                    members.remove(websocket)
                    leave_msg = json.dumps({
                        "type": "system",
                        "content": f"{username} has left the room."
                    })
                    websockets.broadcast(members, leave_msg)
            
            print(f"[INFO] User '{username}' disconnected.")
            await broadcast_user_list()

async def main():
    server = await websockets.serve(handle_client, "localhost", 6789)
    print("[INFO] Chat server started on ws://localhost:6789")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
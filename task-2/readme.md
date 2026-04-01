## 2. Real-Time Chat Application with WebSockets

**Description:** Create a multi-room chat server using WebSockets. Support private messaging, typing indicators, user presence tracking, and message history persistence.

**Prerequisites:**

- TCP/IP and WebSocket protocol basics
- `asyncio` and `async/await` syntax
- `websockets` or `FastAPI WebSocket` library
- JSON serialization/deserialization
- SQLite or Redis for message persistence
- Basic HTML/JS for the client UI

**Use-Case:**

- Users connect via browser and join named chat rooms
- Support direct messages between two users
- Show real-time "typing..." indicators
- Display online/away/offline presence status
- Persist and search message history

**Expected Output:**

```
=== Server Log ===
[INFO] Chat server started on ws://0.0.0.0:8765
[INFO] User "alice" connected (session: a3f8c1)
[INFO] User "bob" connected (session: d92eb4)
[INFO] alice joined room #general
[INFO] bob joined room #general

=== Client View (Alice) ===
#general | 2 members online
──────────────────────────────
[14:32:01] bob: Hey team, anyone available for a code review?
[14:32:05] bob is typing...
[14:32:08] alice: Sure! Send me the PR link.
[14:32:15] bob: https://github.com/org/repo/pull/142
──────────────────────────────
Online: alice, bob | carol (away)

=== Private Message (Bob -> Alice) ===
[DM] bob -> alice: Thanks for the quick review!
[DM] alice -> bob: No problem!
```

**Installation**

- `pip install websockets`

**Execution**

- Created rooms for the users and direct message as well.
- shows 'User is typing..' 
- displays status of all users
- can search message history stored in db
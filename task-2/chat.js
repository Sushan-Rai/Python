let username = prompt("Enter your username:");
if (!username) username = "Anonymous_" + Math.floor(Math.random() * 1000);
// client side socket connection
const socket = new WebSocket(`ws://localhost:6789`);
let currentRoom = "#general";

let isTyping = false;
let myTypingTimeout;
let peerTypingTimeout;

socket.onopen = () => {
    console.log("Connected to the WebSocket server!");
    // authenticating user
    const authMessage = { type: "init", username: username };
    socket.send(JSON.stringify(authMessage));
    // joining currentRoom
    joinRoom(currentRoom);
};
// on message we filter using data type and populate it accordingly
socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    const chatbox = document.querySelector("#chatbox");
    const indicator = document.querySelector("#typing-indicator");
    const messageElement = document.createElement("div");

    switch (data.type) {
        // system message
        case "system":
            messageElement.className = "system-msg";
            messageElement.textContent = `[System]: ${data.content}`;
            chatbox.appendChild(messageElement);
            break;
        // broadcast message
        case "message":
            indicator.textContent = "";
            messageElement.textContent = `[${data.room}] ${data.sender}: ${data.content}`;
            chatbox.appendChild(messageElement);
            break;
        // direct message
        case "dm":
            messageElement.className = "dm-msg";
            messageElement.textContent = `[DM from ${data.sender}]: ${data.content}`;
            chatbox.appendChild(messageElement);
            break;
        //  to show someone is typing
        case "typing":
            indicator.textContent = `${data.sender} is typing...`;
            clearTimeout(peerTypingTimeout);
            peerTypingTimeout = setTimeout(() => {
                indicator.textContent = "";
            }, 2000);
            return;
        //  display the users
        case "roster":
            const userListDiv = document.getElementById("user-list");
            userListDiv.innerHTML = "<strong>Active Users:</strong><br>";
            data.users.forEach(user => {
                const icon = user.status === "online" ? "active" : "inactive";
                userListDiv.innerHTML += `<div>${icon} ${user.username}</div>`;
            });
            break;
        // search results wherein we get response after the query in the backend
        case "search_results":
            const resultsDiv = document.getElementById("search-results");
            resultsDiv.innerHTML = "<strong>Search Results:</strong><br>";
            if (data.results.length === 0) {
                resultsDiv.innerHTML += "No messages found.";
            } else {
                data.results.forEach(msg => {
                    resultsDiv.innerHTML += `<div>[${msg.time}] ${msg.sender}: ${msg.content}</div>`;
                });
            }
            break;

        default:
            console.log("Unknown message type:", data);
            return;
    }

    chatbox.scrollTop = chatbox.scrollHeight;
};
// sends a message to the server informing the query
function searchHistory(event) {
    // event.preventDefault()
    const query = document.getElementById("search-input").value;
    socket.send(JSON.stringify({ type: "search", query: query }));
}
// sends a message to the server informing change status
function changeStatus(event) {
    const status = document.getElementById("my-status").value;
    socket.send(JSON.stringify({ type: "status", status: status }));
}
// joined a room
function joinRoom(roomName) {
    const payload = { type: "join", room: roomName };
    socket.send(JSON.stringify(payload));
    document.getElementById('current-room-display').textContent = roomName;
}
// switching rooms
function switchRoom() {
    // event.preventDefault()
    const newRoomInput = document.getElementById('room-name');
    if (!newRoomInput.value.trim()) return;

    currentRoom = newRoomInput.value.trim();
    joinRoom(currentRoom);

    document.querySelector("#chatbox").innerHTML = "";
    newRoomInput.value = "";
}
// sending message
function sendMessage() {
    const input = document.getElementById('message');
    if (!input.value.trim()) return;

    const payload = {
        type: "message",
        room: currentRoom,
        content: input.value
    };

    socket.send(JSON.stringify(payload));
    input.value = "";

    isTyping = false;
    clearTimeout(myTypingTimeout);
}
// direct message
function sendDM() {
    const targetUser = document.getElementById('dm-user').value.trim();
    const dmContent = document.getElementById('dm-message').value.trim();

    if (!targetUser || !dmContent) return;

    const payload = {
        type: "dm",
        target_user: targetUser,
        content: dmContent
    };

    socket.send(JSON.stringify(payload));

    const chatbox = document.querySelector("#chatbox");
    const messageElement = document.createElement("div");
    messageElement.className = "dm-msg";
    messageElement.textContent = `[DM to ${targetUser}]: ${dmContent}`;
    chatbox.appendChild(messageElement);
    chatbox.scrollTop = chatbox.scrollHeight;

    document.getElementById('dm-message').value = "";
}

// typing indication send as type typing
function sendTypingIndicator() {
    if (!isTyping) {
        isTyping = true;
        const payload = { type: "typing", room: currentRoom };
        socket.send(JSON.stringify(payload));
    }

    clearTimeout(myTypingTimeout);
    myTypingTimeout = setTimeout(() => {
        isTyping = false;
    }, 1000);
}
// once enter is pressed the particular function is called
function handleEnter(event, actionFunction) {
    if (event.key === "Enter") {
        actionFunction();
    }
}
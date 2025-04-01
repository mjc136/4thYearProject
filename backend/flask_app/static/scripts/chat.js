let dotInterval;

function startTypingDots() {
    const dots = document.getElementById("dots");
    let count = 0;
    dotInterval = setInterval(() => {
        count = (count + 1) % 4;
        dots.textContent = ".".repeat(count);
    }, 400);
}

function stopTypingDots() {
    clearInterval(dotInterval);
    document.getElementById("dots").textContent = ".";
}

function typeBotMessage(text, container) {
    const bubble = document.createElement("div");
    bubble.className = "bubble bot-bubble";
    bubble.innerHTML = "<b>Bot:</b> ";
    container.appendChild(bubble);

    let i = 0;
    const speed = 30;

    const interval = setInterval(() => {
        if (i < text.length) {
            bubble.innerHTML += text.charAt(i);
            i++;
        } else {
            clearInterval(interval);
        }
        container.scrollTop = container.scrollHeight;
    }, speed);
}

async function sendMessage(msgOverride = null, auto = false) {
    const inputBox = document.getElementById("userInput");
    const sendButton = document.getElementById("sendButton");
    const message = msgOverride || inputBox.value.trim();
    const chatBox = document.getElementById("chatBox");
    const typing = document.getElementById("typingIndicator");

    if (!message) return;

    if (!auto) {
        chatBox.innerHTML += `<div class="bubble user-bubble"><b>You:</b> ${message}</div>`;
    }

    inputBox.value = "";
    inputBox.disabled = true;
    sendButton.disabled = true;
    typing.style.display = "block";
    startTypingDots();

    try {
        const response = await fetch("/send", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message })
        });

        const data = await response.json();

        stopTypingDots();
        typing.style.display = "none";
        inputBox.disabled = false;
        sendButton.disabled = false;
        inputBox.focus();

        if (data.reply) {
            typeBotMessage(data.reply, chatBox);
        } else if (data.error) {
            typeBotMessage(`⚠️ Error: ${data.error}`, chatBox);
        } else {
            typeBotMessage("⚠️ Unexpected response from bot.", chatBox);
        }

        if (data.attachments && data.attachments.length > 0) {
            data.attachments.forEach(att => {
                const card = att.content;
                chatBox.innerHTML += `
                <div class="card card-box my-2">
                    <div class="card-body">
                        <h5 class="card-title">${card.title || "[Card]"}</h5>
                        <p class="card-text">${card.text || card.subtitle || ""}</p>
                        ${card.buttons?.map(btn => `
                            <button class="btn btn-sm btn-outline-light me-2" onclick="sendQuickReply('${btn.value}')">${btn.title}</button>
                        `).join("") || ""}
                    </div>
                </div>`;
            });
        }

        chatBox.scrollTop = chatBox.scrollHeight;

    } catch (err) {
        stopTypingDots();
        typing.style.display = "none";
        inputBox.disabled = false;
        sendButton.disabled = false;
        typeBotMessage("⚠️ Could not reach the server.", chatBox);
    }
}

function sendQuickReply(value) {
    const input = document.getElementById("userInput");
    input.value = value;
    sendMessage();
}

document.getElementById("userInput").addEventListener("keypress", function (e) {
    if (e.key === "Enter") sendMessage();
});

// Auto-start welcome message
window.addEventListener("load", function () {
    sendMessage("__start__", true);
});

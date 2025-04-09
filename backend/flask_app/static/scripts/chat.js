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
    
    // Check if this is an example message
    if (text.startsWith("Example:") || text.startsWith("Tip:")) {
        bubble.className += " example-bubble"; // Add a special class for examples
        bubble.innerHTML = "<b>Bot:</b> <span class='example-text'>";
    } else {
        bubble.innerHTML = "<b>Bot:</b> ";
    }
    
    container.appendChild(bubble);

    let i = 0;
    const speed = 30;

    const interval = setInterval(() => {
        if (i < text.length) {
            if (text.startsWith("Example:") || text.startsWith("Tip:")) {
                // For examples, we add to the span
                const span = bubble.querySelector('.example-text');
                span.textContent += text.charAt(i);
            } else {
                // Normal message
                bubble.innerHTML += text.charAt(i);
            }
            i++;
        } else {
            clearInterval(interval);
            if (text.startsWith("Example:") || text.startsWith("Tip:")) {
                // Close the span
                const span = bubble.querySelector('.example-text');
                span.innerHTML += "</span>";
            }
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
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    inputBox.value = "";
    inputBox.disabled = true;
    sendButton.disabled = true;
    typing.style.display = "block";
    startTypingDots();
    
    let retryCount = 0;
    const maxRetries = 2;
    const retry = async () => {
        try {
            console.log(`Sending message to server (attempt ${retryCount + 1}/${maxRetries + 1})...`);
            const response = await fetch("/send", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message })
            });
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }

            const data = await response.json();
            console.log("Server response:", data);

            stopTypingDots();
            typing.style.display = "none";
            inputBox.disabled = false;
            sendButton.disabled = false;
            inputBox.focus();

            if (data.reply) {
                // Handle multiline responses by splitting on double newlines
                const messages = data.reply.split("\n\n").filter(msg => msg.trim());
                
                // Display each message separately
                for (const msg of messages) {
                    // Check for instruction messages (Step X of Y)
                    if (msg.startsWith("Step ") && msg.includes(" of ")) {
                        const stepDiv = document.createElement("div");
                        stepDiv.className = "step-indicator";
                        stepDiv.textContent = msg;
                        chatBox.appendChild(stepDiv);
                    } else {
                        // Normal bot message
                        typeBotMessage(msg, chatBox);
                    }
                    // Short delay between multiple messages for better user experience
                    if (messages.length > 1) {
                        await new Promise(resolve => setTimeout(resolve, 500));
                    }
                }
            } else if (data.error) {
                typeBotMessage(`⚠️ Error: ${data.error}`, chatBox);
            } else {
                typeBotMessage("⚠️ The bot is taking longer than expected to respond. Please try again.", chatBox);
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
            console.error("Fetch error:", err);
            
            if (retryCount < maxRetries) {
                retryCount++;
                console.log(`Retrying... (${retryCount}/${maxRetries})`);
                await new Promise(resolve => setTimeout(resolve, 1000)); // Wait before retry
                return retry();
            }
            
            stopTypingDots();
            typing.style.display = "none";
            inputBox.disabled = false;
            sendButton.disabled = false;
            
            if (err.message && err.message.includes("status: 502")) {
                typeBotMessage("⚠️ Bot service is currently unavailable. Please try again in a moment.", chatBox);
            } else {
                typeBotMessage("⚠️ Could not reach the server. Please check your connection and try again.", chatBox);
            }
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    };
    
    await retry();
}

function sendQuickReply(value) {
    const input = document.getElementById("userInput");
    input.value = value;
    sendMessage();
}

document.getElementById("userInput").addEventListener("keypress", function (e) {
    if (e.key === "Enter"){
        e.preventDefault();
        sendMessage();
    }
});

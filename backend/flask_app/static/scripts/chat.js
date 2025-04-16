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
    return new Promise(resolve => {
        console.log("Displaying bot message:", text);
        const bubble = document.createElement("div");
        bubble.className = "bubble bot-bubble";

        const prefix = document.createElement("b");
        prefix.textContent = "Bot: ";
        bubble.appendChild(prefix);

        const messageContent = document.createElement("span");
        bubble.appendChild(messageContent);

        if (text.startsWith("Example:") || text.startsWith("Tip:")) {
            bubble.className += " example-bubble";
            messageContent.className = "example-text";
        }

        container.appendChild(bubble);

        let i = 0;
        const speed = 30;

        const interval = setInterval(() => {
            if (i < text.length) {
                messageContent.textContent = text.substring(0, i + 1);
                i++;
            } else {
                clearInterval(interval);
                console.log("Finished displaying message:", text);
                container.scrollTop = container.scrollHeight;
                resolve(); // Resolve the promise after the typing is done
            }
        }, speed);
    });
}

async function sendMessage(msgOverride = null, auto = false) {
    const inputBox = document.getElementById("userInput");
    const sendButton = document.getElementById("sendButton");
    const message = msgOverride || inputBox.value.trim();
    const chatBox = document.getElementById("chatBox");
    const typing = document.getElementById("typingIndicator");
    const scenario = document.getElementById("scenarioType") ? document.getElementById("scenarioType").value : null;

    if (!message) return;

    console.log(`Sending message: "${message}", auto=${auto}, scenario=${scenario}`);

    if (!auto) {
        // Display user message in chat
        const userBubble = document.createElement("div");
        userBubble.className = "bubble user-bubble";
        userBubble.innerHTML = "<b>You:</b> " + message;
        chatBox.appendChild(userBubble);
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
                headers: { 
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ 
                    message,
                    scenario  // Include the scenario in request body
                })
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
                console.log("Parsed messages:", messages);
                
                if (messages.length === 0) {
                    console.warn("No valid messages found in reply");
                    typeBotMessage("I'm ready to help you practice your language skills!", chatBox);
                } else {
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
                }
            } else if (data.error) {
                console.error("Error from server:", data.error);
                typeBotMessage(`⚠️ Error: ${data.error}`, chatBox);
            } else {
                console.warn("Empty response from server");
                typeBotMessage("I'm here to help you practice. What would you like to talk about?", chatBox);
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
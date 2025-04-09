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
                typeBotMessage(data.reply, chatBox);
            } else if (data.error) {
                typeBotMessage(`⚠️ Error: ${data.error}`, chatBox);
            } else {
                // This could be the case causing "Unexpected response from bot"
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

// Returns appropriate scenario intro based on proficiency level
function getScenarioIntro(proficiency) {
    switch(proficiency.toLowerCase()) {
        case 'beginner':
            return "Imagine you just entered a taxi in a Spanish-speaking country. You need to communicate with the driver to get to your destination.";
        case 'intermediate':
            return "Imagine you are at a hotel reception in a French-speaking country. You need to book a room and discuss accommodations with the staff.";
        case 'advanced':
            return "Imagine you are attending a job interview in Portuguese. You need to showcase your skills and experience to make a good impression.";
        default:
            return "Get ready for your language practice scenario.";
    }
}

// Fetch user profile to get language and proficiency
async function fetchUserProfile() {
    try {
        const response = await fetch("/api/user/profile");
        if (!response.ok) {
            throw new Error("Could not fetch user profile");
        }
        return await response.json();
    } catch (error) {
        console.error("Error fetching profile:", error);
        return { language: "Spanish", proficiency: "beginner" };
    }
}

// Custom welcome message with scenario context
window.addEventListener("load", async function() {
    const chatBox = document.getElementById("chatBox");
    
    // Show initial welcome message
    chatBox.innerHTML = `
        <div class="bubble bot-bubble">
            <b>Bot:</b> Welcome to LingoLizard! 🦎
            <br><br>
            Loading your personalized scenario...
        </div>
    `;
    
    // Try to fetch user profile info
    let userProfile;
    try {
        userProfile = await fetchUserProfile();
    } catch (error) {
        userProfile = { language: "Spanish", proficiency: "beginner" };
    }
    
    // Determine the scenario based on proficiency
    const scenarioIntro = getScenarioIntro(userProfile.proficiency);
    const language = userProfile.language.charAt(0).toUpperCase() + userProfile.language.slice(1);
    
    // Add the complete welcome message with scenario context
    chatBox.innerHTML = `
        <div class="bubble bot-bubble">
            <b>Bot:</b> Welcome to LingoLizard! 🦎
            <br><br>
            You're practicing <strong>${language}</strong> at <strong>${userProfile.proficiency}</strong> level.
            <br><br>
            <strong>Scenario:</strong> ${scenarioIntro}
            <br><br>
            Type "start" when you're ready to begin!
        </div>
    `;
    
    // Don't automatically send "start" - let the user initiate the conversation
});

document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("chat-toggle");
  const chatBox = document.getElementById("chat-box");
  const sendBtn = document.getElementById("chat-send");
  const input = document.getElementById("chat-input");
  const messages = document.getElementById("chat-messages");

  if (!toggleBtn) return;

  toggleBtn.addEventListener("click", () => {
    chatBox.classList.toggle("d-none");
  });

  function appendMessage(role, text) {
    const wrapper = document.createElement("div");
    wrapper.className = role === "user" ? "chat-msg-user" : "chat-msg-assistant";
    wrapper.innerHTML = `<span class="chat-bubble ${role}">${text}</span>`;
    messages.appendChild(wrapper);
    messages.scrollTop = messages.scrollHeight;
  }

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;
    appendMessage("user", text);
    input.value = "";

    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });
    const data = await res.json();
    appendMessage("assistant", data.reply || data.error || "No response");
  }

  sendBtn.addEventListener("click", sendMessage);
  input.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
  });
});

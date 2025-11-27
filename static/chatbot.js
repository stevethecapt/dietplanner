// Ambil elemen panel
const chatbotPanel = document.getElementById("chatbotPanel");
const chatInput = document.getElementById("chatInput");
const chatMessages = document.getElementById("chatMessages");
const chatSendBtn = document.getElementById("chatSendBtn");

// Fungsi buka panel
function openChatbot() {
  chatbotPanel.classList.remove("hidden");
  setTimeout(() => {
    chatInput.focus();
  }, 200);
}

// Fungsi tutup panel
function closeChatbot() {
  chatbotPanel.classList.add("hidden");
}

// Fungsi kirim pesan
function sendMessage() {
  const msg = chatInput.value.trim();
  if (!msg) return;

  // Tambahkan pesan user
  const userMsg = document.createElement("div");
  userMsg.className = "chat-msg user";
  userMsg.textContent = msg;
  chatMessages.appendChild(userMsg);

  chatInput.value = "";
  chatMessages.scrollTop = chatMessages.scrollHeight;

  // Kirim ke backend Gemini API
  fetch("/api/chatbot", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question: msg }),
  })
    .then((res) => res.json())
    .then((data) => {
      const aiMsg = document.createElement("div");
      aiMsg.className = "chat-msg ai";
      if (data.answer) {
        aiMsg.textContent = data.answer;
      } else {
        aiMsg.textContent = data.error || "Maaf, terjadi kesalahan.";
      }
      chatMessages.appendChild(aiMsg);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    })
    .catch(() => {
      const aiMsg = document.createElement("div");
      aiMsg.className = "chat-msg ai";
      aiMsg.textContent = "Maaf, tidak dapat terhubung ke server.";
      chatMessages.appendChild(aiMsg);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    });
}

// Kirim chat dengan tombol Enter
chatInput.addEventListener("keydown", function (e) {
  if (e.key === "Enter") {
    e.preventDefault();
    chatSendBtn.click();
  }
});

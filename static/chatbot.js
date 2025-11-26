// Ambil elemen panel
const chatbotPanel = document.getElementById('chatbotPanel');
const chatInput = document.getElementById('chatInput');
const chatMessages = document.getElementById('chatMessages');

// Fungsi buka panel
function openChatbot() {
  chatbotPanel.classList.remove('hidden');
}

// Fungsi tutup panel
function closeChatbot() {
  chatbotPanel.classList.add('hidden');
}

// Fungsi kirim pesan
function sendMessage() {
  const msg = chatInput.value.trim();
  if (!msg) return;

  // Tambahkan pesan user
  const userMsg = document.createElement('div');
  userMsg.className = 'chat-msg user';
  userMsg.textContent = msg;
  chatMessages.appendChild(userMsg);

  chatInput.value = '';
  chatMessages.scrollTop = chatMessages.scrollHeight;

  // Simulasi balasan AI (sementara)
  setTimeout(() => {
    const aiMsg = document.createElement('div');
    aiMsg.className = 'chat-msg ai';
    aiMsg.textContent = "Ini balasan AI (contoh).";
    chatMessages.appendChild(aiMsg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }, 500);
}

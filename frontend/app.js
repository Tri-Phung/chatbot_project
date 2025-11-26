const API_BASE = window.API_BASE || "http://localhost:8000";
const HISTORY_KEY = "pt-chat-history";
const MEMORY_KEY = "pt-session-memory";

const state = {
  history: [],
  memory: {
    goal: null,
    experience: null,
    equipment: null,
    schedule: null,
    diet: null,
    limitations: null,
    body: null,
  },
};

const chatContainer = document.getElementById("chatContainer");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const imageInput = document.getElementById("imageInput");
const loadingIndicator = document.getElementById("loadingIndicator");
const clearHistoryBtn = document.getElementById("clearHistoryBtn");

function loadState() {
  const history = localStorage.getItem(HISTORY_KEY);
  if (history) {
    try {
      state.history = JSON.parse(history);
    } catch {
      state.history = [];
    }
  }
  const memory = localStorage.getItem(MEMORY_KEY);
  if (memory) {
    try {
      state.memory = JSON.parse(memory);
    } catch {
      /* ignore */
    }
  }
}

function saveState() {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(state.history));
  localStorage.setItem(MEMORY_KEY, JSON.stringify(state.memory));
}

function renderMessages() {
  chatContainer.innerHTML = "";
  state.history.forEach((message) => {
    const bubble = document.createElement("div");
    bubble.className = `message ${message.role}`;
    if (message.meta?.type === "guard") {
      bubble.classList.add("alert");
    }
    bubble.textContent = message.content;
    chatContainer.appendChild(bubble);
  });
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function appendMessage(role, content, meta = {}) {
  const entry = {
    role,
    content,
    meta,
    timestamp: new Date().toISOString(),
  };
  state.history.push(entry);
  saveState();
  renderMessages();
}

function toggleLoading(show) {
  const existingIndicator = document.querySelector('.typing-indicator');

  if (show) {
    // Remove existing indicator if any
    if (existingIndicator) existingIndicator.remove();

    // Create typing indicator bubble
    const typingBubble = document.createElement('div');
    typingBubble.className = 'message assistant typing-indicator';
    typingBubble.innerHTML = `
      <div class="typing-dots">
        <span></span>
        <span></span>
        <span></span>
      </div>
    `;

    chatContainer.appendChild(typingBubble);
    chatContainer.scrollTop = chatContainer.scrollHeight;
  } else {
    // Remove typing indicator
    if (existingIndicator) {
      existingIndicator.remove();
    }
  }
}

function buildApiMessages() {
  return state.history
    .filter((msg) => msg.role === "user" || msg.role === "assistant")
    .map((msg) => ({
      role: msg.role === "user" ? "user" : "assistant",
      content: msg.content,
    }));
}

function updateMemoryFromText(text) {
  const lower = text.toLowerCase();
  if (lower.includes("tăng cơ")) state.memory.goal = "tăng cơ";
  if (lower.includes("giảm mỡ") || lower.includes("giảm cân")) state.memory.goal = "giảm mỡ";
  if (lower.includes("giữ form") || lower.includes("giữ dáng")) state.memory.goal = "giữ form";
  if (lower.includes("mới tập") || lower.includes("beginner")) state.memory.experience = "mới tập";
  if (lower.includes("trung cấp") || lower.includes("intermediate")) state.memory.experience = "trung cấp";
  if (lower.includes("nâng cao") || lower.includes("advanced")) state.memory.experience = "nâng cao";
  if (lower.includes("không dụng cụ") || lower.includes("bodyweight")) state.memory.equipment = "tự do";
  if (lower.includes("phòng gym") || lower.includes("gym")) state.memory.equipment = "phòng gym";
  const scheduleMatch = text.match(/(\d+)\s*(buổi|ngày)/i);
  if (scheduleMatch) state.memory.schedule = `${scheduleMatch[1]} buổi/tuần`;
  if (lower.includes("ăn chay")) state.memory.diet = "ăn chay";
  if (lower.includes("ít carb")) state.memory.diet = "ít carb";
  if (lower.includes("đau") || lower.includes("chấn thương")) state.memory.limitations = "có hạn chế";
  const bodyMatch = text.match(/(\d{2,3})\s?kg/i);
  if (bodyMatch) state.memory.body = `${bodyMatch[1]} kg`;
  saveState();
}

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;
  appendMessage("user", text);
  updateMemoryFromText(text);
  userInput.value = "";
  const payload = { messages: buildApiMessages() };
  toggleLoading(true);
  try {
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Máy chủ trả về lỗi.");
    }
    appendMessage("assistant", data.reply, {
      type: data.guardrail_triggered ? "guard" : "chat",
    });
  } catch (error) {
    appendMessage("assistant", `⚠️ Xin lỗi, có lỗi xảy ra: ${error.message}`, { type: "error" });
  } finally {
    toggleLoading(false);
  }
}

async function sendImage() {
  const file = imageInput.files[0];
  if (!file) {
    alert("Vui lòng chọn ảnh bữa ăn trước.");
    return;
  }
  const note = userInput.value.trim();
  if (note) {
    updateMemoryFromText(note);
  }
  appendMessage("user", note ? `Ảnh bữa ăn + ghi chú: ${note}` : "Mình vừa gửi ảnh bữa ăn.", {
    type: "image",
  });
  userInput.value = "";
  const formData = new FormData();
  formData.append("image", file);
  if (note) formData.append("note", note);
  imageInput.value = "";
  toggleLoading(true);
  try {
    const response = await fetch(`${API_BASE}/api/analyze-meal`, {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Không phân tích được ảnh.");
    }
    appendMessage("assistant", data.reply, {
      type: "meal",
      followUp: data.needs_follow_up,
    });
  } catch (error) {
    appendMessage("assistant", `⚠️ Phân tích ảnh thất bại: ${error.message}`, { type: "error" });
  } finally {
    toggleLoading(false);
  }
}

async function finalizeMeal() {
  const clarifications = userInput.value.trim();
  if (!clarifications) {
    alert("Mô tả thông tin khẩu phần chi tiết trước khi hoàn tất.");
    return;
  }
  updateMemoryFromText(clarifications);
  appendMessage("user", `Hoàn tất khẩu phần: ${clarifications}`, { type: "finalize" });
  userInput.value = "";
  toggleLoading(true);
  try {
    const response = await fetch(`${API_BASE}/api/meal-finalize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ clarifications }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Không hoàn tất được dinh dưỡng.");
    }
    appendMessage("assistant", data.reply, { type: "meal-final" });
  } catch (error) {
    appendMessage("assistant", `⚠️ Không thể hoàn tất khẩu phần: ${error.message}`, { type: "error" });
  } finally {
    toggleLoading(false);
  }
}

function clearHistory() {
  if (!confirm("Xóa toàn bộ lịch sử trò chuyện?")) return;
  state.history = [];
  saveState();
  renderMessages();
}

function setupEvents() {
  sendBtn.addEventListener("click", sendMessage);
  imageInput.addEventListener("change", sendImage);
  clearHistoryBtn.addEventListener("click", clearHistory);
  userInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });
}

function bootstrap() {
  loadState();
  renderMessages();
  setupEvents();
  if (!state.history.length) {
    appendMessage(
      "assistant",
      "Xin chào! Mình là trợ lý PT & dinh dưỡng Lý Đức 2.0. Hãy cho mình biết mục tiêu, kinh nghiệm tập, dụng cụ, lịch tập, khẩu vị và chỉ số cơ thể để mình hỗ trợ chính xác nhé! Mình sẽ giúp bạn đô như Lý Đức nè!"
    );
  }
}

bootstrap();


async function askQuestion() {
  const input = document.getElementById("question-input");
  const chatBox = document.getElementById("chat-box");

  const question = input.value.trim();
  if (!question) return;

  addMessage(question, "user");
  input.value = "";

  addMessage("Thinking...", "bot", true);

  try {
  const res = await fetch("http://127.0.0.1:8000/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question })
  });

  const data = await res.json();
  console.log("API response:", data);  // 👈 Add this for debugging
  removeThinking();

  // If backend returned an error
  if (data.error) {
    addMessage(data.error, "bot");
    return;
  }

  console.log("Data Type: ", data.answer);

  // If structured result exists
  if (data.answer) {
    if (data.answer.type === "table") {
      addTable(data.answer.columns, data.answer.rows);
    } else if (data.answer.type === "text") {
      addMessage(data.answer.message, "bot");
    } else {
      addMessage("Unknown response format", "bot");
    }
  } else {
    addMessage("No result returned from server", "bot");
  }

} catch (err) {
  console.error("Fetch error:", err);
  removeThinking();
  addMessage("Error connecting to server", "bot");
}


function addMessage(text, role, thinking=false) {
  const chatBox = document.getElementById("chat-box");
  const msg = document.createElement("div");
  msg.className = `message ${role}`;
  if (thinking) msg.id = "thinking";
  msg.innerText = text;
  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function removeThinking() {
  const thinking = document.getElementById("thinking");
  if (thinking) thinking.remove();
}

function addTable(columns, rows) {
  const chatBox = document.getElementById("chat-box");

  const table = document.createElement("table");

  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  columns.forEach(col => {
    const th = document.createElement("th");
    th.innerText = col;
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);

  const tbody = document.createElement("tbody");
  rows.forEach(row => {
    const tr = document.createElement("tr");
    row.forEach(cell => {
      const td = document.createElement("td");
      td.innerText = cell;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });

  table.appendChild(thead);
  table.appendChild(tbody);

  const wrapper = document.createElement("div");
  wrapper.className = "message bot";
  wrapper.appendChild(table);

  chatBox.appendChild(wrapper);
  chatBox.scrollTop = chatBox.scrollHeight;
}}

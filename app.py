from flask import Flask, render_template, request, Response, jsonify
from prometheus_client import Counter, generate_latest
import uuid
from flipkart.data_ingestion import DataIngestor
from flipkart.rag_agent import RAGAgentBuilder
from dotenv import load_dotenv

load_dotenv()

# Prometheus metrics
REQUEST_COUNT  = Counter("http_requests_total",      "Total HTTP Requests")
PREDICTION_COUNT = Counter("model_predictions_total", "Total Model Predictions")


def create_app():
    app = Flask(__name__,
                template_folder="frontend/templates",
                static_folder="frontend/static")

    THREAD_ID = str(uuid.uuid4())
    print(f"[INFO] New chat thread created: {THREAD_ID}")

    vector_store = DataIngestor().ingest(load_existing=True)
    rag_agent    = RAGAgentBuilder(vector_store).build_agent()

    # ── inject the Flipkart HTML template on first run ──────────────────────
    import os
    tmpl_dir = os.path.join(app.root_path, "frontend", "templates")
    os.makedirs(tmpl_dir, exist_ok=True)

    #with open(os.path.join(tmpl_dir, "index.html"), "w") as f:
    with open(os.path.join(tmpl_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Flipkart Product Assistant</title>
  <link rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"/>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    /* ── Reset ─────────────────────────────────────── */
    * { margin:0; padding:0; box-sizing:border-box; }
    body {
      font-family: 'Segoe UI', Arial, sans-serif;
      background: #f1f3f6;
      display: flex;
      flex-direction: column;
      height: 100vh;
    }

    /* ── Navbar ─────────────────────────────────────── */
    .navbar {
      background: #2874f0;
      padding: 0 24px;
      height: 56px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      box-shadow: 0 2px 6px rgba(0,0,0,.25);
      position: sticky; top: 0; z-index: 100;
    }
    .navbar-left { display:flex; align-items:center; gap:6px; }
    .navbar-logo {
      font-size: 22px; font-weight: 800;
      color: #fff; letter-spacing: -0.5px;
    }
    .navbar-logo span { color: #ffe500; font-style: italic; }
    .navbar-tagline {
      color: #ffe500; font-size: 11px;
      font-style: italic; margin-top: 2px;
    }
    .navbar-search {
      flex: 1; max-width: 540px; margin: 0 32px;
      display: flex; height: 36px;
    }
    .navbar-search input {
      flex: 1; padding: 0 14px;
      border: none; border-radius: 2px 0 0 2px;
      font-size: 14px; outline: none;
    }
    .navbar-search button {
      background: #ffe500; border: none;
      padding: 0 16px; border-radius: 0 2px 2px 0;
      cursor: pointer; color: #2874f0; font-size: 16px;
    }
    .navbar-right { display:flex; gap:28px; align-items:center; }
    .navbar-right a {
      color: #fff; text-decoration: none;
      font-size: 14px; font-weight: 500;
    }

    /* ── Layout ─────────────────────────────────────── */
    .main {
      display: flex;
      flex: 1;
      overflow: hidden;
    }

    /* ── Sidebar ─────────────────────────────────────── */
    .sidebar {
      width: 240px; background: #fff;
      border-right: 1px solid #e0e0e0;
      padding: 20px 16px;
      overflow-y: auto;
    }
    .sidebar h3 {
      color: #2874f0; font-size: 13px;
      text-transform: uppercase; letter-spacing: 1px;
      margin-bottom: 12px;
    }
    .sidebar ul { list-style: none; }
    .sidebar ul li {
      padding: 8px 10px; font-size: 13px;
      color: #212121; cursor: pointer;
      border-radius: 4px; margin-bottom: 4px;
      transition: background .2s;
    }
    .sidebar ul li:hover { background: #e8f0fe; color: #2874f0; }
    .sidebar ul li i { margin-right: 8px; color: #2874f0; }
    .sidebar-badge {
      background: #ffe500; color: #212121;
      font-size: 10px; font-weight: 700;
      padding: 2px 6px; border-radius: 10px;
      margin-left: 6px;
    }

    /* ── Chat area ───────────────────────────────────── */
    .chat-container {
      flex: 1; display: flex; flex-direction: column;
      overflow: hidden;
    }
    .chat-header {
      background: #fff;
      padding: 14px 24px;
      border-bottom: 1px solid #e0e0e0;
      display: flex; align-items: center; gap: 12px;
    }
    .chat-header-icon {
      width: 42px; height: 42px;
      background: #2874f0; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      color: #ffe500; font-size: 20px;
    }
    .chat-header-info h2 { font-size: 16px; color: #212121; }
    .chat-header-info p  { font-size: 12px; color: #878787; }
    .status-dot {
      width: 8px; height: 8px;
      background: #26a541; border-radius: 50%;
      display: inline-block; margin-right: 4px;
    }

    /* ── Messages ────────────────────────────────────── */
    .messages {
      flex: 1; overflow-y: auto;
      padding: 24px; display: flex;
      flex-direction: column; gap: 16px;
      background: #f1f3f6;
    }
    .message { display: flex; gap: 10px; max-width: 75%; }
    .message.user  { align-self: flex-end;  flex-direction: row-reverse; }
    .message.bot   { align-self: flex-start; }

    .avatar {
      width: 36px; height: 36px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 16px; flex-shrink: 0;
    }
    .avatar.bot  { background: #2874f0; color: #ffe500; }
    .avatar.user { background: #ffe500; color: #2874f0; font-weight: 700; }

    .bubble {
      padding: 12px 16px; border-radius: 12px;
      font-size: 14px; line-height: 1.6; max-width: 100%;
    }
    .bubble.bot {
      background: #fff;
      border: 1px solid #e0e0e0;
      border-top-left-radius: 2px;
      color: #212121;
      box-shadow: 0 1px 3px rgba(0,0,0,.08);
    }
    .bubble.user {
      background: #2874f0; color: #fff;
      border-top-right-radius: 2px;
    }
    .bubble-time {
      font-size: 10px; color: #878787;
      margin-top: 4px; text-align: right;
    }

    /* Welcome card */
    .welcome-card {
      background: #fff; border-radius: 8px;
      padding: 20px 24px; text-align: center;
      border: 1px solid #e0e0e0;
      box-shadow: 0 2px 6px rgba(0,0,0,.06);
      margin: auto;
    }
    .welcome-card h2 { color: #2874f0; font-size: 20px; margin-bottom: 8px; }
    .welcome-card p  { color: #878787; font-size: 13px; margin-bottom: 16px; }
    .suggestion-chips { display:flex; flex-wrap:wrap; gap:8px; justify-content:center; }
    .chip {
      background: #e8f0fe; color: #2874f0;
      border: 1px solid #c5d8ff;
      padding: 6px 14px; border-radius: 20px;
      font-size: 12px; cursor: pointer;
      transition: background .2s;
    }
    .chip:hover { background: #2874f0; color: #fff; }

    /* Typing indicator */
    .typing { display:none; align-self:flex-start; }
    .typing .bubble {
      display: flex; gap: 4px;
      align-items: center; padding: 14px 16px;
    }
    .dot {
      width: 8px; height: 8px;
      background: #2874f0; border-radius: 50%;
      animation: bounce 1.2s infinite;
    }
    .dot:nth-child(2) { animation-delay:.2s; }
    .dot:nth-child(3) { animation-delay:.4s; }
    @keyframes bounce {
      0%,60%,100% { transform:translateY(0); }
      30%          { transform:translateY(-6px); }
    }

    /* ── Input bar ───────────────────────────────────── */
    .input-area {
      background: #fff;
      padding: 16px 24px;
      border-top: 1px solid #e0e0e0;
      display: flex; gap: 12px; align-items: center;
    }
    .input-area input {
      flex: 1; padding: 12px 18px;
      border: 2px solid #e0e0e0; border-radius: 24px;
      font-size: 14px; outline: none;
      transition: border-color .2s;
    }
    .input-area input:focus { border-color: #2874f0; }
    .send-btn {
      background: #2874f0; color: #fff;
      border: none; border-radius: 50%;
      width: 46px; height: 46px;
      font-size: 18px; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      transition: background .2s, transform .1s;
    }
    .send-btn:hover   { background: #1a5ed4; }
    .send-btn:active  { transform: scale(.93); }

    /* ── Scrollbar ───────────────────────────────────── */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #f1f3f6; }
    ::-webkit-scrollbar-thumb { background: #c5d8ff; border-radius: 3px; }
  </style>
</head>
<body>

<!-- NAVBAR -->
<nav class="navbar">
  <div class="navbar-left">
    <div>
      <div class="navbar-logo">Flipkart<span>✦</span></div>
      <div class="navbar-tagline">Explore Plus</div>
    </div>
  </div>
  <div class="navbar-search">
    <input type="text" placeholder="Search for products, brands and more"/>
    <button><i class="fas fa-search"></i></button>
  </div>
  <div class="navbar-right">
    <a href="#"><i class="fas fa-user"></i> Login</a>
    <a href="#"><i class="fas fa-shopping-cart"></i> Cart</a>
  </div>
</nav>

<!-- MAIN -->
<div class="main">

  <!-- SIDEBAR -->
  <aside class="sidebar">
    <h3>Audio Products</h3>
    <ul>
      <li onclick="sendChip('Best BoAt Rockerz 235v2 review')">
        <i class="fas fa-headphones"></i>BoAt Rockerz
        <span class="sidebar-badge">HOT</span>
      </li>
      <li onclick="sendChip('Realme Buds Wireless review')">
        <i class="fas fa-headphones-alt"></i>Realme Buds Wireless
      </li>
      <li onclick="sendChip('OnePlus Bullets Wireless Z review')">
        <i class="fas fa-headphones"></i>OnePlus Bullets Z
      </li>
      <li onclick="sendChip('BoAt Airdopes 131 review')">
        <i class="fas fa-assistive-listening-systems"></i>BoAt Airdopes 131
      </li>
      <li onclick="sendChip('Realme Buds 2 wired headset review')">
        <i class="fas fa-music"></i>Realme Buds 2
      </li>
      <li onclick="sendChip('OnePlus Bullets Z Bass Edition review')">
        <i class="fas fa-volume-up"></i>OnePlus Bass Edition
      </li>
      <li onclick="sendChip('U and I Titanic Neckband review')">
        <i class="fas fa-headset"></i>U&amp;I Titanic
      </li>
      <li onclick="sendChip('BoAt BassHeads 100 review')">
        <i class="fas fa-plug"></i>BoAt BassHeads 100
      </li>
      <li onclick="sendChip('Realme Buds Q earbuds review')">
        <i class="fas fa-podcast"></i>Realme Buds Q
      </li>
    </ul>
  </aside>

  <!-- CHAT -->
  <div class="chat-container">
    <div class="chat-header">
      <div class="chat-header-icon"><i class="fas fa-robot"></i></div>
      <div class="chat-header-info">
        <h2>Flipkart Product Recommender</h2>
        <p><span class="status-dot"></span>Online · AI-Powered Chatbot</p>
      </div>
    </div>

    <div class="messages" id="messages">
      <!-- Welcome card -->
      <div class="welcome-card" id="welcomeCard">
        <h2>🛒 Welcome to Flipkart Product Recommender!</h2>
        <p>Ask me about products — reviews, comparisons &amp; recommendations powered by AI!</p>
        <div class="suggestion-chips">
          <div class="chip" onclick="sendChip('Best Bluetooth neckband under 1500')">🎵 Best Neckbands</div>
          <div class="chip" onclick="sendChip('Compare BoAt vs OnePlus earphones')">⚖️ BoAt vs OnePlus</div>
          <div class="chip" onclick="sendChip('Best earbuds with good bass')">🔊 Best Bass Earbuds</div>
          <div class="chip" onclick="sendChip('Which earphone has best battery backup')">🔋 Best Battery Life</div>
          <div class="chip" onclick="sendChip('Best wireless earphones for calling')">📞 Best for Calls</div>
          <div class="chip" onclick="sendChip('Realme Buds vs BoAt Rockerz comparison')">🆚 Realme vs BoAt</div>
        </div>
      </div>

      <!-- Typing indicator -->
      <div class="message bot typing" id="typing">
        <div class="avatar bot"><i class="fas fa-robot"></i></div>
        <div class="bubble bot">
          <div class="dot"></div><div class="dot"></div><div class="dot"></div>
        </div>
      </div>
    </div>

    <!-- INPUT -->
    <div class="input-area">
      <input type="text" id="userInput"
             placeholder="Ask about a product, price, or comparison…"
             onkeypress="if(event.key==='Enter') sendMessage()"/>
      <button class="send-btn" onclick="sendMessage()">
        <i class="fas fa-paper-plane"></i>
      </button>
    </div>
  </div>
</div>

<script>
  function getTime() {
    return new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
  }

  function appendMessage(role, text) {
    const msgs = document.getElementById('messages');
    const typing = document.getElementById('typing');

    const div = document.createElement('div');
    div.className = `message ${role}`;

    const avatar = role === 'user'
      ? `<div class="avatar user"><i class="fas fa-user"></i></div>`
      : `<div class="avatar bot"><i class="fas fa-robot"></i></div>`;

    div.innerHTML = `
      ${avatar}
      <div>
        <div class="bubble ${role}">${text}</div>
        <div class="bubble-time">${getTime()}</div>
      </div>`;

    msgs.insertBefore(div, typing);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function sendChip(text) {
    document.getElementById('userInput').value = text;
    sendMessage();
  }

  async function sendMessage() {
    const input   = document.getElementById('userInput');
    const typing  = document.getElementById('typing');
    const welcome = document.getElementById('welcomeCard');
    const text    = input.value.trim();
    if (!text) return;

    if (welcome) welcome.remove();

    appendMessage('user', text);
    input.value = '';

    typing.style.display = 'flex';
    document.getElementById('messages').scrollTop = 99999;

    try {
      const res  = await fetch('/get', {
        method: 'POST',
        headers: {'Content-Type':'application/x-www-form-urlencoded'},
        body: `msg=${encodeURIComponent(text)}`
      });
      const reply = await res.text();
      typing.style.display = 'none';
      appendMessage('bot', marked.parse(reply));
    } catch (e) {
      typing.style.display = 'none';
      appendMessage('bot', '⚠️ Sorry, something went wrong. Please try again.');
    }
  }
</script>
</body>
</html>
""")

    # ── Routes ──────────────────────────────────────────────────────────────
    @app.route("/")
    def index():
        REQUEST_COUNT.inc()
        return render_template("index.html")

    @app.route("/get", methods=["POST"])
    def get_response():
        REQUEST_COUNT.inc()
        user_input = request.form["msg"]

        response = rag_agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config={"configurable": {"thread_id": THREAD_ID}}
        )
        PREDICTION_COUNT.inc()

        if not response.get("messages"):
            return "Sorry, I couldn't find relevant product information."
        return response["messages"][-1].content

    @app.route("/health")
    def health():
        return jsonify({"status": "healthy"}), 200

    @app.route("/metrics")
    def metrics():
        return Response(generate_latest(), mimetype="text/plain")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
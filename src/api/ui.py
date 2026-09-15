"""Interactive Web UI component for FInee.ai RAG Streaming & Citation Display."""

HTML_CHAT_UI = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FInee.ai - Streaming RAG & Citation Viewer</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0b0f19;
            --bg-card: rgba(22, 30, 49, 0.7);
            --bg-card-hover: rgba(30, 41, 67, 0.8);
            --accent-glow: #6366f1;
            --accent-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
            --accent-cyan: #06b6d4;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --border-color: rgba(255, 255, 255, 0.1);
            --border-highlight: rgba(99, 102, 241, 0.3);
            --error-bg: rgba(239, 68, 68, 0.15);
            --error-border: rgba(239, 68, 68, 0.4);
            --error-text: #fca5a5;
            --font-main: 'Inter', system-ui, -apple-system, sans-serif;
            --font-code: 'JetBrains Mono', monospace;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-family: var(--font-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 2rem 1rem;
            background-image: 
                radial-gradient(circle at 15% 15%, rgba(99, 102, 241, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 85% 85%, rgba(168, 85, 247, 0.12) 0%, transparent 40%);
        }

        .container {
            width: 100%;
            max-width: 900px;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        header {
            text-align: center;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border-color);
        }

        .brand {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.5rem;
        }

        .brand-badge {
            background: var(--accent-gradient);
            padding: 0.25rem 0.6rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        h1 {
            font-size: 2.2rem;
            font-weight: 800;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.4rem;
        }

        .subtitle {
            color: var(--text-secondary);
            font-size: 0.95rem;
        }

        .preset-queries {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1rem;
            justify-content: center;
        }

        .chip {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 0.4rem 0.8rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .chip:hover {
            background: rgba(99, 102, 241, 0.2);
            border-color: var(--border-highlight);
            color: var(--text-primary);
            transform: translateY(-1px);
        }

        .chip.danger:hover {
            background: rgba(239, 68, 68, 0.2);
            border-color: var(--error-border);
        }

        .input-card {
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1.25rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }

        .input-group {
            display: flex;
            gap: 0.75rem;
        }

        input[type="text"] {
            flex: 1;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color);
            border-radius: 0.75rem;
            padding: 0.85rem 1.1rem;
            color: var(--text-primary);
            font-size: 0.95rem;
            font-family: var(--font-main);
            outline: none;
            transition: border-color 0.2s;
        }

        input[type="text"]:focus {
            border-color: var(--accent-glow);
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
        }

        button.send-btn {
            background: var(--accent-gradient);
            border: none;
            border-radius: 0.75rem;
            color: #fff;
            padding: 0 1.5rem;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: opacity 0.2s, transform 0.1s;
        }

        button.send-btn:hover {
            opacity: 0.95;
            transform: translateY(-1px);
        }

        button.send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        .status-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-top: 0.5rem;
            min-height: 1.5rem;
        }

        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
        }

        .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--text-muted);
        }

        .dot.active {
            background: #10b981;
            box-shadow: 0 0 8px #10b981;
            animation: pulse 1.5s infinite;
        }

        .dot.error {
            background: #ef4444;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.4; }
            100% { opacity: 1; }
        }

        .output-card {
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1.5rem;
            min-height: 250px;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .section-header {
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .answer-area {
            font-size: 1.05rem;
            line-height: 1.7;
            color: var(--text-primary);
            white-space: pre-wrap;
            position: relative;
        }

        .cursor {
            display: inline-block;
            width: 8px;
            height: 18px;
            background: var(--accent-cyan);
            margin-left: 2px;
            vertical-align: middle;
            animation: blink 0.8s infinite;
        }

        @keyframes blink {
            50% { opacity: 0; }
        }

        .citation-badge {
            display: inline-flex;
            align-items: center;
            background: rgba(99, 102, 241, 0.2);
            color: var(--accent-cyan);
            border: 1px solid rgba(6, 182, 212, 0.4);
            border-radius: 4px;
            padding: 0.1rem 0.4rem;
            font-size: 0.8rem;
            font-weight: 600;
            font-family: var(--font-code);
            margin: 0 0.2rem;
            cursor: pointer;
            transition: all 0.2s;
        }

        .citation-badge:hover {
            background: rgba(6, 182, 212, 0.3);
            color: #fff;
            transform: scale(1.05);
        }

        .sources-section {
            border-top: 1px dashed var(--border-color);
            padding-top: 1.25rem;
        }

        .sources-grid {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        details.source-card {
            background: rgba(0, 0, 0, 0.25);
            border: 1px solid var(--border-color);
            border-radius: 0.75rem;
            overflow: hidden;
            transition: border-color 0.2s;
        }

        details.source-card[open] {
            border-color: var(--border-highlight);
            background: rgba(0, 0, 0, 0.4);
        }

        summary.source-summary {
            padding: 0.75rem 1rem;
            font-size: 0.9rem;
            font-weight: 500;
            color: var(--text-secondary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
            user-select: none;
        }

        summary.source-summary:hover {
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.03);
        }

        .source-tag {
            font-family: var(--font-code);
            color: var(--accent-cyan);
            font-weight: 700;
            margin-right: 0.5rem;
        }

        .source-doc {
            color: var(--text-primary);
            font-weight: 600;
        }

        .source-meta {
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        .source-content {
            padding: 0.75rem 1rem 1rem 1rem;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 0.88rem;
            color: #cbd5e1;
            line-height: 1.6;
            background: rgba(15, 23, 42, 0.6);
        }

        .alert-error {
            background: var(--error-bg);
            border: 1px solid var(--error-border);
            color: var(--error-text);
            border-radius: 0.75rem;
            padding: 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            animation: fadeIn 0.3s ease-in-out;
        }

        .alert-error p {
            font-size: 0.9rem;
            font-weight: 500;
        }

        .retry-btn {
            background: rgba(239, 68, 68, 0.3);
            border: 1px solid var(--error-border);
            color: #fff;
            padding: 0.4rem 0.9rem;
            border-radius: 0.5rem;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .retry-btn:hover {
            background: rgba(239, 68, 68, 0.5);
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-4px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .empty-placeholder {
            color: var(--text-muted);
            font-style: italic;
            font-size: 0.95rem;
        }
    </style>
</head>
<body>

<div class="container">
    <header>
        <div class="brand">
            <span class="brand-badge">FInee.ai RAG</span>
            <span style="font-size: 0.85rem; color: var(--text-muted);">Compliance Engine v1.0</span>
        </div>
        <h1>Streaming Responses & Citation Display</h1>
        <p class="subtitle">Real-time progressive token streaming with interactive source evidence attribution</p>
        
        <div class="preset-queries">
            <button class="chip" onclick="selectQuery('What is an expense ratio?')">What is an expense ratio?</button>
            <button class="chip" onclick="selectQuery('How do equity funds invest?')">How do equity funds invest?</button>
            <button class="chip" onclick="selectQuery('How do interest rates affect debt funds?')">How do interest rates affect debt funds?</button>
            <button class="chip danger" onclick="selectQuery('Simulate Error')">⚠️ Test Error Stream</button>
        </div>
    </header>

    <main style="display: flex; flex-direction: column; gap: 1.5rem;">
        <div class="input-card">
            <form id="chatForm" onsubmit="handleQuery(event)" class="input-group">
                <input type="text" id="questionInput" placeholder="Ask a financial question..." value="What is an expense ratio?" required autocomplete="off">
                <button type="submit" id="sendBtn" class="send-btn">
                    <span>Ask RAG</span>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
                </button>
            </form>
            <div class="status-bar">
                <div class="status-indicator">
                    <span id="statusDot" class="dot"></span>
                    <span id="statusText">Ready</span>
                </div>
                <div id="metricText"></div>
            </div>
        </div>

        <div id="errorAlert" class="alert-error" style="display: none;">
            <p id="errorMessage">The answer stopped streaming. Please try again.</p>
            <button class="retry-btn" onclick="retryQuery()">Retry</button>
        </div>

        <div class="output-card">
            <div>
                <div class="section-header">
                    <span>Generated RAG Answer</span>
                    <span id="tokenCounter" style="font-family: var(--font-code); text-transform: none;"></span>
                </div>
                <div id="answerArea" class="answer-area">
                    <span class="empty-placeholder">Ask a question above to stream a compliance-grounded response.</span>
                </div>
            </div>

            <div id="sourcesContainer" class="sources-section" style="display: none;">
                <div class="section-header">
                    <span>Cited Evidence Sources</span>
                    <span id="sourceCount" style="font-family: var(--font-code);"></span>
                </div>
                <div id="sourcesGrid" class="sources-grid"></div>
            </div>
        </div>
    </main>
</div>

<script>
    let isStreaming = false;
    let lastQuestion = "";
    let receivedSources = [];
    let startTime = 0;

    function selectQuery(text) {
        document.getElementById('questionInput').value = text;
        if (!isStreaming) {
            handleQuery(new Event('submit'));
        }
    }

    function retryQuery() {
        if (lastQuestion) {
            document.getElementById('questionInput').value = lastQuestion;
            handleQuery(new Event('submit'));
        }
    }

    function setStatus(state, message) {
        const dot = document.getElementById('statusDot');
        const text = document.getElementById('statusText');
        dot.className = 'dot ' + state;
        text.innerText = message;
    }

    function renderCitations(sources) {
        const container = document.getElementById('sourcesContainer');
        const grid = document.getElementById('sourcesGrid');
        const countSpan = document.getElementById('sourceCount');

        if (!sources || sources.length === 0) {
            container.style.display = 'none';
            return;
        }

        receivedSources = sources;
        grid.innerHTML = '';
        countSpan.innerText = sources.length + ' source(s)';

        sources.forEach((source) => {
            const card = document.createElement('details');
            card.className = 'source-card';
            card.id = 'source-detail-' + source.id;

            const summary = document.createElement('summary');
            summary.className = 'source-summary';
            summary.innerHTML = `
                <div>
                    <span class="source-tag">${source.label}</span>
                    <span class="source-doc">${source.document}</span>
                </div>
                <div class="source-meta">
                    ID: ${source.chunk_id} | Chunk: ${source.chunk_index} | Score: ${(source.score || 0).toFixed(3)}
                </div>
            `;

            const content = document.createElement('div');
            content.className = 'source-content';
            content.innerHTML = `
                <p style="margin-bottom: 0.4rem; color: var(--text-muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">Retrieved Chunk Content (${source.section || 'General'}):</p>
                <p style="font-family: var(--font-main); color: #e2e8f0;">"${source.text}"</p>
            `;

            card.appendChild(summary);
            card.appendChild(content);
            grid.appendChild(card);
        });

        container.style.display = 'block';
    }

    function highlightCitationSource(label) {
        const index = label.replace('[', '').replace(']', '');
        const targetCard = document.getElementById('source-detail-source-' + index);
        if (targetCard) {
            targetCard.open = true;
            targetCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    async function handleQuery(event) {
        if (event) event.preventDefault();
        
        const input = document.getElementById('questionInput');
        const question = input.value.trim();
        if (!question || isStreaming) return;

        lastQuestion = question;
        isStreaming = true;
        startTime = Date.now();

        // UI Reset
        document.getElementById('sendBtn').disabled = true;
        document.getElementById('errorAlert').style.display = 'none';
        document.getElementById('sourcesContainer').style.display = 'none';
        document.getElementById('sourcesGrid').innerHTML = '';
        
        const answerArea = document.getElementById('answerArea');
        answerArea.innerHTML = '<span class="cursor"></span>';

        setStatus('active', 'Retrieving context & streaming tokens...');

        try {
            const response = await fetch('/query/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
            });

            if (!response.ok || !response.body) {
                throw new Error('Could not connect to the streaming service.');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let currentAnswerText = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\\n');

                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;
                    
                    try {
                        const eventData = JSON.parse(line.slice(6));

                        if (eventData.type === 'citations') {
                            renderCitations(eventData.sources);
                        }

                        if (eventData.type === 'token') {
                            currentAnswerText += eventData.text;
                            // Format citation brackets nicely
                            const formattedHtml = currentAnswerText.replace(/(\\[\\d+\\])/g, (match) => {
                                return `<span class="citation-badge" onclick="highlightCitationSource('${match}')">${match}</span>`;
                            });
                            answerArea.innerHTML = formattedHtml + '<span class="cursor"></span>';
                        }

                        if (eventData.type === 'error') {
                            throw new Error(eventData.message);
                        }

                        if (eventData.type === 'done') {
                            const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
                            setStatus('', 'Stream completed (' + elapsed + 's)');
                        }
                    } catch (e) {
                        if (e.message.includes('JSON')) continue;
                        throw e;
                    }
                }
            }

            // Remove streaming cursor on finish
            const cursor = answerArea.querySelector('.cursor');
            if (cursor) cursor.remove();

        } catch (error) {
            console.error('Streaming error:', error);
            document.getElementById('errorMessage').innerText = error.message || 'The answer stopped streaming. Please retry.';
            document.getElementById('errorAlert').style.display = 'flex';
            setStatus('error', 'Stream interrupted');
            
            // Keep cursor off but preserve partial text
            const cursor = answerArea.querySelector('.cursor');
            if (cursor) cursor.remove();
        } finally {
            isStreaming = false;
            document.getElementById('sendBtn').disabled = false;
        }
    }
</script>
</body>
</html>
"""

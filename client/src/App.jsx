import { useState, useEffect, useRef } from 'react'
import './App.css'

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [status, setStatus] = useState('disconnected'); // 'connected', 'working', 'disconnected'
  const [screenshot, setScreenshot] = useState(null);
  const [isWorking, setIsWorking] = useState(false);

  const ws = useRef(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const connect = () => {
      let host = import.meta.env.VITE_WS_BACKEND_URL || (import.meta.env.DEV ? 'localhost:8000' : window.location.host);

      // Clean up the host (strip protocol if accidentally included)
      host = host.replace(/^https?:\/\//, '').replace(/^wss?:\/\//, '');

      // Determine if we should use secure websockets
      const isLocal = host.includes('localhost') || host.includes('127.0.0.1');
      const protocol = isLocal ? 'ws' : 'wss';
      const wsUrl = `${protocol}://${host}/ws`;

      console.log(`[WS] Attempting connection to: ${wsUrl} (derived from host: ${host})`);
      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log(`[WS] Connection established successfully with: ${wsUrl}`);
        setStatus('connected');
      };
      socket.onclose = (event) => {
        console.log(`[WS] Connection closed. Code: ${event.code}, Reason: ${event.reason || 'None'}`);
        setStatus('disconnected');
        setTimeout(connect, 3000);
      };
      socket.onerror = (error) => {
        console.error(`[WS] Connection error occurred:`, error);
        setStatus('disconnected');
      };

      socket.onmessage = (e) => {
        console.log(`[WS] Message received:`, e.data.substring(0, 100) + '...');
        const event = JSON.parse(e.data);
        handleEvent(event);
      };

      ws.current = socket;
    };

    connect();

    return () => {
      if (ws.current) ws.current.close();
    };
  }, []);

  const handleEvent = (event) => {
    switch (event.type) {
      case 'thinking':
        setMessages(prev => {
          // Remove the temporary thinking indicator if it exists
          const filtered = prev.filter(m => m.type !== 'thinking_indicator');
          return [...filtered, { type: 'agent', content: event.content }];
        });
        break;
      case 'tool_call':
        setMessages(prev => {
          const filtered = prev.filter(m => m.type !== 'thinking_indicator');
          return [...filtered, {
            type: 'tool_call',
            name: event.name,
            args: event.args
          }, { type: 'thinking_indicator' }];
        });
        break;
      case 'tool_result':
        setMessages(prev => {
          const filtered = prev.filter(m => m.type !== 'thinking_indicator');
          return [...filtered, {
            type: 'tool_result',
            name: event.name,
            content: event.content,
            success: event.success
          }, { type: 'thinking_indicator' }];
        });
        break;
      case 'screenshot':
        setScreenshot(event.data);
        break;
      case 'done':
        setMessages(prev => [
          ...prev.filter(m => m.type !== 'thinking_indicator'),
          { type: 'done' }
        ]);
        setStatus('connected');
        setIsWorking(false);
        break;
      case 'error':
        setMessages(prev => [
          ...prev.filter(m => m.type !== 'thinking_indicator'),
          { type: 'error', content: event.content }
        ]);
        setStatus('connected');
        setIsWorking(false);
        break;
      default:
        break;
    }
  };

  const sendMessage = (text) => {
    const msgText = text || input;
    if (!msgText.trim() || isWorking || !ws.current || ws.current.readyState !== 1) return;

    setMessages(prev => [...prev, { type: 'user', content: msgText }, { type: 'thinking_indicator' }]);
    ws.current.send(JSON.stringify({ message: msgText }));
    setInput('');
    setIsWorking(true);
    setStatus('working');
  };

  const sendExample = (text) => {
    sendMessage(text);
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <div className="logo">🌐</div>
          <div>
            <h1>SurfAI</h1>
            <span className="subtitle">AI Browser Automation</span>
          </div>
        </div>
        <div className={`status-badge ${status === 'disconnected' ? 'disconnected' : status === 'working' ? 'working' : ''}`}>
          <span className="status-dot"></span>
          <span>{status === 'connected' ? 'Connected' : status === 'working' ? 'Working...' : 'Disconnected'}</span>
        </div>
      </header>

      {/* Main Layout */}
      <main className="main">
        {/* Chat Panel */}
        <div className="chat-panel">
          <div className="messages">
            {messages.length === 0 && (
              <div className="welcome">
                <div className="icon">🤖</div>
                <h2>What can I help you with?</h2>
                <p>I can navigate websites, click buttons, fill forms, and more — all by seeing the screen.</p>
                <div className="examples">
                  <div className="example-chip" onClick={() => sendExample("Navigate to google.com and search for 'LangGraph'")}>
                    Navigate to google.com and search for 'LangGraph'
                  </div>
                  <div className="example-chip" onClick={() => sendExample("Go to Wikipedia and find the page about Artificial Intelligence")}>
                    Go to Wikipedia and find the page about Artificial Intelligence
                  </div>
                  <div className="example-chip" onClick={() => sendExample("Visit github.com and check trending repositories")}>
                    Visit github.com and check trending repositories
                  </div>
                </div>
              </div>
            )}

            {messages.map((msg, idx) => {
              if (msg.type === 'user') {
                return (
                  <div key={idx} className="msg user">
                    <div className="msg-label">You</div>
                    <div className="msg-bubble">{msg.content}</div>
                  </div>
                );
              }
              if (msg.type === 'agent') {
                return (
                  <div key={idx} className="msg agent">
                    <div className="msg-label">Agent</div>
                    <div className="msg-bubble">{msg.content}</div>
                  </div>
                );
              }
              if (msg.type === 'tool_call') {
                const argsStr = Object.entries(msg.args).map(([k, v]) => `${k}: ${JSON.stringify(v)}`).join(', ');
                return (
                  <div key={idx} className="tool-group">
                    <div className="tool-chip">
                      <span className="icon">🔨</span>
                      <span className="name">{msg.name}</span>
                      <span className="args">{argsStr}</span>
                    </div>
                  </div>
                );
              }
              if (msg.type === 'tool_result') {
                return (
                  <div key={idx} className="tool-group">
                    <div className={`tool-chip ${msg.success ? 'success' : 'error'}`}>
                      <span className="icon">{msg.success ? '✅' : '❌'}</span>
                      <span className="args">{msg.content}</span>
                    </div>
                  </div>
                );
              }
              if (msg.type === 'thinking_indicator') {
                return (
                  <div key={idx} className="thinking-indicator">
                    <div className="thinking-dots"><span></span><span></span><span></span></div>
                    Agent is thinking...
                  </div>
                );
              }
              if (msg.type === 'done') {
                return <div key={idx} className="done-badge">✓ Task completed</div>;
              }
              if (msg.type === 'error') {
                return <div key={idx} className="error-badge">⚠ Error: {msg.content}</div>;
              }
              return null;
            })}
            <div ref={messagesEndRef} />
          </div>

          <div className="input-bar">
            <div className="input-wrapper">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') sendMessage(); }}
                placeholder="Tell me what to do..."
                autoComplete="off"
                disabled={isWorking}
              />
              <button
                className="send-btn"
                onClick={() => sendMessage()}
                disabled={isWorking || !input.trim()}
              >
                ➤
              </button>
            </div>
          </div>
        </div>

        {/* Browser Panel */}
        <div className="browser-panel">
          <div className="browser-header">
            <div className="browser-dots"><span></span><span></span><span></span></div>
            <span className="browser-title">Browser — Live View</span>
          </div>
          <div className="browser-viewport">
            {screenshot ? (
              <img src={`data:image/jpeg;base64,${screenshot}`} alt="Browser screenshot" />
            ) : (
              <div className="browser-placeholder">
                <div className="icon">🖥️</div>
                <p>Live browser view will appear here</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;

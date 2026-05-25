import React, { useState, useEffect, useRef } from 'react';

export default function App() {
  // Input Settings
  const [prompt, setPrompt] = useState(
    'Tạo một ứng dụng Todo List bằng Python lưu trữ persistent bằng SQLite, viết kèm đầy đủ file unit test chạy bằng pytest.'
  );
  const [apiKey, setApiKey] = useState(localStorage.getItem('VERTEX_KEY_API_KEY') || '');

  // Per-agent model configurations
  const [modelArchitect, setModelArchitect] = useState(localStorage.getItem('model_architect') || 'aws/claude-sonnet-4-6');
  const [modelCoder, setModelCoder] = useState(localStorage.getItem('model_coder') || 'aws/claude-sonnet-4-6');
  const [modelReviewer, setModelReviewer] = useState(localStorage.getItem('model_reviewer') || 'aws/claude-haiku-4-5');
  const [modelTester, setModelTester] = useState(localStorage.getItem('model_tester') || 'aws/qwen3-codex');

  // Workflow State
  const [isRunning, setIsRunning] = useState(false);
  const [wsStatus, setWsStatus] = useState('disconnected'); // connected | disconnected | running
  const [activeNode, setActiveNode] = useState('idle'); // idle | architect | coder | reviewer | tester
  const [iterations, setIterations] = useState(0);
  
  // Accumulated Data
  const [plan, setPlan] = useState('');
  const [files, setFiles] = useState({});
  const [folderFiles, setFolderFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [codeFolder, setCodeFolder] = useState(localStorage.getItem('code_folder') || '');
  const [editContent, setEditContent] = useState('');
  const [saveStatus, setSaveStatus] = useState('');
  const [errors, setErrors] = useState([]);
  const [testResults, setTestResults] = useState('');
  const [logs, setLogs] = useState([
    { type: 'system', content: 'Hệ thống đã sẵn sàng. Hãy nhập yêu cầu và nhấn nút Bắt đầu.' }
  ]);

  const wsRef = useRef(null);
  const consoleEndRef = useRef(null);

  const [logFilter, setLogFilter] = useState('all');
  const [isFolderLoading, setIsFolderLoading] = useState(false);
  const [folderError, setFolderError] = useState('');

  // Auto-scroll console terminal to bottom on new logs
  useEffect(() => {
    if (consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Save API key & model selections to localStorage
  useEffect(() => { localStorage.setItem('VERTEX_KEY_API_KEY', apiKey); }, [apiKey]);
  useEffect(() => { localStorage.setItem('model_architect', modelArchitect); }, [modelArchitect]);
  useEffect(() => { localStorage.setItem('model_coder', modelCoder); }, [modelCoder]);
  useEffect(() => { localStorage.setItem('model_reviewer', modelReviewer); }, [modelReviewer]);
  useEffect(() => { localStorage.setItem('model_tester', modelTester); }, [modelTester]);
  useEffect(() => { localStorage.setItem('code_folder', codeFolder); }, [codeFolder]);

  useEffect(() => {
    if (selectedFile && files[selectedFile]) {
      setEditContent(files[selectedFile]);
      setSaveStatus('');
    } else {
      setEditContent('');
    }
  }, [selectedFile, files]);

  useEffect(() => {
    setFolderFiles([]);
    setSelectedFile(null);
    setEditContent('');
    setFolderError('');
  }, [codeFolder]);

  const addLog = (type, content) => {
    setLogs((prev) => [...prev, { type, content }]);
  };

  const handleSaveFile = async () => {
    if (!selectedFile) {
      setSaveStatus('Chưa chọn file để lưu.');
      return;
    }

    try {
      const response = await fetch('/api/save-file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          relative_path: selectedFile,
          content: editContent,
          code_folder: codeFolder || undefined,
        }),
      });
      const data = await response.json();
      if (data.status === 'success') {
        setFiles((prev) => ({ ...prev, [selectedFile]: editContent }));
        setSaveStatus('Lưu file thành công.');
        addLog('system', `✅ File '${selectedFile}' đã được lưu vào ${codeFolder || 'sandbox root'}.`);
        await refreshFolderFiles();
      } else {
        setSaveStatus(`Lỗi lưu file: ${data.message}`);
        addLog('error', `🛑 Lỗi lưu file: ${data.message}`);
      }
    } catch (error) {
      setSaveStatus(`Lỗi lưu file: ${error.message}`);
      addLog('error', `🛑 Lỗi lưu file: ${error.message}`);
    }
  };

  const refreshFolderFiles = async () => {
    setIsFolderLoading(true);
    setFolderError('');

    try {
      const response = await fetch('/api/list-files', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code_folder: codeFolder || undefined }),
      });
      const data = await response.json();
      if (data.status === 'success') {
        setFolderFiles(data.files || []);
        if (data.files && data.files.length > 0) {
          setSelectedFile(data.files[0]);
        }
      } else {
        setFolderError(data.message || 'Không thể tải thư mục.');
        addLog('error', `🛑 ${data.message}`);
      }
    } catch (error) {
      setFolderError(error.message);
      addLog('error', `🛑 Lỗi tải thư mục: ${error.message}`);
    } finally {
      setIsFolderLoading(false);
    }
  };

  const loadFileFromFolder = async (relativePath) => {
    setSelectedFile(relativePath);
    try {
      const response = await fetch('/api/read-file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ relative_path: relativePath, code_folder: codeFolder || undefined }),
      });
      const data = await response.json();
      if (data.status === 'success') {
        setEditContent(data.content);
        setSaveStatus('');
      } else {
        setEditContent('');
        setSaveStatus(`Lỗi đọc file: ${data.message}`);
      }
    } catch (error) {
      setEditContent('');
      setSaveStatus(`Lỗi đọc file: ${error.message}`);
    }
  };

  const handleStartWorkflow = () => {
    if (isRunning) return;

    if (!apiKey) {
      alert('Vui lòng nhập Vertex Key API Key ở góc trên để chạy hệ thống!');
      return;
    }

    // 1. Reset State
    setIsRunning(true);
    setWsStatus('running');
    setActiveNode('architect'); // Architect is always the first node
    setIterations(0);
    setPlan('');
    setFiles({});
    setSelectedFile(null);
    setEditContent('');
    setSaveStatus('');
    setErrors([]);
    setTestResults('');
    setLogs([
      { type: 'system', content: '🚀 Đang bắt đầu khởi chạy hệ thống LangChain Multi-Agent...' },
      { type: 'system', content: '🔌 Đang kết nối tới server WebSockets tại ws://127.0.0.1:8000/api/ws...' }
    ]);

    // 2. Establish WebSocket connection
    const socket = new WebSocket('ws://127.0.0.1:8000/api/ws');
    wsRef.current = socket;

    socket.onopen = () => {
      setWsStatus('connected');
      addLog('system', '✅ Kết nối WebSocket thành công. Đang gửi dữ liệu yêu cầu...');
      
      // Send task parameters with per-agent model selections
      socket.send(JSON.stringify({
        prompt: prompt,
        api_key: apiKey,
        code_folder: codeFolder,
        model_architect: modelArchitect,
        model_coder: modelCoder,
        model_reviewer: modelReviewer,
        model_tester: modelTester,
        // legacy fallback group keys
        model_complex: modelArchitect,
        model_fast: modelReviewer
      }));
    };

    socket.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'status') {
          addLog('system', data.status);
        }
        
        else if (data.type === 'agent_log' || data.type === 'node_complete') {
          const completedNode = data.node;
          const message = data.message;
          const nextState = data.state;
          const logType = ['architect', 'coder', 'reviewer', 'tester'].includes(completedNode) ? completedNode : 'system';
          
          addLog(logType, `[${completedNode.toUpperCase()}] ${message}`);
          
          if (nextState.plan) setPlan(nextState.plan);
          if (nextState.files) {
            setFiles(nextState.files);
            const fileKeys = Object.keys(nextState.files);
            if (fileKeys.length > 0 && !selectedFile) {
              setSelectedFile(fileKeys[0]);
            }
          }
          if (nextState.iterations) setIterations(nextState.iterations);
          if (nextState.errors) setErrors(nextState.errors);
          if (nextState.test_results) setTestResults(nextState.test_results);
          
          if (completedNode === 'architect') {
            setActiveNode('coder');
          } else if (completedNode === 'coder') {
            setActiveNode('reviewer');
          } else if (completedNode === 'reviewer') {
            if (nextState.errors && nextState.errors.length > 0) {
              addLog('system', `⚠️ Reviewer phát hiện lỗi. Quay lại Coder để sửa.`);
              setActiveNode('coder');
            } else {
              setActiveNode('tester');
            }
          } else if (completedNode === 'tester') {
            if (message.includes('SUCCESS') || message.includes('PASSED')) {
              setActiveNode('idle');
            } else {
              addLog('system', `❌ Tester phát hiện bài kiểm tra thất bại. Quay lại Coder để debug.`);
              setActiveNode('coder');
            }
          }
        }
        
        else if (data.type === 'workflow_complete') {
          addLog('system', `🎉 THÀNH CÔNG: ${data.status}`);
          if (data.files) setFiles(data.files);
          await refreshFolderFiles();
          setIsRunning(false);
          setActiveNode('idle');
          setWsStatus('connected');
          if (socket) socket.close();
        }
        
        else if (data.type === 'error') {
          addLog('error', `🛑 Lỗi hệ thống: ${data.content}`);
          setIsRunning(false);
          setActiveNode('idle');
          setWsStatus('disconnected');
          if (socket) socket.close();
        }
      } catch (e) {
        addLog('error', `Lỗi xử lý WebSocket payload: ${e.message}`);
      }
    };

    socket.onerror = (error) => {
      addLog('error', '⚠️ Lỗi kết nối WebSocket. Hãy đảm bảo FastAPI backend đang chạy.');
      setIsRunning(false);
      setActiveNode('idle');
      setWsStatus('disconnected');
    };

    socket.onclose = () => {
      setWsStatus('disconnected');
      setIsRunning(false);
      addLog('system', '🔌 Đã ngắt kết nối WebSocket.');
    };
  };

  const handleStopWorkflow = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    setIsRunning(false);
    setActiveNode('idle');
    addLog('system', '🛑 Hủy bỏ tiến trình theo yêu cầu của người dùng.');
  };

  const filteredLogs = logs.filter((log) => {
    if (logFilter === 'all') return true;
    return log.type === logFilter;
  });

  const displayedFiles = folderFiles.length > 0 ? folderFiles : Object.keys(files);

  return (
    <div className="app-container">
      {/* Header Bar */}
      <header className="header-bar glass">
        <div className="logo-section">
          <div className="logo-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-cpu text-white"><rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M9 1v3"/><path d="M15 1v3"/><path d="M9 20v3"/><path d="M15 20v3"/><path d="M20 9h3"/><path d="M20 15h3"/><path d="M1 9h3"/><path d="M1 15h3"/></svg>
          </div>
          <div>
            <span className="logo-text">CodeMachine AI</span>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Multi-Agent Coding Framework</div>
          </div>
        </div>

        <div className="settings-section">
          <div className={`status-pill ${wsStatus !== 'disconnected' ? 'connected' : 'disconnected'}`}>
            <span className={`status-indicator ${isRunning ? 'pulsing' : ''}`} />
            <span>{wsStatus === 'running' ? 'Đang chạy' : wsStatus === 'connected' ? 'Sẵn sàng' : 'Chưa kết nối'}</span>
          </div>

          <input
            type="password"
            className="api-input"
            placeholder="Nhập Vertex API Key (vai-...)"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
        </div>
      </header>

      {/* Main Dashboard Grid */}
      <main className="dashboard-grid">
        
        {/* Left column - Control Panel */}
        <section className="sidebar glass" style={{ padding: '24px' }}>
          <h2 className="panel-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.1a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
            <span>Yêu cầu dự án</span>
          </h2>

          <div className="form-group">
            <label className="form-label">Yêu cầu phát triển phần mềm:</label>
            <textarea
              className="textarea-input"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              disabled={isRunning}
            />
          </div>

          {/* Per-Agent Model Selection */}
          <div className="form-group" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <label className="form-label" style={{ marginBottom: '2px' }}>🤖 Model cho từng Agent:</label>

            {/* Architect */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '11px', color: 'var(--accent-violet)', minWidth: '70px', fontWeight: 600 }}>Architect</span>
              <select
                id="select-model-architect"
                className="api-input"
                style={{ flex: 1, height: '34px', padding: '0 8px', background: 'rgba(0,0,0,0.3)', fontSize: '12px' }}
                value={modelArchitect}
                onChange={(e) => setModelArchitect(e.target.value)}
                disabled={isRunning}
              >
                <option value="aws/claude-sonnet-4-6">Claude Sonnet 4.6</option>
                <option value="aws/claude-haiku-4-5">Claude Haiku 4.5</option>
                <option value="aws/qwen3-codex">Qwen3 Codex</option>
                <option value="aws/minimax-m2.5">MiniMax M2.5</option>
                <option value="aws/glm-5">GLM-5</option>
              </select>
            </div>

            {/* Coder */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '11px', color: 'var(--accent-cyan)', minWidth: '70px', fontWeight: 600 }}>Coder</span>
              <select
                id="select-model-coder"
                className="api-input"
                style={{ flex: 1, height: '34px', padding: '0 8px', background: 'rgba(0,0,0,0.3)', fontSize: '12px' }}
                value={modelCoder}
                onChange={(e) => setModelCoder(e.target.value)}
                disabled={isRunning}
              >
                <option value="aws/claude-sonnet-4-6">Claude Sonnet 4.6</option>
                <option value="aws/claude-haiku-4-5">Claude Haiku 4.5</option>
                <option value="aws/qwen3-codex">Qwen3 Codex</option>
                <option value="aws/minimax-m2.5">MiniMax M2.5</option>
                <option value="aws/glm-5">GLM-5</option>
              </select>
            </div>

            {/* Reviewer */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '11px', color: 'var(--accent-amber)', minWidth: '70px', fontWeight: 600 }}>Reviewer</span>
              <select
                id="select-model-reviewer"
                className="api-input"
                style={{ flex: 1, height: '34px', padding: '0 8px', background: 'rgba(0,0,0,0.3)', fontSize: '12px' }}
                value={modelReviewer}
                onChange={(e) => setModelReviewer(e.target.value)}
                disabled={isRunning}
              >
                <option value="aws/claude-haiku-4-5">Claude Haiku 4.5</option>
                <option value="aws/claude-sonnet-4-6">Claude Sonnet 4.6</option>
                <option value="aws/qwen3-codex">Qwen3 Codex</option>
                <option value="aws/minimax-m2.5">MiniMax M2.5</option>
                <option value="aws/glm-5">GLM-5</option>
              </select>
            </div>

            {/* Tester */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '11px', color: 'var(--accent-emerald)', minWidth: '70px', fontWeight: 600 }}>Tester</span>
              <select
                id="select-model-tester"
                className="api-input"
                style={{ flex: 1, height: '34px', padding: '0 8px', background: 'rgba(0,0,0,0.3)', fontSize: '12px' }}
                value={modelTester}
                onChange={(e) => setModelTester(e.target.value)}
                disabled={isRunning}
              >
                <option value="aws/qwen3-codex">Qwen3 Codex</option>
                <option value="aws/claude-haiku-4-5">Claude Haiku 4.5</option>
                <option value="aws/claude-sonnet-4-6">Claude Sonnet 4.6</option>
                <option value="aws/minimax-m2.5">MiniMax M2.5</option>
                <option value="aws/glm-5">GLM-5</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">📁 Thư mục code gốc</label>
            <input
              className="api-input"
              type="text"
              placeholder="Ví dụ: src hoặc backend/app"
              value={codeFolder}
              onChange={(e) => setCodeFolder(e.target.value)}
              disabled={isRunning}
            />
            <small style={{ color: 'var(--text-secondary)', marginTop: '6px', display: 'block' }}>
              Để trống để tạo file ở sandbox root.
            </small>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {!isRunning ? (
              <button className="btn-run" onClick={handleStartWorkflow}>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="6 3 20 12 6 21 6 3"/></svg>
                <span>Bắt đầu Coding</span>
              </button>
            ) : (
              <button className="btn-run" style={{ background: 'linear-gradient(135deg, var(--accent-rose), #e11d48)' }} onClick={handleStopWorkflow}>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/></svg>
                <span>Dừng tiến trình</span>
              </button>
            )}
          </div>

          {/* Execution details */}
          <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '13px', color: 'var(--text-secondary)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '8px' }}>
              <span>Vòng lặp sửa đổi:</span>
              <span className="gradient-text" style={{ fontWeight: 'bold' }}>{iterations} / 10</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '8px' }}>
              <span>Số file đã tạo:</span>
              <span>{Object.keys(files).length} file</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '8px' }}>
              <span>Trạng thái review:</span>
              <span style={{ color: errors.length > 0 ? 'var(--accent-rose)' : isRunning ? 'var(--accent-amber)' : 'var(--accent-emerald)' }}>
                {errors.length > 0 ? 'Phát hiện lỗi' : isRunning ? 'Đang phân tích' : 'Đã duyệt'}
              </span>
            </div>
          </div>
        </section>

        {/* Right column - Multi-Agent State and Files */}
        <div className="main-content">
          
          {/* Agent Visual Node Graph */}
          <section className="glass graph-container">
            <div className="graph-canvas">
              
              {/* Architect Node */}
              <div className={`agent-node node-architect ${activeNode === 'architect' ? 'active' : ''}`}>
                <div className="node-icon-circle">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3h18v18H3z"/><path d="M21 9H3"/><path d="M21 15H3"/><path d="M12 3v18"/></svg>
                </div>
                <div className="node-label">Architect</div>
                <div className="node-status">{activeNode === 'architect' ? 'Đang chạy' : 'Chờ'}</div>
              </div>

              <div className="graph-arrow" />

              {/* Coder Node */}
              <div className={`agent-node node-coder ${activeNode === 'coder' ? 'active' : ''}`}>
                <div className="node-icon-circle">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/><line x1="14" x2="10" y1="4" y2="20"/></svg>
                </div>
                <div className="node-label">Coder</div>
                <div className="node-status">{activeNode === 'coder' ? 'Đang chạy' : 'Chờ'}</div>
              </div>

              <div className="graph-arrow" />

              {/* Reviewer Node */}
              <div className={`agent-node node-reviewer ${activeNode === 'reviewer' ? 'active' : ''}`}>
                <div className="node-icon-circle">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
                </div>
                <div className="node-label">Reviewer</div>
                <div className="node-status">{activeNode === 'reviewer' ? 'Đang chạy' : 'Chờ'}</div>
              </div>

              <div className="graph-arrow" />

              {/* Tester Node */}
              <div className={`agent-node node-tester ${activeNode === 'tester' ? 'active' : ''}`}>
                <div className="node-icon-circle">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m8 2 1.88 1.88"/><path d="M14.12 3.88 16 2"/><path d="M9 7.13v-1"/><path d="M15 7.13v-1"/><path d="M12 20c-4.41 0-8-3.59-8-8v-1.42c0-1.07.42-2.1 1.17-2.85l.77-.77C6.44 6.46 7.21 6 8.04 6h7.92c.83 0 1.6.46 2.1 1.13l.63.63c.8.8 1.31 1.9 1.31 3.09V12c0 4.41-3.59 8-8 8Z"/><path d="M6 12h12"/><path d="M12 12v6"/></svg>
                </div>
                <div className="node-label">Tester</div>
                <div className="node-status">{activeNode === 'tester' ? 'Đang chạy' : 'Chờ'}</div>
              </div>

            </div>
          </section>

          {/* Bottom Panels: Console & Files */}
          <div className="bottom-split">
            
            {/* Terminal Console log */}
            <div className="console-panel glass">
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid var(--border-color)', background: 'rgba(255,255,255,0.02)' }}>
                <span style={{ fontSize: '13px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span className="status-indicator" style={{ color: 'var(--accent-emerald)', width: '6px', height: '6px' }} />
                  Live System Terminal
                </span>
                <button 
                  onClick={() => setLogs([{ type: 'system', content: 'Console logs cleared.' }])}
                  style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: '11px', cursor: 'pointer' }}
                >
                  Clear logs
                </button>
              </div>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', padding: '12px 16px', borderBottom: '1px solid var(--border-color)', background: 'rgba(255,255,255,0.03)' }}>
                {['all', 'architect', 'coder', 'reviewer', 'tester', 'system', 'error'].map((type) => (
                  <button
                    key={type}
                    onClick={() => setLogFilter(type)}
                    className={`filter-pill ${logFilter === type ? 'active' : ''}`}
                    style={{ fontSize: '11px' }}
                  >
                    {type === 'all' ? 'Tất cả' : type.charAt(0).toUpperCase() + type.slice(1)}
                  </button>
                ))}
              </div>
              <div className="console-terminal">
                {filteredLogs.map((log, idx) => (
                  <div key={idx} className={`console-line ${log.type}`}>
                    {log.content}
                  </div>
                ))}
                <div ref={consoleEndRef} />
              </div>
            </div>

            {/* Code Workspace Explorer & Viewer */}
            <div className="glass" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                <div style={{ display: 'flex', padding: '12px 16px', borderBottom: '1px solid var(--border-color)', background: 'rgba(255,255,255,0.02)' }}>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 'bold' }}>Workspace Explorer</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Gốc: {codeFolder || 'sandbox'}</div>
                </div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <button
                    className="btn-run"
                    style={{ padding: '8px 14px', fontSize: '12px' }}
                    onClick={refreshFolderFiles}
                  >
                    Refresh folder
                  </button>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{isFolderLoading ? 'Đang tải...' : `${displayedFiles.length} file`}</span>
                </div>
              </div>

              {folderError ? (
                <div className="empty-state" style={{ padding: '20px' }}>
                  <span>{folderError}</span>
                </div>
              ) : displayedFiles.length === 0 ? (
                <div className="empty-state">
                  <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M4 22V4c0-.5.2-1 .6-1.4C5 2.2 5.5 2 6 2h8.5L20 7.5V22H4z"/><polyline points="14 2 14 8 20 8"/><path d="M12 18v-6"/><path d="M9 15h6"/></svg>
                  <span>Chưa có file nào trong thư mục này.</span>
                </div>
              ) : (
                <div className="files-panel">
                  {/* File Tree */}
                  <div className="file-explorer">
                    <span className="explorer-header">Danh sách File</span>
                    {displayedFiles.map((filepath) => (
                      <div
                        key={filepath}
                        className={`file-item ${selectedFile === filepath ? 'selected' : ''}`}
                        onClick={() => loadFileFromFolder(filepath)}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-file-code-2"><path d="M4 22V4c0-.5.2-1 .6-1.4C5 2.2 5.5 2 6 2h8.5L20 7.5V22H4z"/><polyline points="14 2 14 8 20 8"/><path d="m8 16 1.5-1.5L8 13"/><path d="m16 16-1.5-1.5 1.5-1.5"/><path d="m10 18 4-8"/></svg>
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {filepath.split(/[/\\\\]/).pop()}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Code View */}
                  <div className="file-content-area">
                    {selectedFile ? (
                      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                          <div>
                            <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>{selectedFile}</div>
                            <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Lưu ở: {codeFolder || 'sandbox'}</div>
                          </div>
                          <button
                            className="btn-run"
                            style={{ padding: '8px 14px', fontSize: '12px', width: 'auto' }}
                            onClick={handleSaveFile}
                          >
                            Lưu file
                          </button>
                        </div>
                        <textarea
                          className="textarea-input"
                          style={{ height: '100%', minHeight: '360px', fontFamily: 'Fira Code, monospace' }}
                          value={editContent}
                          onChange={(e) => setEditContent(e.target.value)}
                        />
                        {saveStatus && (
                          <div style={{ marginTop: '12px', color: saveStatus.startsWith('Lỗi') ? '#fca5a5' : '#a7f3d0', fontSize: '12px' }}>
                            {saveStatus}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="empty-state">Chọn một file để xem nội dung code</div>
                    )}
                  </div>
                </div>
              )}
            </div>

          </div>

        </div>

      </main>
    </div>
  );
}

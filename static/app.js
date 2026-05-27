document.addEventListener("DOMContentLoaded", () => {
    // UI Elements Selection
    const btnRun = document.getElementById("btnRun");
    const btnStop = document.getElementById("btnStop");
    const promptInput = document.getElementById("promptInput");
    const vertexKey = document.getElementById("vertexKey");
    const workspacePath = document.getElementById("workspacePath");
    
    // Agent Inputs
    const agentCeoActive = document.getElementById("agentCeoActive");
    const ceoModel = document.getElementById("ceoModel");
    const agentArchActive = document.getElementById("agentArchActive");
    const archModel = document.getElementById("archModel");
    const coderModel = document.getElementById("coderModel");
    const agentQaActive = document.getElementById("agentQaActive");
    const qaModel = document.getElementById("qaModel");
    
    // Outputs Elements
    const globalStatus = document.getElementById("globalStatus");
    const iterationCount = document.getElementById("iterationCount");
    const clock = document.getElementById("clock");
    const consoleBody = document.getElementById("consoleBody");
    const btnClearConsole = document.getElementById("btnClearConsole");
    
    const prdPlaceholder = document.getElementById("prdPlaceholder");
    const prdOutput = document.getElementById("prdOutput");
    const archPlaceholder = document.getElementById("archPlaceholder");
    const archOutput = document.getElementById("archOutput");
    const qaPlaceholder = document.getElementById("qaPlaceholder");
    const qaOutputWrapper = document.getElementById("qaOutputWrapper");
    const qaStatusCard = document.getElementById("qaStatusCard");
    const qaStatusIcon = document.getElementById("qaStatusIcon");
    const qaStatusText = document.getElementById("qaStatusText");
    const qaOutput = document.getElementById("qaOutput");
    
    const workspaceFileList = document.getElementById("workspaceFileList");
    const fileViewerHeader = document.getElementById("fileViewerHeader");
    const fileViewerContent = document.getElementById("fileViewerContent").firstElementChild;

    let activeStreamReader = null;
    let savedFilesContent = {}; // Lưu trữ nội dung file để render nhanh

    // 1. Clock Initialization
    function updateClock() {
        const now = new Date();
        clock.textContent = now.toTimeString().split(' ')[0];
    }
    setInterval(updateClock, 1000);
    updateClock();

    // 2. Load settings from sessionStorage
    if (sessionStorage.getItem("vertexKey")) {
        vertexKey.value = sessionStorage.getItem("vertexKey");
    }
    vertexKey.addEventListener("input", () => {
        sessionStorage.setItem("vertexKey", vertexKey.value);
    });

    // Toggle sub-agent config disabled attribute
    agentCeoActive.addEventListener("change", () => {
        ceoModel.disabled = !agentCeoActive.checked;
        document.getElementById("ceoConfigBody").style.opacity = agentCeoActive.checked ? "1" : "0.5";
    });
    agentArchActive.addEventListener("change", () => {
        archModel.disabled = !agentArchActive.checked;
        document.getElementById("archConfigBody").style.opacity = agentArchActive.checked ? "1" : "0.5";
    });
    agentQaActive.addEventListener("change", () => {
        qaModel.disabled = !agentQaActive.checked;
        document.getElementById("qaConfigBody").style.opacity = agentQaActive.checked ? "1" : "0.5";
    });

    // 3. Tab Navigation Logic
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tabButtons.forEach(b => b.classList.remove("active"));
            tabPanes.forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            document.getElementById(btn.dataset.tab).classList.add("active");
        });
    });

    // 4. Notification Helper
    function showNotification(message, type = "success") {
        const area = document.getElementById("notificationArea");
        const notif = document.createElement("div");
        notif.className = `notification ${type}`;
        
        let icon = "fa-circle-check";
        if (type === "error") icon = "fa-circle-xmark";
        if (type === "warning") icon = "fa-circle-exclamation";
        
        notif.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
        area.appendChild(notif);
        
        setTimeout(() => {
            notif.style.opacity = "0";
            notif.style.transform = "translateX(100%)";
            notif.style.transition = "opacity 0.3s, transform 0.3s";
            setTimeout(() => notif.remove(), 300);
        }, 4000);
    }

    // 5. Console Helpers
    function appendConsoleLog(message, type = "system-msg") {
        const line = document.createElement("div");
        line.className = `console-line ${type}`;
        line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        consoleBody.appendChild(line);
        consoleBody.scrollTop = consoleBody.scrollHeight;
    }

    btnClearConsole.addEventListener("click", () => {
        consoleBody.innerHTML = '<div class="console-line system-msg">> Console cleared.</div>';
    });

    // 6. Reset Graph visualizer states
    function resetVisualizer() {
        document.querySelectorAll(".graph-node").forEach(n => {
            n.classList.remove("active", "completed", "bypassed");
        });
        document.querySelectorAll(".graph-edge").forEach(e => {
            e.classList.remove("active", "completed");
        });
        
        iterationCount.textContent = "0/5";
        
        // Hide loop edges
        const edgeQaCoder = document.getElementById("edge-qa-coder");
        if (edgeQaCoder) edgeQaCoder.style.display = "none";
        
        // Clear old file contents
        savedFilesContent = {};
        workspaceFileList.innerHTML = '<li class="empty-list-msg">Chưa có file nào được tạo.</li>';
        fileViewerHeader.textContent = "Chọn một file để xem nội dung...";
        fileViewerContent.textContent = "";
    }

    // 7. Graph State management
    function updateGraphState(nodeName, state = "active") {
        const node = document.getElementById(`node-${nodeName}`);
        if (!node) return;

        if (state === "active") {
            // Remove active from others
            document.querySelectorAll(".graph-node").forEach(n => n.classList.remove("active"));
            node.classList.add("active");
            
            // Activate incoming edge
            if (nodeName === "ceo") activateEdge("start", "ceo");
            if (nodeName === "architect") activateEdge("ceo", "arch");
            if (nodeName === "coder") activateEdge("arch", "coder");
            if (nodeName === "qa") activateEdge("coder", "qa");
        } else if (state === "completed") {
            node.classList.remove("active");
            node.classList.add("completed");
            
            // Mark outgoing edge completed
            if (nodeName === "ceo") completeEdge("start", "ceo");
            if (nodeName === "architect") completeEdge("ceo", "arch");
            if (nodeName === "coder") completeEdge("arch", "coder");
            if (nodeName === "qa") completeEdge("coder", "qa");
        } else if (state === "bypassed") {
            node.classList.remove("active");
            node.classList.add("bypassed");
        }
    }

    function activateEdge(from, to) {
        const edge = document.getElementById(`edge-${from}-${to}`);
        if (edge) edge.classList.add("active");
    }

    function completeEdge(from, to) {
        const edge = document.getElementById(`edge-${from}-${to}`);
        if (edge) {
            edge.classList.remove("active");
            edge.classList.add("completed");
        }
    }

    // 8. Handle dynamic files payload
    function fetchAndRenderWorkspaceFiles(filesList) {
        if (!filesList || filesList.length === 0) return;
        
        workspaceFileList.innerHTML = "";
        filesList.forEach(file => {
            const li = document.createElement("li");
            li.innerHTML = `<i class="fa-regular fa-file-code"></i> <span>${file}</span>`;
            li.addEventListener("click", () => {
                document.querySelectorAll(".file-list li").forEach(el => el.classList.remove("active"));
                li.classList.add("active");
                fetchFileContent(file);
            });
            workspaceFileList.appendChild(li);
        });
    }

    async function fetchFileContent(filePath) {
        fileViewerHeader.textContent = `File: ${filePath} (Đang tải...)`;
        fileViewerContent.textContent = "Loading file content...";
        
        const customWorkspace = workspacePath.value.trim() || null;
        
        try {
            // Tận dụng tool API read_workspace_file hoặc lấy trực tiếp
            // Backend cho phép đọc file bằng cách mô phỏng công cụ read thông qua endpoint phụ hoặc trực tiếp
            // Ở đây để đơn giản, ta gọi endpoint lấy nội dung file
            const payload = {
                relative_path: filePath,
                config: {
                    configurable: {
                        workspace_path: customWorkspace
                    }
                }
            };
            
            // Gửi yêu cầu qua tool read
            // Để frontend có thể lấy trực tiếp nội dung file, backend FastAPI có thể cung cấp thêm endpoint đọc file.
            // Hãy gọi API fetch /api/read-file hoặc fallback lấy từ cache nếu chưa viết API.
            // Chúng ta sẽ viết API đọc file ở backend (hoặc lấy từ cache state trả về nếu state lưu nội dung file).
            // Vì LangGraph state.code_files lưu nội dung {path: content}, ta có thể cache nó trực tiếp khi nhận event!
            if (savedFilesContent[filePath]) {
                fileViewerHeader.textContent = `File: ${filePath}`;
                fileViewerContent.textContent = savedFilesContent[filePath];
            } else {
                fileViewerContent.textContent = "Nội dung file không có sẵn trong bộ nhớ đệm.";
            }
        } catch (e) {
            fileViewerHeader.textContent = `Lỗi đọc file: ${filePath}`;
            fileViewerContent.textContent = e.toString();
        }
    }

    // 9. SSE Message Processor
    function handleSSEMessage(data) {
        if (data.event === "start") {
            appendConsoleLog(data.message, "system-msg");
            updateGraphState("start", "completed");
            document.getElementById("node-start").classList.add("completed");
            
            // Kích hoạt Node active đầu tiên tùy theo cấu hình
            if (agentCeoActive.checked) {
                updateGraphState("ceo", "active");
            } else if (agentArchActive.checked) {
                updateGraphState("ceo", "bypassed");
                updateGraphState("architect", "active");
            } else {
                updateGraphState("ceo", "bypassed");
                updateGraphState("architect", "bypassed");
                updateGraphState("coder", "active");
            }
        }
        
        else if (data.event === "node_complete") {
            const node = data.node;
            appendConsoleLog(`Tác tử [${node.toUpperCase()}] hoàn thành bước xử lý.`, "node-start-msg");
            
            updateGraphState(node, "completed");

            // Xử lý dữ liệu từng node đặc thù
            if (node === "ceo") {
                if (data.prd) {
                    prdPlaceholder.style.display = "none";
                    prdOutput.style.display = "block";
                    prdOutput.textContent = data.prd;
                }
                
                // Active node tiếp theo
                if (agentArchActive.checked) {
                    updateGraphState("architect", "active");
                } else {
                    updateGraphState("architect", "bypassed");
                    updateGraphState("coder", "active");
                }
            }
            
            else if (node === "architect") {
                if (data.architecture) {
                    archPlaceholder.style.display = "none";
                    archOutput.style.display = "block";
                    archOutput.textContent = data.architecture;
                }
                updateGraphState("coder", "active");
            }
            
            else if (node === "coder") {
                iterationCount.textContent = `${data.iterations}/5`;
                if (data.files && data.files.length > 0) {
                    fetchAndRenderWorkspaceFiles(data.files);
                }
                
                if (agentQaActive.checked) {
                    updateGraphState("qa", "active");
                } else {
                    updateGraphState("qa", "bypassed");
                    // Đi thẳng đến END
                    completeEdge("coder", "qa");
                    updateGraphState("end", "active");
                }
            }
            
            else if (node === "qa") {
                qaPlaceholder.style.display = "none";
                qaOutputWrapper.style.display = "block";
                
                qaOutput.textContent = data.test_results;
                
                if (data.is_verified) {
                    qaStatusCard.className = "qa-status-card passed";
                    qaStatusIcon.className = "fa-solid fa-circle-check";
                    qaStatusText.textContent = "SUCCESS: Tất cả bài test case đã VƯỢT QUA thành công!";
                    appendConsoleLog("Xác minh hoàn thành: Code đã đạt chất lượng.", "success-msg");
                    
                    updateGraphState("end", "active");
                    completeEdge("qa", "end");
                } else {
                    qaStatusCard.className = "qa-status-card failed";
                    qaStatusIcon.className = "fa-solid fa-circle-xmark";
                    qaStatusText.textContent = `FAILED: Test case thất bại (Vòng lặp sửa lỗi #${data.iterations})`;
                    appendConsoleLog(`Xác minh thất bại. Quay lại sửa lỗi code...`, "error-msg");

                    // Show loop arrow
                    const edgeQaCoder = document.getElementById("edge-qa-coder");
                    if (edgeQaCoder) edgeQaCoder.style.display = "block";
                    
                    if (data.iterations < 5) {
                        updateGraphState("coder", "active");
                    } else {
                        appendConsoleLog("Hệ thống đạt giới hạn số lần sửa lỗi tối đa (5 vòng).", "error-msg");
                        updateGraphState("end", "active");
                        completeEdge("qa", "end");
                    }
                }
            }
        }
        
        else if (data.event === "end") {
            appendConsoleLog(data.message, "success-msg");
            updateGraphState("end", "completed");
            setSystemRunningState(false);
            globalStatus.textContent = "Đã hoàn thành";
            globalStatus.className = "status-value finished";
            showNotification(data.message, "success");
        }
        
        else if (data.event === "error") {
            appendConsoleLog(`LỖI: ${data.message}`, "error-msg");
            setSystemRunningState(false);
            globalStatus.textContent = "Lỗi hệ thống";
            globalStatus.className = "status-value error";
            showNotification(data.message, "error");
        }
    }

    // 10. Start system running visual states
    function setSystemRunningState(isRunning) {
        btnRun.disabled = isRunning;
        btnStop.disabled = !isRunning;
        promptInput.disabled = isRunning;
        workspacePath.disabled = isRunning;
        vertexKey.disabled = isRunning;
        
        document.querySelectorAll("select, input[type=checkbox]").forEach(el => {
            // Coder active is always disabled
            if (el.id !== "agentCoderActive") el.disabled = isRunning;
        });

        if (isRunning) {
            btnRun.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang chạy...';
            globalStatus.textContent = "Đang thực thi";
            globalStatus.className = "status-value running";
        } else {
            btnRun.innerHTML = '<i class="fa-solid fa-play"></i> Kích hoạt Workflow';
        }
    }

    // 11. Run Workflow execution trigger
    async function handleRun() {
        const prompt = promptInput.value.trim();
        if (!prompt) {
            showNotification("Vui lòng nhập mô tả yêu cầu phần mềm trước khi chạy!", "warning");
            return;
        }

        resetVisualizer();
        setSystemRunningState(true);
        appendConsoleLog("Đang kết nối API Backend & Khởi tạo luồng...", "system-msg");

        const activeAgents = ["coder"]; // Coder luôn được kích hoạt
        if (agentCeoActive.checked) activeAgents.push("ceo");
        if (agentArchActive.checked) activeAgents.push("architect");
        if (agentQaActive.checked) activeAgents.push("qa");

        const agentsConfig = {
            ceo: { model: ceoModel.value },
            architect: { model: archModel.value },
            coder: { model: coderModel.value },
            qa: { model: qaModel.value }
        };

        const payload = {
            prompt: prompt,
            vertex_key: vertexKey.value.trim() || null,
            workspace_path: workspacePath.value.trim() || null,
            active_agents: activeAgents,
            agents_config: agentsConfig
        };

        try {
            const response = await fetch("/api/run", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errText = await response.text();
                throw new Error(errText || "Không thể kết nối đến Backend Server.");
            }

            const reader = response.body.getReader();
            activeStreamReader = reader;
            const decoder = new TextDecoder("utf-8");
            let buffer = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop(); // Save the last chunk back to buffer

                for (const line of lines) {
                    if (line.trim().startsWith("data: ")) {
                        const dataStr = line.replace("data: ", "").trim();
                        if (dataStr) {
                            try {
                                const data = JSON.parse(dataStr);
                                
                                // Cache code files content directly from completed nodes payload to enable immediate viewing
                                if (data.event === "node_complete") {
                                    // Cache PRD và Architecture
                                    if (data.prd) savedFilesContent["Tài liệu PRD"] = data.prd;
                                    if (data.architecture) savedFilesContent["Kiến trúc hệ thống"] = data.architecture;
                                    
                                    // Mock cache file contents
                                    // Trong thực tế, vì node completed không trả về toàn bộ nội dung file code để giảm băng thông SSE,
                                    // Chúng ta có thể lưu trữ nội dung file tạm thời. Để phục vụ việc xem trực tiếp trên giao diện:
                                    // Ở đây vì state.code_files chứa {path: content}, backend của chúng ta trong file server.py trả về:
                                    // "files": list(node_state.get("code_files", {}).keys())
                                    // Để hiển thị nội dung file tức thời, chúng ta sẽ tối ưu backend server.py hoặc lưu content.
                                    // Hãy sửa backend để trả về cả nội dung của code_files qua SSE hoặc cache nó.
                                    // Để giao diện mượt, chúng ta sẽ bổ sung endpoint API phụ để đọc file hoặc sửa payload.
                                    // Giải pháp tối ưu: Ở backend server.py, ta lưu lại state.code_files của lần chạy gần nhất
                                    // và cung cấp một endpoint GET `/api/file?path=...` để đọc trực tiếp từ ổ đĩa!
                                }
                                
                                handleSSEMessage(data);
                            } catch (e) {
                                console.error("Error parsing JSON chunk:", e);
                            }
                        }
                    }
                }
            }

        } catch (e) {
            appendConsoleLog(`LỖI KẾT NỐI: ${e.message}`, "error-msg");
            setSystemRunningState(false);
            globalStatus.textContent = "Lỗi kết nối";
            globalStatus.className = "status-value error";
            showNotification(e.message, "error");
        }
    }

    // 12. Stop execution
    function handleStop() {
        if (activeStreamReader) {
            activeStreamReader.cancel();
            activeStreamReader = null;
            appendConsoleLog("Người dùng đã chủ động dừng luồng thực thi.", "error-msg");
            setSystemRunningState(false);
            globalStatus.textContent = "Đã dừng";
            globalStatus.className = "status-value idle";
            showNotification("Đã dừng thực thi hệ thống tác tử.", "warning");
        }
    }

    btnRun.addEventListener("click", handleRun);
    btnStop.addEventListener("click", handleStop);
});

# Code Machine 🚀

Một ứng dụng web AI được xây dựng với FastAPI backend và React frontend để tự động hóa quy trình phát triển phần mềm bằng cách sử dụng multi-agent orchestration.

## Tổng Quan Dự Án

Code Machine là một hệ thống đa tác nhân (multi-agent) được thiết kế để hỗ trợ toàn bộ chu kỳ phát triển phần mềm:

- **Architect Agent**: Thiết kế kiến trúc phần mềm
- **Coder Agent**: Viết code dựa trên thiết kế
- **Reviewer Agent**: Đánh giá và review code
- **Tester Agent**: Viết test và đảm bảo chất lượng
- **File System Tools**: Quản lý file và thư mục
- **Terminal Tools**: Thực thi lệnh trong terminal

### Công Nghệ Sử Dụng

**Backend:**
- FastAPI - Web framework hiện đại
- LangChain & LangGraph - Orchestration cho multi-agent
- OpenAI/Vertex Key - LLM models
- WebSocket - Real-time communication
- Pydantic - Data validation

**Frontend:**
- React 19 - UI library
- Vite - Build tool
- ESLint - Code linting

## Cài Đặt

### Yêu Cầu Hệ Thống
- Python 3.8+
- Node.js 16+
- npm hoặc yarn

### Backend Setup

1. **Tạo Virtual Environment**
```bash
cd backend
python -m venv venv

# Trên Windows
venv\Scripts\activate

# Trên macOS/Linux
source venv/bin/activate
```

2. **Cài Đặt Dependencies**
```bash
pip install -r requirements.txt
```

3. **Cấu Hình Environment Variables**

Tạo file `.env` trong thư mục `backend/`:
```
OPENAI_API_KEY=your_openai_api_key_here
# hoặc cho Vertex AI
GOOGLE_APPLICATION_CREDENTIALS=path_to_credentials.json
```

### Frontend Setup

1. **Cài Đặt Dependencies**
```bash
cd frontend
npm install
```

2. **Cấu Hình Backend URL** (tùy chọn)

Chỉnh sửa file `src/main.jsx` nếu backend chạy trên URL khác localhost:8000

## Chạy Ứng Dụng

### Backend

```bash
cd backend
python run.py
```

Backend sẽ khởi động tại: `http://localhost:8000`

**API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend

```bash
cd frontend
npm run dev
```

Frontend sẽ khởi động tại: `http://localhost:5173`

## Cấu Trúc Dự Án

```
code-machine/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py           # Cấu hình chung
│   │   ├── main.py             # API endpoints
│   │   ├── state.py            # Định nghĩa state cho agents
│   │   ├── graph.py            # LangGraph configuration
│   │   ├── agents/             # Multi-agent definitions
│   │   │   ├── base.py         # Base agent class
│   │   │   ├── architect.py    # Architect agent
│   │   │   ├── coder.py        # Coder agent
│   │   │   ├── reviewer.py     # Reviewer agent
│   │   │   └── tester.py       # Tester agent
│   │   └── tools/              # Tool definitions
│   │       ├── file_system.py  # File operations
│   │       └── terminal.py     # Terminal commands
│   ├── run.py                  # Entry point
│   ├── requirements.txt        # Python dependencies
│   ├── test_graph.py          # Graph tests
│   └── test_websocket.py      # WebSocket tests
│
└── frontend/
    ├── src/
    │   ├── App.jsx            # Main component
    │   ├── App.css            # Styles
    │   ├── main.jsx           # Entry point
    │   ├── index.css          # Global styles
    │   └── assets/            # Images, fonts, etc.
    ├── public/                # Static files
    ├── package.json
    ├── vite.config.js
    ├── eslint.config.js
    └── index.html
```

## Sử Dụng API

### Health Check
```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "ok",
  "message": "CodeMachine backend gateway is running"
}
```

### Test Connection
```bash
curl -X POST http://localhost:8000/api/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your_api_key",
    "model": "gpt-4"
  }'
```

### WebSocket Connection
Để kết nối WebSocket cho real-time streaming:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

ws.send(JSON.stringify({
  type: 'user_message',
  content: 'Your request here'
}));
```

## Phát Triển

### Chạy Tests

**Backend:**
```bash
cd backend
python test_graph.py
python test_websocket.py
```

**Frontend:**
```bash
cd frontend
npm run lint
npm run build
```

### Build Production

**Backend:**
Sẵn sàng để deploy bằng:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Frontend:**
```bash
cd frontend
npm run build
```

Output sẽ trong thư mục `dist/`

## Cấu Hình

### Backend Configuration

File `backend/app/config.py` chứa các cấu hình chính:
- Model selections
- API endpoints
- Agent parameters
- Tool configurations

### Environment Variables

```bash
# OpenAI
OPENAI_API_KEY=sk_...

# Vertex AI (Google Cloud)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Frontend (nếu khác localhost)
REACT_APP_API_URL=http://localhost:8000
```

## Troubleshooting

### Backend không khởi động
```bash
# Kiểm tra Python version
python --version

# Kiểm tra dependencies
pip list

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend không kết nối được Backend
- Kiểm tra backend đã khởi động: `http://localhost:8000/api/health`
- Kiểm tra CORS configuration trong `backend/app/main.py`
- Kiểm tra firewall settings

### WebSocket Connection Failed
- Kiểm tra browser console cho errors
- Đảm bảo backend đang chạy trên `ws://localhost:8000`
- Kiểm tra browser hỗ trợ WebSocket

## API Key Configuration

### Sử dụng OpenAI
1. Tạo account tại [OpenAI](https://openai.com)
2. Lấy API key từ dashboard
3. Set environment variable hoặc config file

### Sử dụng Google Vertex AI
1. Tạo Google Cloud project
2. Enable Vertex AI API
3. Tạo service account và download JSON key
4. Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable

## Các Tính Năng Chính

✅ **Multi-Agent System** - Hợp tác giữa nhiều AI agents  
✅ **Real-time Communication** - WebSocket support cho live updates  
✅ **File Management** - Tạo, chỉnh sửa, xóa files  
✅ **Terminal Execution** - Chạy lệnh shell  
✅ **Code Review** - AI-powered code review  
✅ **Automated Testing** - Viết test tự động  

## License

MIT License - xem file LICENSE để chi tiết

## Support & Contribution

Nếu bạn gặp issue hoặc có đề xuất, vui lòng:
1. Tạo GitHub issue
2. Fork repository và submit pull request
3. Liên hệ qua email

## Tài Liệu Bổ Sung

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [LangChain Documentation](https://python.langchain.com)
- [React Documentation](https://react.dev)
- [Vite Documentation](https://vitejs.dev)

---

**Version:** 0.0.0  
**Last Updated:** 2026-05-25

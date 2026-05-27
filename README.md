# LangGraph SDLC Agentic System & Dashboard

Dự án này triển khai một hệ thống phát triển phần mềm tự động (SDLC) dựa trên kiến trúc Đa Tác tử (Multi-Agent System) sử dụng **LangGraph** và **LangChain**. Hệ thống bao gồm nhiều tác tử có vai trò chuyên biệt (CEO, Architect, Coder, QA, Supervisor, Research, Chart, Math) làm việc cùng nhau để lập kế hoạch, thiết kế kiến trúc, viết mã nguồn và kiểm thử. Dự án cũng đi kèm một giao diện Web Dashboard (FastAPI + HTML/CSS/JS tĩnh) trực quan hóa quy trình hoạt động của các tác tử.

---

## 📋 Mục lục
1. [Yêu cầu hệ thống](#-yêu cầu-hệ-thống)
2. [Cấu trúc dự án](#-cấu-trúc-dự-án)
3. [Cài đặt & Cấu hình](#-cài-đặt--cấu-hình)
4. [Khởi chạy Cơ sở dữ liệu](#-khởi-chạy-cơ-sở-dữ-liệu)
5. [Hướng dẫn sử dụng](#-hướng-dẫn-sử-dụng)
   - [Chạy Web Dashboard](#1-chạy-web-dashboard)
   - [Chạy CLI Developer Organization (E2E)](#2-chạy-cli-developer-organization-e2e)
   - [Chạy CLI Supervisor (Research, Chart & Math)](#3-chạy-cli-supervisor-research-chart--math)
   - [Chạy CLI Tác tử phát triển Landing Page FindingHome](#4-chạy-cli-tác-tử-phát-triển-landing-page-findinghome)

---

## 💻 Yêu cầu hệ thống
- **Python**: Phiên bản `3.10` trở lên.
- **Docker & Docker Compose**: Để khởi chạy PostgreSQL chứa dữ liệu persistence (checkpoint) cho các hội thoại của tác tử.
- **API Keys**: Tài khoản Vertex-Key (hoặc OpenAI) và Tavily Search API.

---

## 📂 Cấu trúc dự án

```text
code-machine/
├── docker-compose.yml       # Cấu hình container PostgreSQL cho bộ nhớ tác tử
├── requirements.txt         # Các thư viện Python cần thiết
├── server.py                # Server FastAPI & Web Dashboard API
├── main.py                  # CLI chạy Multi-Agent Supervisor (Research/Chart/Math)
├── main_org.py              # CLI chạy Quy trình Phát triển Phần mềm Tự động E2E
├── main_findinghome.py      # CLI chạy Tác tử phát triển Next.js Frontend cho FindingHome
├── .env                     # File cấu hình biến môi trường và API Keys
├── static/                  # Giao diện Web Dashboard (HTML, CSS, JS tĩnh)
│   ├── index.html
│   ├── style.css
│   └── app.js
├── src/                     # Mã nguồn lõi của hệ thống Tác tử
│   ├── config.py            # Cấu hình LLM kết nối Vertex-Key & PostgreSQL DB
│   ├── state.py             # Schema trạng thái chung của Tác tử (AgentOrgState)
│   ├── agents.py            # Logic của các Node tác tử (CEO, Architect, Coder, QA)
│   ├── tools.py             # Định nghĩa công cụ (chạy terminal, sửa file, kiểm thử...)
│   └── graph.py             # Xây dựng sơ đồ quy trình LangGraph (StateGraph)
└── workspace/               # Thư mục đầu ra mặc định chứa mã nguồn do tác tử tạo ra
```

---

## 🛠️ Cài đặt & Cấu hình

### 1. Cài đặt thư viện Python
Mở terminal tại thư mục gốc của dự án và cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường
Tạo hoặc chỉnh sửa tệp `.env` tại thư mục gốc với các nội dung sau:
```env
# Cấu hình kết nối LLM qua Vertex-Key (hoặc sử dụng trực tiếp OpenAI)
VERTEX_KEY_API_KEY=your_vertex_key_here
VERTEX_KEY_API_BASE=https://vertex-key.com/api/v1
VERTEX_KEY_MODEL_NAME=aws/claude-haiku-4-5  # Hoặc gpt-4o, claude-3-5-sonnet...

# API Key cho công cụ tìm kiếm Tavily Search
TAVILY_API_KEY=your_tavily_key_here

# Cấu hình cơ sở dữ liệu lưu Checkpoints PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_secure_password
POSTGRES_DB=agent_memory
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

---

## 🗄️ Khởi chạy Cơ sở dữ liệu

Hệ thống sử dụng PostgreSQL để lưu trữ tiến trình/bộ nhớ hội thoại (checkpointer) của LangGraph nhằm hỗ trợ tiếp tục phiên làm việc khi gặp lỗi. 

Khởi động database bằng Docker Compose:
```bash
docker-compose up -d
```
*Lưu ý: Lệnh này sẽ tạo container PostgreSQL chạy ngầm tại cổng `5432`.*

---

## 🚀 Hướng dẫn sử dụng

### 1. Chạy Web Dashboard
Giao diện Web cho phép bạn nhập prompt yêu cầu, bật/tắt các tác tử, cấu hình model và theo dõi trực quan trạng thái hoàn thành của từng bước (CEO -> Architect -> Coder -> QA).

Chạy lệnh:
```bash
python server.py
```
Sau khi khởi chạy thành công, truy cập giao diện tại:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

*(Nếu kết nối cơ sở dữ liệu PostgreSQL thất bại, server sẽ tự động chuyển sang chế độ `MemorySaver` lưu trữ tạm thời trong RAM)*

---

### 2. Chạy CLI Developer Organization (E2E)
Kịch bản này giả lập một tổ chức phát triển phần mềm khép kín bao gồm:
- **CEO**: Phân tích yêu cầu và viết tài liệu PRD.
- **Architect**: Thiết kế kiến trúc thư mục/tập tin.
- **Coder**: Viết mã nguồn tương ứng trong thư mục `workspace`.
- **QA**: Viết test và chạy thử nghiệm bằng terminal. Nếu lỗi xảy ra, QA sẽ báo cáo lại để Coder sửa mã nguồn (hỗ trợ tối đa 5 vòng lặp).

Chạy thử nghiệm với yêu cầu mặc định:
```bash
python main_org.py
```

---

### 3. Chạy CLI Supervisor (Research, Chart & Math)
Kịch bản chạy hệ thống phân cấp gồm một tác tử Supervisor điều phối công việc cho 3 tác tử chuyên môn:
- **Research Agent**: Sử dụng công cụ Tavily Search để tìm thông tin trực tuyến.
- **Chart Agent**: Sử dụng Python REPL để viết code biểu diễn biểu đồ/đồ thị.
- **Math Agent**: Sử dụng các hàm tính toán cơ bản cộng, nhân, chia.

Chạy thử nghiệm câu hỏi phân tích GDP Mỹ và bang New York:
```bash
python main.py
```

---

### 4. Chạy CLI Tác tử phát triển Landing Page FindingHome
Kịch bản phát triển mã nguồn frontend sử dụng Next.js 14, TypeScript, Tailwind CSS, shadcn/ui cho dự án bất động sản Đà Nẵng "FindingHome".

Chạy lệnh:
```bash
python main_findinghome.py
```
*Lưu ý: Bạn có thể thay đổi đường dẫn lưu trữ mã nguồn tại dòng 15 trong file `main_findinghome.py` (Mặc định: `D:/project/FindingHome`).*

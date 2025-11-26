# 💪 PT & Dinh Dưỡng Lý Đức 2.0 - AI Fitness Assistant

![Project Banner](https://img.shields.io/badge/Fitness-AI_Assistant-green?style=for-the-badge&logo=google-gemini)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-009688?style=for-the-badge&logo=fastapi)
![Gemini](https://img.shields.io/badge/Google_Gemini-API-8E75B2?style=for-the-badge&logo=google)

> **Trợ lý ảo AI chuyên biệt về thể hình và dinh dưỡng**, được thiết kế để giúp bạn đạt được mục tiêu vóc dáng mơ ước với phong cách tư vấn đậm chất "Lý Đức" - thân thiện, chuyên nghiệp và đầy động lực.

---

## ✨ Chức năng nổi bật (Features)

### 🤖 1. Tư vấn tập luyện thông minh (Smart Workout Planning)
- **Cá nhân hóa tối đa**: Xây dựng lịch tập dựa trên mục tiêu (tăng cơ/giảm mỡ), kinh nghiệm, dụng cụ sẵn có và quỹ thời gian của bạn.
- **Hội thoại theo ngữ cảnh (Stateful Context)**: Bot ghi nhớ và tư vấn chi tiết dựa trên thông tin bạn đã cung cấp.
- **Giảm hallucination, tránh AI đoán mò**: Hệ thống thông minh tự động trích xuất dữ liệu từ câu trả lời phức tạp của người dùng, nếu có thông tin nào chưa được làm rõ thì sẽ tự động hỏi người dùng để xác nhận.

### 🥗 2. Phân tích dinh dưỡng qua ảnh (AI Meal Analysis)
- **Nhận diện món ăn**: Chỉ cần tải lên ảnh bữa ăn, AI sẽ nhận diện các món ăn.
- **Tính toán Calories & Macro**: Ước lượng lượng calo, protein, carb, fat chi tiết.
- **Lời khuyên dinh dưỡng**: Đưa ra nhận xét và gợi ý điều chỉnh khẩu phần ăn cho phù hợp với mục tiêu.

### 🎨 3. Giao diện hiện đại (Modern UI/UX)
- **Dark Mode Premium**: Thiết kế tối màu sang trọng với tông xanh neon (Health & Fitness).
- **Hiệu ứng mượt mà**: Typing indicator, message animations, và các hiệu ứng chuyển động tinh tế.

---

## 🛠️ Công nghệ sử dụng (Tech Stack)

### Backend (Server)
- **Ngôn ngữ**: [Python](https://www.python.org/)
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (High performance, easy to learn)
- **AI Model**: [Google Gemini API](https://ai.google.dev/) (Gemini 2.5 Flash)
- **Server**: [Uvicorn](https://uvicorn.dev/)

### Frontend (Client)
- **Core**: HTML5, CSS3 (Vanilla), JavaScript (ES6+)
- **Styling**: Custom CSS Variables, Flexbox/Grid Layout, Glassmorphism effects
- **Icons**: Emoji & CSS Shapes

---

## 🚀 Hướng dẫn cài đặt & Chạy (Installation)

### Yêu cầu tiên quyết
- Python 3.8 trở lên
- Tài khoản Google Cloud (để lấy Gemini API Key)

### Bước 1: Clone và Cấu hình
1. Clone dự án về máy.
2. Tạo file `.env` trong thư mục `backend/` dựa trên file `.env.example`:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

### Bước 2: Chạy Backend Server
Mở terminal tại thư mục gốc của dự án và chạy:

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```
Server sẽ khởi chạy tại: `http://127.0.0.1:8000`

### Bước 3: Chạy Frontend
Sử dụng **Live Server** (VS Code Extension) hoặc mở trực tiếp file `index.html`:

1. Mở `frontend/index.html` trong VS Code.
2. Nhấn **Go Live** (góc dưới phải).
3. Truy cập: `http://127.0.0.1:5500`

---

## 🤝 Đóng góp (Contributing)
Mọi đóng góp đều được hoan nghênh! Hãy tạo Pull Request hoặc mở Issue nếu bạn tìm thấy lỗi.

## � License
Dự án này được phát hành dưới giấy phép MIT.

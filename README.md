# BizFlow - Nền Tảng Chuyển Đổi Số Cho Hộ Kinh Doanh

**BizFlow** là nền tảng Backend API hỗ trợ chuyển đổi số cho các hộ kinh doanh vừa và nhỏ, cung cấp giải pháp quản lý bán hàng, kho, công nợ, và báo cáo tài chính tuân thủ Thông tư 88/2021/TT-BTC.

## Tính Năng Chính (MVP)

### 1. Quản Lý Bán Hàng & Đơn Hàng
- Tạo đơn hàng tại quầy (POS) nhanh chóng.
- Hỗ trợ bán chịu (ghi nợ) và theo dõi công nợ khách hàng.
- Tự động trừ kho khi xác nhận đơn hàng.
- **AI Draft Order**: Hỗ trợ tạo đơn nháp từ ngôn ngữ tự nhiên (Vd: "Lấy 5 bao xi măng cho chú Ba, ghi nợ").

### 2. Quản Lý Kho & Sản Phẩm
- Theo dõi tồn kho theo thời gian thực.
- Hỗ trợ nhập kho, xuất kho, kiểm kê.
- Quản lý sản phẩm với nhiều đơn vị tính (bao, kg, cái, thùng...).

### 3. Khách Hàng & Công Nợ
- Quản lý thông tin khách hàng và lịch sử mua hàng.
- Theo dõi hạn mức công nợ và lịch sử thanh toán.

### 4. Báo Cáo & Tài Chính
- Báo cáo doanh thu theo ngày/tháng.
- Báo cáo công nợ phải thu.
- **Tuân thủ TT88**: Tự động tạo các bút toán doanh thu, nhập/xuất kho theo quy định.

### 5. Phân Quyền (RBAC)
- **Admin**: Quản trị hệ thống, tạo tài khoản chủ cửa hàng.
- **Owner**: Quản lý toàn bộ hoạt động cửa hàng, xem báo cáo.
- **Employee**: Bán hàng, tạo đơn, theo dõi kho (nhưng không xem báo cáo tài chính).

---

## Công Nghệ Sử Dụng

- **Backend**: Python (Flask)
- **Database**: MySQL 8.0
- **Cache**: Redis (Optional)
- **ORM**: SQLAlchemy
- **Auth**: JWT (Flask-JWT-Extended)
- **API Docs**: Swagger/OpenAPI

---

##  Hướng Dẫn Cài Đặt & Chạy

### Yêu Cầu
- Python 3.10+
- MySQL Server (hoặc Docker)
- Redis (Tùy chọn)

### Cách 1: Chạy Local (Dev)

1. **Chuẩn bị Database**
   Chạy lệnh SQL để tạo database:
   ```sql
   CREATE DATABASE bizflow CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
   Cấu hình file `.env` trong thư mục `src`:
   ```ini
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_DATABASE=bizflow
   ```

2. **Cài đặt thư viện**
   ```bash
   # Kích hoạt môi trường ảo
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac

   # Cài đặt requirements
   pip install -r src/requirements.txt
   ```

3. **Khởi chạy Server**
   ```bash
   python .\src\app.py
   ```
   Server sẽ chạy tại: `http://localhost:9999`

4. **Tạo Dữ Liệu Mẫu**
   Mở terminal khác và chạy:
   ```bash
   python src/seed.py
   ```

### Cách 2: Chạy bằng Docker Compose

```bash
docker-compose up -d --build
```

---

##  API Documentation

Truy cập Swagger UI để xem và test API:
 **[http://localhost:9999/docs](http://localhost:9999/docs)**

### Tài Khoản Test Mặc Định

| Vai Trò | Email | Mật Khẩu | Ghi Chú |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@bizflow.vn` | `admin123` | Quản trị hệ thống |
| **Owner** | `owner@bizflow.vn` | `owner123` | Chủ cửa hàng |
| **Employee** | `nhanvien@bizflow.vn` | `nhanvien123` | Nhân viên bán hàng |

---

##  Ví Dụ Sử Dụng (Curl)

### Đăng Nhập (Lấy Token)
```bash
curl -X POST http://localhost:9999/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "owner@bizflow.vn", "password": "owner123"}'
```

### Tạo Đơn Hàng Mới
```bash
curl -X POST http://localhost:9999/api/v1/orders \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": 1,
    "customer_id": 1,
    "items": [
      {"product_unit_id": 1, "quantity": 10},
      {"product_unit_id": 3, "quantity": 5}
    ]
  }'
```

### Tạo Draft Order bằng AI (Text)
```bash
curl -X POST http://localhost:9999/api/v1/ai/draft-orders \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": 1,
    "text": "Lấy 10 bao xi măng cho chú Ba, ghi nợ"
  }'
```

---

##  Cấu Trúc Dự Án (Clean Architecture)

```
src/
├── api/                # Controllers & Routes
├── domain/             # Business Rules & Entities
├── services/           # Application Logic
├── infrastructure/     # Database Models & External Services
├── app.py              # Main Application Entry
├── config.py           # App Configuration
├── seed.py             # Sample Data Script
└── requirements.txt    # Python Dependencies
```

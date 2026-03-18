# Nest & Love - Intelligent E-commerce & Recommendation System

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.2-green.svg)
![Polars](https://img.shields.io/badge/polars-Fast_Data_Processing-orange.svg)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?logo=tailwind-css&logoColor=white)


## Tính năng Nổi bật

### 1. Data Pipeline & Tiền xử lý tự động (Automated Preprocessing)
* Tự động làm sạch dữ liệu và loại bỏ các sản phẩm đã ngừng kinh doanh (`sale_status = 0`).
* **Sử dụng Regular Expression (Regex)** để bóc tách các thông tin phi cấu trúc bị ẩn trong phần mô tả (Description) hoặc Tên sản phẩm, cụ thể là **Kích cỡ (Size)** và **Quy cách đóng gói (Piece)** của mặt hàng Tã/Bỉm.

### 2. Thuật toán Khuyến nghị
Thuật toán là sự kết hợp giữa **Lọc cộng tác (Collaborative Filtering)**, **Lọc theo nội dung (Content-based)** và **Luật kinh doanh (Business Rules)**:
* **Thuật toán cốt lõi:** Đề xuất chéo (Cross-sale) dựa trên tần suất mua chung (Co-buy frequency) từ hàng ngàn lịch sử giao dịch khách hàng.
* **Chiến lược Up-sale Đặc thù:** Tự động nhận diện ngành hàng "Tã", phân tích size hiện tại và khuếch đại điểm số cho các sản phẩm có kích cỡ lớn hơn (Up-sale) bám sát chu kỳ tăng trưởng của em bé.
* **Laplace Smoothing:** Xử lý triệt để bài toán *Cold-Start* cho các sản phẩm mới bằng hằng số smoothing `+0.1`, đảm bảo sản phẩm mới vẫn có cơ hội lọt Top đề xuất.

---

## Cấu trúc Thư mục (Project Structure)

```text
NestAndLove/
│
├── data/                               
│   ├── items.parquet                  
│   └── transactions-2025-12.parquet    
│
├── templates/                        
│   ├── index.html                    
│   ├── detail.html                    
│   └── cart.html                     
│
├── app.py                             
├── models.py                                       
└── README.md                      

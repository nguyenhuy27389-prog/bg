# Ứng dụng tạo báo giá

Ứng dụng dòng lệnh hỗ trợ đọc danh sách sản phẩm từ Excel và xuất báo giá PDF với mẫu được định dạng bằng HTML/CSS.

## Cài đặt

1. Tạo và kích hoạt môi trường ảo (khuyến nghị):

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Trên Windows: .venv\\Scripts\\activate
   ```

2. Cài đặt các thư viện cần thiết:

   ```bash
   pip install pandas jinja2 weasyprint
   ```

   > **Lưu ý:** WeasyPrint phụ thuộc vào một số thư viện hệ thống (GTK, Pango, Cairo…). Tham khảo tài liệu chính thức của [WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation) để chuẩn bị môi trường tương ứng với hệ điều hành của bạn.

## Chuẩn bị dữ liệu Excel

File Excel cần chứa ít nhất các cột sau:

- `code`: Mã sản phẩm.
- `name`: Tên hoặc mô tả sản phẩm.
- `unit_price`: Đơn giá (số).

Có thể bổ sung thêm các cột tùy chọn như `unit` (đơn vị tính), `description` (mô tả chi tiết) hay các cột khác. Ứng dụng sẽ tự động đưa các trường có sẵn vào báo giá.

Ví dụ tối giản trong Excel:

| code | name                | unit_price | unit | description        |
|------|---------------------|------------|------|--------------------|
| SP01 | Máy in laser A4     | 3200000    | bộ  | Bảo hành 12 tháng |
| SP02 | Giấy in A4 80gsm    | 55000      | ram |                    |

## Tạo báo giá

Sau khi có file Excel (ví dụ `data.xlsx`), chạy lệnh:

```bash
python -m quote_app \
  --input data.xlsx \
  --output bao_gia.pdf \
  --customer "Công ty TNHH XYZ" \
  --items SP01:2 SP02:10 \
  --note "Giá đã bao gồm chi phí vận chuyển nội thành." \
  --tax-rate 8
```

Các tuỳ chọn hữu ích khác:

- `--customer-company`, `--customer-address`: Bổ sung thông tin khách hàng.
- `--company-name`, `--company-address`, `--company-phone`, `--company-email`, `--company-website`, `--company-tax-code`: Tùy biến thông tin công ty phát hành báo giá.
- `--logo`: Chỉ định đường dẫn logo (định dạng PNG/SVG/JPG) để hiển thị trong báo giá.
- `--template-file`: Sử dụng mẫu HTML tùy chỉnh (Jinja2). Nếu không cung cấp, ứng dụng dùng mẫu mặc định trong mã nguồn.
- `--currency-symbol`: Đổi ký hiệu tiền tệ hiển thị.
- `--footer`: Thêm ghi chú chân trang (ví dụ điều khoản thanh toán).

Sau khi chạy lệnh thành công, file PDF báo giá sẽ được tạo tại đường dẫn đã chỉ định trong tham số `--output`.

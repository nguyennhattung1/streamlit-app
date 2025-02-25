# Sử dụng image Python 3.10-slim
FROM python:3.10-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Sao chép file requirements.txt vào container và cài đặt các phụ thuộc
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào container
COPY segments_16k /app/segments_16k
COPY re_check.py /app/re_check.py
COPY verified_batches /app/verified_batches

# Tạo thư mục config trong /app/.streamlit/
RUN mkdir -p /app/.streamlit

# Tạo file cấu hình config.toml với CORS được bật
RUN echo "[server]\n\
headless = true\n\
enableCORS = true\n\
enableXsrfProtection = false\n\
port = 8501\n\
[browser]\n\
serverAddress = '0.0.0.0'" > /app/.streamlit/config.toml

# Mở port mà Streamlit sử dụng (mặc định là 8501)
EXPOSE 8501

# Khai báo biến môi trường để Streamlit đọc config từ /app/.streamlit/
ENV STREAMLIT_CONFIG="/app/.streamlit/config.toml"

# Chạy ứng dụng Streamlit
CMD ["streamlit", "run", "re_check.py", "--server.port=8501", "--server.address=0.0.0.0"]
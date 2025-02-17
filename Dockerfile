# Sử dụng image Python 3.10-slim
FROM python:3.10-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Sao chép file requirements.txt vào container và cài đặt các phụ thuộc
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào container
COPY segments_16k /app/segments_16k
COPY building.py /app/building.py
COPY batches /app/batches

# Mở port mà Streamlit sử dụng (mặc định là 8501)
EXPOSE 8501

# Chạy ứng dụng Streamlit (sử dụng file buildind.py)
CMD ["streamlit", "run", "building.py", "--server.port", "8501", "--server.enableCORS", "false"]

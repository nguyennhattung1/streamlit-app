import streamlit as st
import pandas as pd
import os


def safe_rerun():
    """
    Gọi hàm rerun phù hợp với phiên bản Streamlit hiện tại.
    Sử dụng st.rerun() (Streamlit >=1.27) hoặc st.experimental_rerun() nếu cần.
    """
    try:
        if hasattr(st, "rerun"):
            st.rerun()
        elif hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
    except Exception:
        pass


# Thư mục chứa các file CSV batch đã được xác nhận
BATCH_DIR = "verified_batches"


def load_batch_file():
    """
    Đọc file CSV đã được xác nhận (từ session_state).
    Tạo cột 'audio_path' dựa vào cột đã có trong CSV và chỉ load những dòng có tag là "Yes".
    """
    csv_path = os.path.join(BATCH_DIR, st.session_state.confirmed_csv)
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        st.stop()

    if "audio_path" not in df.columns:
        st.error("CSV file must have an 'audio_path' column.")
        st.stop()

    # Nếu cần chuyển đổi audio_path (ở đây chỉ giữ nguyên giá trị)
    df["audio_path"] = df["audio_path"].apply(lambda x: f"{x}")

    # Lọc các dòng có tag bằng "Yes"
    if "tag" in df.columns:
        df = df[df["tag"] == "Yes"]
        df = df.reset_index(drop=True)
    else:
        st.error("CSV file must have a 'tag' column.")
        st.stop()

    return df


def initialize_state_from_file():
    """
    Khởi tạo các biến điều hướng và chỉnh sửa dựa trên file CSV đã xác nhận.
    
    Thiết lập các biến sau trong session_state:
      - current_index: chỉ số dòng hiện tại (khởi tạo bằng 0)
      - edited_transcripts: danh sách transcript từ CSV
      - tags: danh sách tag từ CSV
      - confirmed_rows: danh sách trạng thái confirm cho mỗi dòng (False ban đầu)
      - row_confirmed: cờ báo dòng đã được chọn hiển thị chi tiết
    """
    df = load_batch_file()
    st.session_state.current_index = 0
    st.session_state.edited_transcripts = df["transcripts"].tolist()
    st.session_state.tags = df["tag"].tolist()
    st.session_state.confirmed_rows = [False] * len(df)
    st.session_state.row_confirmed = False


def display_item(df, index):
    """
    Hiển thị audio và transcript của dòng được chọn.
    Có ba nút: "Yes", "No" để cập nhật tag và nút "Confirm" có chức năng toggle highlight.
    """
    if 0 <= index < len(df):
        audio_path = df["audio_path"].iloc[index]
        transcript = st.session_state.edited_transcripts[index]

        if os.path.exists(audio_path):
            st.audio(audio_path, format="audio/wav")
        else:
            st.error(f"Audio file not found: {audio_path}")

        def update_transcript(new_text):
            st.session_state.edited_transcripts[index] = new_text

        st.text_area(
            "Transcript",
            value=transcript,
            height=100,
            key=f"transcript_{index}",
            on_change=lambda: update_transcript(
                st.session_state.get(f"transcript_{index}", transcript)
            ),
        )

        col1, col2, col3 = st.columns(3)
        if col1.button("Yes", key=f"yes_{index}"):
            st.session_state.tags[index] = "Yes"
        if col2.button("No", key=f"no_{index}"):
            st.session_state.tags[index] = "No"

        # Xác định trạng thái hiện tại của nút confirm và thay đổi nhãn tương ứng
        current_confirm_state = st.session_state.confirmed_rows[index]
        confirm_label = "Unconfirm" if current_confirm_state else "Confirm"
        if col3.button(confirm_label, key=f"confirm_{index}"):
            st.session_state.confirmed_rows[index] = not current_confirm_state
            safe_rerun()
        return True
    else:
        st.write("No more items.")
        return False


def main():
    # Liệt kê tất cả các file CSV trong BATCH_DIR
    csv_files = sorted([f for f in os.listdir(BATCH_DIR) if f.endswith(".csv")])
    if not csv_files:
        st.error("No CSV files found in the verified_batches directory.")
        st.stop()

    # Khởi tạo các key trong session_state nếu chưa tồn tại
    if "batch_confirmed" not in st.session_state:
        st.session_state.batch_confirmed = False
    if "confirmed_csv" not in st.session_state:
        st.session_state.confirmed_csv = None
    if "selected_row" not in st.session_state:
        st.session_state.selected_row = 0
    if "row_confirmed" not in st.session_state:
        st.session_state.row_confirmed = False

    # Sidebar: Nếu file batch chưa được xác nhận, hiển thị widget chọn file.
    if not st.session_state.batch_confirmed:
        chosen_file = st.sidebar.selectbox(
            "Chọn file Batch CSV", csv_files, key="selected_csv"
        )
        if st.sidebar.button("Confirm Batch File"):
            st.session_state.confirmed_csv = chosen_file
            st.session_state.batch_confirmed = True
            initialize_state_from_file()
            safe_rerun()
    else:
        st.sidebar.markdown(
            f"**Batch file confirmed:** {st.session_state.confirmed_csv}"
        )
        if st.sidebar.button("Cancel Batch File"):
            for key in [
                "batch_confirmed",
                "confirmed_csv",
                "current_index",
                "edited_transcripts",
                "tags",
                "confirmed_rows",
                "selected_row",
                "row_confirmed",
            ]:
                st.session_state.pop(key, None)
            safe_rerun()

    if not st.session_state.batch_confirmed:
        st.info("Vui lòng confirm file batch để tiếp tục.")
        st.stop()

    # Load file CSV đã xác nhận
    df = load_batch_file()
    df = pd.DataFrame(df, columns=["audio_path", "transcripts", "tag"])

    # Cập nhật các biến session state nếu độ dài không khớp với DataFrame
    if "edited_transcripts" not in st.session_state or len(st.session_state.edited_transcripts) != len(df):
        st.session_state.edited_transcripts = df["transcripts"].tolist()
    if "tags" not in st.session_state or len(st.session_state.tags) != len(df):
        st.session_state.tags = df["tag"].tolist()
    if "confirmed_rows" not in st.session_state or len(st.session_state.confirmed_rows) != len(df):
        st.session_state.confirmed_rows = [False] * len(df)

    # Cập nhật DataFrame với giá trị mới từ session state
    df["transcripts"] = st.session_state.edited_transcripts
    df["tag"] = st.session_state.tags

    # Tạo container hiển thị preview bảng với style thay đổi dựa trên trạng thái confirm
    preview_container = st.empty()

    def highlight_confirmed(row):
        if st.session_state.confirmed_rows[row.name]:
            return ['background-color: lightgreen'] * len(row)
        else:
            return [''] * len(row)

    styled_df = df.style.apply(highlight_confirmed, axis=1)
    preview_container.write("### DataFrame Preview (Updated):")
    preview_container.dataframe(styled_df)

    # Hiển thị số dòng đã confirm
    confirmed_count = st.session_state.confirmed_rows.count(True)
    st.markdown(f"**Đã confirm:** {confirmed_count} dòng")

    # Selectbox để chọn dòng hiển thị chi tiết
    selected_row_widget = st.selectbox(
        "Select a row to view details",
        list(range(len(df))),
        index=st.session_state.selected_row,
        format_func=lambda i: f"Index {i}: {df.loc[i, 'transcripts'][:100]}",
        key="selected_row",
    )
    temp_selected_row = selected_row_widget

    # Nút xác nhận dòng được chọn
    if st.button("Confirm Row Selection"):
        st.session_state.current_index = temp_selected_row
        st.session_state.row_confirmed = True
        safe_rerun()

    # Nếu đã xác nhận dòng, hiển thị chi tiết (audio và transcript kèm nút confirm)
    if st.session_state.row_confirmed:
        st.write("### Detail View:")
        display_item(df, st.session_state.current_index)
    else:
        st.info("Vui lòng nhấn 'Confirm Row Selection' để hiển thị chi tiết của dòng đã chọn.")

    # Các nút điều hướng chuyển đến dòng trước/sau
    col1, col2 = st.columns(2)
    if col1.button("Previous"):
        st.session_state.current_index = max(0, st.session_state.current_index - 1)
        st.session_state.row_confirmed = True
        safe_rerun()
    if col2.button("Next"):
        st.session_state.current_index += 1
        if st.session_state.current_index >= len(df):
            st.session_state.current_index = len(df) - 1
            st.warning("Bạn đang ở mục cuối cùng.")
        st.session_state.row_confirmed = True
        safe_rerun()

    # Nút download CSV với dữ liệu đã được cập nhật
    if st.button("Download Data (CSV)"):
        # Cập nhật DataFrame với transcript và tag mới nhất
        df["transcripts"] = st.session_state.edited_transcripts
        df["tag"] = st.session_state.tags
        csv_file = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="Download CSV",
            data=csv_file,
            file_name="tagged_data.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
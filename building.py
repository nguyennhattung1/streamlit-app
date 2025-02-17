import streamlit as st
import pandas as pd
import os


def safe_rerun():
    """
    Gọi hàm rerun phù hợp với phiên bản Streamlit.
    Nếu có st.rerun() (Streamlit >=1.27) thì dùng, ngược lại dùng st.experimental_rerun().
    Bắt các exception do rerun gây ra để không hiển thị traceback.
    """
    try:
        if hasattr(st, "rerun"):
            st.rerun()
        elif hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
    except Exception:
        pass


# Thư mục chứa các file CSV batch
BATCH_DIR = "batches"


def load_batch_file():
    """
    Đọc file CSV đã được xác nhận (từ confirmed_csv) và tạo cột 'audio_path' từ cột 'filename'.
    """
    csv_path = os.path.join(BATCH_DIR, st.session_state.confirmed_csv)
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        st.stop()
    if "filename" in df.columns:
        df["audio_path"] = df["filename"].apply(lambda x: f"segments_16k/{x}.wav")
    else:
        st.error("CSV file must have a 'filename' column.")
        st.stop()
    return df


def initialize_state_from_file():
    """
    Khởi tạo các biến điều hướng và chỉnh sửa từ file CSV đã được xác nhận.
    Các biến:
      - current_index: chỉ số dòng hiện tại.
      - edited_transcripts: danh sách transcript từ file.
      - tags: danh sách tag, khởi tạo ban đầu là None.
      - row_confirmed: cờ cho biết dòng đã được xác nhận để hiển thị Detail View.
    """
    df = load_batch_file()
    st.session_state.current_index = 0
    st.session_state.edited_transcripts = df["transcripts"].tolist()
    st.session_state.tags = [None] * len(df)
    st.session_state.row_confirmed = False


def display_item(df, index):
    """
    Hiển thị audio và transcript của dòng có chỉ số index.
    Có 2 nút "Yes" và "No" để cập nhật tag cho dòng đó.
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

        col1, col2 = st.columns(2)
        if col1.button("Yes", key=f"yes_{index}"):
            st.session_state.tags[index] = "Yes"
        if col2.button("No", key=f"no_{index}"):
            st.session_state.tags[index] = "No"
        return True
    else:
        st.write("No more items.")
        return False


def main():
    # Liệt kê các file CSV có trong thư mục batches
    csv_files = sorted([f for f in os.listdir(BATCH_DIR) if f.endswith(".csv")])
    if not csv_files:
        st.error("No CSV files found in the batches directory.")
        st.stop()

    # Khởi tạo các key trong session state nếu chưa có
    if "batch_confirmed" not in st.session_state:
        st.session_state.batch_confirmed = False
    if "confirmed_csv" not in st.session_state:
        st.session_state.confirmed_csv = None
    if "selected_row" not in st.session_state:
        st.session_state.selected_row = 0
    if "row_confirmed" not in st.session_state:
        st.session_state.row_confirmed = False

    # Sidebar: Nếu batch chưa được confirm, hiển thị widget chọn file
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
                "selected_row",
                "row_confirmed",
            ]:
                st.session_state.pop(key, None)
            safe_rerun()

    if not st.session_state.batch_confirmed:
        st.info("Vui lòng confirm file batch để tiếp tục.")
        st.stop()

    # Tải file CSV đã được xác nhận
    df = load_batch_file()
    df = pd.DataFrame(df, columns=["audio_path", "transcripts", "tag"])

    # Cập nhật lại các biến nếu số lượng không khớp
    if "edited_transcripts" not in st.session_state or len(
        st.session_state.edited_transcripts
    ) != len(df):
        st.session_state.edited_transcripts = df["transcripts"].tolist()
    if "tags" not in st.session_state or len(st.session_state.tags) != len(df):
        st.session_state.tags = [None] * len(df)

    # Container cho DataFrame Preview cập nhật liên tục
    preview_container = st.empty()
    df["transcripts"] = st.session_state.edited_transcripts
    df["tag"] = st.session_state.tags
    preview_container.write("### DataFrame Preview (Updated):")
    preview_container.dataframe(df)

    # Hiển thị đếm số lượng tag chưa cập nhật (None)
    remaining = st.session_state.tags.count(None)
    if remaining > 0:
        st.markdown(
            f"<span style='color:red;'>Số tag chưa cập nhật: {remaining}</span>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<span style='color:green;'>Tất cả tag đã được cập nhật!</span>",
            unsafe_allow_html=True,
        )

    # Selectbox để chọn dòng hiển thị detail (không thay đổi giá trị của widget)
    selected_row_widget = st.selectbox(
        "Select a row to view details",
        list(range(len(df))),
        index=st.session_state.selected_row,
        format_func=lambda i: f"Index {i}: {df.loc[i, 'transcripts'][:50]}",
        key="selected_row",
    )
    temp_selected_row = selected_row_widget

    # Nút xác nhận dòng
    if st.button("Confirm Row Selection"):
        st.session_state.current_index = temp_selected_row
        st.session_state.row_confirmed = True

    # Nếu đã xác nhận dòng, hiển thị Detail View (audio và transcript)
    if st.session_state.row_confirmed:
        st.write("### Detail View:")
        display_item(df, st.session_state.current_index)
    else:
        st.info(
            "Vui lòng nhấn 'Confirm Row Selection' để hiển thị chi tiết của dòng đã chọn."
        )

    # Các nút điều hướng Previous/Next (cập nhật current_index)
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

    # Nút tải file CSV đã cập nhật (với các thay đổi transcript và tag)
    if st.button("Download Data (CSV)"):
        csv_file = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="Download CSV",
            data=csv_file,
            file_name="tagged_data.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()

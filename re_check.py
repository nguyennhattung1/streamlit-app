import streamlit as st
import pandas as pd
import os


def safe_rerun():
    """
    Call the appropriate rerun function depending on the Streamlit version.
    Uses st.rerun() (Streamlit >=1.27) or st.experimental_rerun() as a fallback.
    Exceptions raised during rerun are caught to avoid displaying tracebacks.
    """
    try:
        if hasattr(st, "rerun"):
            st.rerun()
        elif hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
    except Exception:
        pass


# Directory containing the CSV batch files
BATCH_DIR = "verified_batches"


def load_batch_file():
    """
    Read the confirmed CSV file from the session state.
    Creates an 'audio_path' column by prepending the fixed directory path to each file name.
    """
    csv_path = os.path.join(BATCH_DIR, st.session_state.confirmed_csv)
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        st.stop()
    if "audio_path" in df.columns:
        df["audio_path"] = df["audio_path"]
    else:
        st.error("CSV file must have an 'audio_path' column.")
        st.stop()
    return df


def initialize_state_from_file():
    """
    Initialize navigation and editing variables based on the confirmed CSV file.
    
    Sets the following session state variables:
      - current_index: the current row index (initialized to 0)
      - edited_transcripts: list of transcripts loaded from the CSV
      - tags: list of tags loaded from the CSV if the 'tag' column exists,
              otherwise a list of None values
      - row_confirmed: flag indicating whether the row has been confirmed for detail view
    """
    df = load_batch_file()
    st.session_state.current_index = 0
    st.session_state.edited_transcripts = df["transcripts"].tolist()
    # If a 'tag' column exists, load its values; otherwise, initialize with None.
    st.session_state.tags = df["tag"].tolist() if "tag" in df.columns else [None] * len(df)
    st.session_state.row_confirmed = False


def display_item(df, index):
    """
    Display the audio and transcript for the row at the given index.
    Two buttons ("Yes" and "No") update the tag for that row.
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
    # List all CSV files in the BATCH_DIR
    csv_files = sorted([f for f in os.listdir(BATCH_DIR) if f.endswith(".csv")])
    if not csv_files:
        st.error("No CSV files found in the unverified_batches directory.")
        st.stop()

    # Initialize keys in session state if they do not exist
    if "batch_confirmed" not in st.session_state:
        st.session_state.batch_confirmed = False
    if "confirmed_csv" not in st.session_state:
        st.session_state.confirmed_csv = None
    if "selected_row" not in st.session_state:
        st.session_state.selected_row = 0
    if "row_confirmed" not in st.session_state:
        st.session_state.row_confirmed = False

    # Sidebar: If the batch file is not yet confirmed, show the file selection widget.
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

    # Load the confirmed CSV file.
    df = load_batch_file()
    df = pd.DataFrame(df, columns=["audio_path", "transcripts", "tag"])

    # Update session state variables if the lengths do not match the DataFrame.
    if "edited_transcripts" not in st.session_state or len(st.session_state.edited_transcripts) != len(df):
        st.session_state.edited_transcripts = df["transcripts"].tolist()
    if "tags" not in st.session_state or len(st.session_state.tags) != len(df):
        st.session_state.tags = df["tag"].tolist() if "tag" in df.columns else [None] * len(df)

    # Create a container for the DataFrame preview that updates continuously.
    preview_container = st.empty()
    df["transcripts"] = st.session_state.edited_transcripts
    df["tag"] = st.session_state.tags
    preview_container.write("### DataFrame Preview (Updated):")
    preview_container.dataframe(df)

    # Display the count of rows whose tag is still None.
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

    # Selectbox for choosing a row to view details (this widget does not change the session state by itself)
    selected_row_widget = st.selectbox(
        "Select a row to view details",
        list(range(len(df))),
        index=st.session_state.selected_row,
        format_func=lambda i: f"Index {i}: {df.loc[i, 'transcripts'][:50]}",
        key="selected_row",
    )
    temp_selected_row = selected_row_widget

    # Button to confirm the selected row.
    if st.button("Confirm Row Selection"):
        st.session_state.current_index = temp_selected_row
        st.session_state.row_confirmed = True

    # If a row has been confirmed, display its detail view (audio and transcript).
    if st.session_state.row_confirmed:
        st.write("### Detail View:")
        display_item(df, st.session_state.current_index)
    else:
        st.info("Vui lòng nhấn 'Confirm Row Selection' để hiển thị chi tiết của dòng đã chọn.")

    # Navigation buttons to move to the previous/next row.
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

    # Button to download the updated CSV file (with changes to transcripts and tags).
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
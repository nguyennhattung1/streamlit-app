import streamlit as st
import pandas as pd
import json

data = []
with open("segments_16k/metadata_asr_v2.json", "r", encoding="utf-8") as f:
    for line in f.readlines():
        seg = {}
        x = json.loads(line.strip())
        seg["audio_path"] = f'segments_16k/{x["filename"]}.wav'
        seg["transcript"] = x["transcripts"]
        data.append(seg)


df = pd.DataFrame(data)

if "current_index" not in st.session_state:
    st.session_state.current_index = 0

if "edited_transcripts" not in st.session_state:
    st.session_state.edited_transcripts = df["transcript"].copy()
if "tags" not in st.session_state:
    st.session_state.tags = ["None"] * len(df)


def display_item(index):
    if 0 <= index < len(df):
        audio_path = df["audio_path"][index]
        transcript = st.session_state.edited_transcripts[index]

        st.audio(audio_path, format="audio/wav")

        def update_transcript(index, new_text):
            st.session_state.edited_transcripts[index] = new_text

        st.text_area(
            "Transcript",
            value=transcript,
            height=100,
            key=f"transcript_{index}",
            on_change=lambda: update_transcript(
                index, st.session_state[f"transcript_{index}"]
            ),
        )

        col1, col2 = st.columns(2)

        if col1.button("Yes", key=f"yes_{index}"):
            st.session_state.tags[index] = "Yes"
            st.rerun()
        if col2.button("No", key=f"no_{index}"):
            st.session_state.tags[index] = "No"
            st.rerun()
        return True
    else:
        st.write("No more items.")
        return False


if display_item(st.session_state.current_index):
    col1, col2 = st.columns(2)

    if col1.button("Previous"):
        st.session_state.current_index = max(0, st.session_state.current_index - 1)
        st.rerun()

    if col2.button("Next"):
        st.session_state.current_index += 1
        if st.session_state.current_index >= len(df):
            st.session_state.current_index = len(df) - 1
            st.warning("You are at the last item.")
        st.rerun()

df["transcript"] = st.session_state.edited_transcripts
df["tag"] = st.session_state.tags
if st.button("Download Data (CSV)"):
    csv_file = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        label="Download CSV",
        data=csv_file,
        file_name="tagged_data.csv",
        mime="text/csv",
    )

import pandas as pd


def main():
    path = "batch_13.csv"
    df = pd.read_csv(path)

    # Thêm cột 'tag' với giá trị mặc định là "yes"
    df["tags"] = "Yes"

    # Giữ lại 3 cột: audio_path, transcripts, tag
    df_selected = df[["audio_path", "transcripts", "tags"]]

    # Lưu DataFrame vào file csv mới tên là batch_13.csv
    output_path = "batch_131.csv"
    df_selected.to_csv(output_path, index=False)
    print(f"Đã lưu file mới: {output_path}")


if __name__ == "__main__":
    main()

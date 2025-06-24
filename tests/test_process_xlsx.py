from app.process_xlsx import extract_comments_by_video_id, dict_to_json

if __name__ == "__main__":
    file_path = "output.xlsx"  # 请根据实际路径修改
    data = extract_comments_by_video_id(file_path)

    for k,v in data.items():
        print(f"{k}:{len(v)}")
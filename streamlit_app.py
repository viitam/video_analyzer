import streamlit as st
import boto3

def upload_file(file, s3_key, s3_bucket_name):
    try:
        # S3クライアントの作成
        s3 = boto3.client('s3', region_name='ap-northeast-1')  # 例: 東京リージョン
        # S3にファイルをアップロード
        s3.upload_fileobj(file, s3_bucket_name, s3_key)
        st.success("動画がS3にアップロードされました")
    except Exception as e:
        st.error(f"エラー: {e}")

def main():
    st.title("動画アップロード")
    st.write("アップロードした動画はAmazon S3に保存されます")

    # ファイルアップロードのUI
    uploaded_file = st.file_uploader("動画ファイルを選択してください", type=["mp4", "mov", "avi"])

    if uploaded_file is not None:
        # S3にアップロードするためのファイルパス設定
        file_name = "video/" + uploaded_file.name

        # アップロードボタン
        if st.button("アップロード"):
            # ファイルをS3にアップロード
            upload_file(uploaded_file, file_name, s3_bucket_name="tq-video-archive")

if __name__ == "__main__":
    main()

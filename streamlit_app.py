import streamlit as st
import boto3
from datetime import datetime
import json
import os
import tempfile
from moviepy.editor import VideoFileClip

def upload_file(file, s3_key, s3_bucket_name):
    try:
        s3 = boto3.client('s3', region_name='ap-northeast-1')
        s3.upload_fileobj(file, s3_bucket_name, s3_key)
        st.success("動画がS3にアップロードされました")
    except Exception as e:
        st.error(f"エラー: {e}")

def get_data_from_s3(bucket_name, key, data_type):
    """
    S3からデータを取得し、ファイルタイプに応じてデータを返す関数。

    Parameters:
    - bucket_name (str): S3バケット名
    - key (str): S3のオブジェクトキー
    - data_type (str): 取得するデータのタイプ ("json", "audio", "image")

    Returns:
    - データの内容に応じたデータオブジェクト
    """
    s3 = boto3.client('s3')
    try:
        response = s3.get_object(Bucket=bucket_name, Key=key)
        if data_type == "json":
            return json.loads(response['Body'].read().decode('utf-8'))
        elif data_type in ["audio", "image"]:
            return response['Body'].read()  # バイナリデータを返す
        else:
            st.error("不正なデータタイプが指定されました")
            return None
    except Exception as e:
        st.error(f"{data_type}ファイルの取得中にエラーが発生しました: {e}")
        return None

def main():
    st.title("動画アップロード")
    st.write("アップロードした動画はAmazon S3に保存されます")

    s3_bucket_name_out = "tq-lambda-result"
    st.session_state.s3_bucket_name_out = s3_bucket_name_out
    audio_bucket_name = "tq-tmp-audio"  # 音声ファイルのS3バケット
    photo_bucket_name = "tq-tmp-photo"  # 画像ファイルのS3バケット

    uploaded_file = st.file_uploader("動画ファイルを選択してください", type=["mp4", "mov", "avi"])

    if 'hashid' not in st.session_state:
        st.session_state.hashid = None
        st.session_state.output_path = None
        st.session_state.basename = None
        st.session_state.uploaded_file_name = None

    if uploaded_file is not None:
        if not st.session_state.hashid:
            st.session_state.hashid = datetime.now().strftime('%Y%m%d%H%M%S')
        
        base_name = os.path.splitext(uploaded_file.name)[0]
        s3_key = f"{st.session_state.hashid}{uploaded_file.name}"
        st.session_state.uploaded_file_name = s3_key        
        st.session_state.basename = base_name
        st.session_state.output_path = f"{s3_bucket_name_out}/{st.session_state.hashid}{base_name}"

        # 動画の再生時間取得
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
                temp_file.write(uploaded_file.read())  # 一時ファイルにアップロードデータを書き込み
                temp_file_path = temp_file.name

            with VideoFileClip(temp_file_path) as video:
                duration = video.duration
            
            st.write(f"動画の長さ: {duration} 秒")
            os.unlink(temp_file_path)  # 一時ファイルを削除
        except Exception as e:
            st.error(f"動画の読み込み中にエラーが発生しました: {e}")
            return

        json_file_count = int(duration // 30) + 1
        json_file_count2 = int(duration // 5) + 1

        if st.button("アップロード"):
            uploaded_file.seek(0)
            upload_file(uploaded_file, s3_key, s3_bucket_name="tq-video-archive")
            st.write("Lambda関数で処理されたJSON結果を表示します")

    if st.session_state.uploaded_file_name:
        st.write(f"**アップロードされたファイル名: {st.session_state.uploaded_file_name}**")
        st.write(f"**出力先: {st.session_state.output_path}**")

    if st.button("最新の結果を取得"):
        for i in range(1, json_file_count + 1):
            key = f"{st.session_state.hashid}{st.session_state.basename}/{st.session_state.hashid}{st.session_state.basename}_audio_{i:05}.json"
            st.write(f"{(i-1)*30} ~{i*30}sec までの音声文字起こし")
            json_data = get_data_from_s3(s3_bucket_name_out, key, "json")
            if json_data:
                audio_key = f"{st.session_state.hashid}{st.session_state.basename}/{st.session_state.hashid}{st.session_state.basename}_audio_{i:05}.mp4"  # 音声ファイルのキー
                audio_data = get_data_from_s3(audio_bucket_name, audio_key, "audio")
                st.write(audio_key)
                st.audio(audio_data)  # 音声ファイルを埋め込み
                st.json(json_data)
        
        for i in range(0, json_file_count2):
            key = f"{st.session_state.hashid}{st.session_state.basename}/{st.session_state.hashid}{st.session_state.basename}_photo_{i:07}.json"
            st.write(f"{i*5}sec の写真")
            json_data = get_data_from_s3(s3_bucket_name_out, key, "json")
            if json_data:
                photo_key = f"{st.session_state.hashid}{st.session_state.basename}/{st.session_state.hashid}{st.session_state.basename}_photo_{i:07}.jpg"  # 画像ファイルのキー
                photo_data = get_data_from_s3(photo_bucket_name, photo_key, "image")
                st.image(photo_data)
                st.json(json_data)


if __name__ == "__main__":
    main()

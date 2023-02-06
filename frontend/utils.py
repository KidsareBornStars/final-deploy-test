import os
import av
import time
import cv2
from google.cloud import storage


def upload_video(file_path, upload_path, bucket_name="heyi-storage"):
    """_summary_

    Args:
        file_path (_type_): 업로드할 파일의 현재 서버의 파일 경로
        upload_path (_type_): 업로드할 파일의 Google cloud의 파일 경로
        bucket_name (str, optional): 업로드할 bucket 이름. Defaults to "heyi-storage".

    """
    if '\\' in file_path:
        file_path = file_path.replace('\\', '/')
    if '\\' in upload_path:
        upload_path = upload_path.replace('\\', '/')

    assert os.path.exists(file_path), f"{file_path}에 영상이 존재하지 않습니다."
    assert os.path.exists("./frontend/hey-i-375802-d3dcfd2b25d1.json"), "Key가 존재하지 않습니다."
    storage_client = storage.Client.from_service_account_json(
        "./frontend/hey-i-375802-d3dcfd2b25d1.json"
    )
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(upload_path)
    blob.upload_from_filename(file_path)

    # url = blob.public_url
    # return url # upload 된 파일의 경로


def download_video(storage_path, download_path, bucket_name="heyi-storage"):
    """_summary_

    Args:
        storage_path (_type_): 다운로드할 파일의 Google cloud의 파일 경로
        download_path (_type_): 다운로드할 파일의 현재 서버에서의 저장 경로
        bucket_name (str, optional): 다운로드할 bucket 이름. Defaults to "heyi-storage".
    """
    if '\\' in storage_path:
        storage_path = storage_path.replace('\\', '/')
    if '\\' in download_path:
        download_path = download_path.replace('\\', '/')

    assert os.path.exists("./frontend/hey-i-375802-d3dcfd2b25d1.json"), "Key가 존재하지 않습니다."
    storage_client = storage.Client.from_service_account_json(
        "./frontend/hey-i-375802-d3dcfd2b25d1.json"
    )
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(storage_path)
    blob.download_to_filename(download_path)


if __name__ == "__main__":
    # FINAL_PRO... 여기서 실행해야함
    upload_video(
        file_path="./streamlit/recording.webm", upload_path="백우열_2762/recording.webm"
    )
    download_video(
        storage_path="백우열_2762/recording.webm",
        download_path="./streamlit/recording2.webm",
    )


########################################################### WebRTC
def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
    img = frame.to_ndarray(format="bgr24")
    return av.VideoFrame.from_ndarray(img, format="bgr24")


def convert_to_webm(in_file, video_dir):
    start = time.process_time()
    cap = cv2.VideoCapture(in_file)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*"vp80")

    out = cv2.VideoWriter(
        video_dir,
        fourcc,
        fps,
        (width, height),
    )
    while True:
        ret, frame = cap.read()
        if not ret:  # 새로운 프레임을 못받아 왔을 때 braek
            break
        out.write(frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    end = time.process_time()
    
    print(f"Convert Complete: {video_dir} on {end-start}")
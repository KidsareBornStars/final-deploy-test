import os
import cv2
import glob
import pandas as pd
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
    assert os.path.exists("./backend/hey-i-375802-d3dcfd2b25d1.json"), "Key가 존재하지 않습니다."
    storage_client = storage.Client.from_service_account_json(
        "./backend/hey-i-375802-d3dcfd2b25d1.json"
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

    assert os.path.exists("./backend/hey-i-375802-d3dcfd2b25d1.json"), "Key가 존재하지 않습니다."
    storage_client = storage.Client.from_service_account_json(
        "./backend/hey-i-375802-d3dcfd2b25d1.json"
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

def video_to_frame(VIDEO_PATH, SAVED_DIR):

    if not os.path.exists(SAVED_DIR):
        os.makedirs(SAVED_DIR)

    cap = cv2.VideoCapture(VIDEO_PATH)
    count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = cap.get(cv2.CAP_PROP_FPS)/20
    # fps = cap.get(cv2.CAP_PROP_FPS)/11

    while True:  # 무한 루프
        ret, frame = cap.read()  # 두 개의 값을 반환하므로 두 변수 지정

        if not ret:  # 새로운 프레임을 못받아 왔을 때 braek
            break
        if int(cap.get(1)) % int(fps) == 0:
            cv2.imwrite(SAVED_DIR + "/frame%d.jpg" % count, frame)
            print("Saved frame number : ", str(int(cap.get(1))))
            count += 1

        # 10ms 기다리고 다음 프레임으로 전환, Esc누르면 while 강제 종료
        if cv2.waitKey(10) == 27:
            break

    cap.release()  # 사용한 자원 해제
    cv2.destroyAllWindows()

    frames = glob.glob(f"{SAVED_DIR}/*.jpg")
    frames.sort()

    return frames



def make_emotion_df(emotions_mtcnn):
    angry = []
    disgust = []
    fear = []
    happy = []
    sad = []
    surprise = []
    neutral = []
    lenoflist = len(emotions_mtcnn)
    dominant_emotion = []

    for i in range(1, lenoflist + 1):
        tmp = "instance_" + str(i)
        angry.append(emotions_mtcnn[tmp]["emotion"]["angry"])
        disgust.append(emotions_mtcnn[tmp]["emotion"]["disgust"])
        fear.append(emotions_mtcnn[tmp]["emotion"]["fear"])
        happy.append(emotions_mtcnn[tmp]["emotion"]["happy"])
        sad.append(emotions_mtcnn[tmp]["emotion"]["sad"])
        surprise.append(emotions_mtcnn[tmp]["emotion"]["surprise"])
        neutral.append(emotions_mtcnn[tmp]["emotion"]["neutral"])
    df_mtcnn = pd.DataFrame(
        {
            "angry": angry,
            "disgust": disgust,
            "fear": fear,
            "happy": happy,
            "sad": sad,
            "surprise": surprise,
            "neutral": neutral,
        }
    )

    return df_mtcnn


def make_binary_df(emotions_mtcnn, df_mtcnn):
    pos_emo = ["happy", "neutral"]
    neg_emp = ["angry", "disgust", "fear", "sad", "surprise"]
    highest = []
    for i in range(len(df_mtcnn)):
        string = df_mtcnn.iloc[i].idxmax()
        highest.append(string)
    positive = []
    negative = []

    for i in range(1, len(emotions_mtcnn) + 1):
        tmp = "instance_" + str(i)
        p = 0
        n = 0
        if highest[i - 1] in pos_emo:
            p += emotions_mtcnn[tmp]["emotion"]["happy"]
            p += emotions_mtcnn[tmp]["emotion"]["neutral"]

        else:
            n += emotions_mtcnn[tmp]["emotion"]["angry"]
            n += emotions_mtcnn[tmp]["emotion"]["disgust"]
            n += emotions_mtcnn[tmp]["emotion"]["fear"]
            n += emotions_mtcnn[tmp]["emotion"]["sad"]
            n += emotions_mtcnn[tmp]["emotion"]["surprise"]
        positive.append(p)
        negative.append(n)
    df_binary = pd.DataFrame({"positive": positive, "negative": negative})
    return df_binary


def add_emotion_on_frame(emotions_mtcnn, df_mtcnn, saved_dir):
    len_of_df = len(df_mtcnn)
    text_of_rec = []
    for i in range(len_of_df):
        string = (
            df_mtcnn.iloc[i].idxmax()
            + "_"
            + str(round(df_mtcnn.iloc[i][df_mtcnn.iloc[i].idxmax()], 3))
            + "%"
        )
        text_of_rec.append(string)

    regions = []
    for i in range(1, len_of_df + 1):
        tmp = "instance_" + str(i)
        region = emotions_mtcnn[tmp]["region"]
        regions.append(region)

    images = glob.glob(f"{saved_dir}/*.jpg")
    images.sort()

    rec_image_list = []
    for idx, (region, i) in enumerate(zip(regions, images)):
        pth = cv2.imread(i)
        rec = (region["x"], region["y"], region["w"], region["h"])
        x = rec[0]
        y = rec[1] - 10
        pos = (x, y)
        rec_image = cv2.rectangle(pth, rec, (0, 255, 0), thickness=4)
        rec_image = cv2.putText(
            rec_image,
            text_of_rec[idx],
            pos,
            cv2.FONT_HERSHEY_SIMPLEX,
            2,
            (36, 255, 12),
            3,
        )
        rec_image_list.append(rec_image)
    return rec_image_list


def add_emotion_on_frame_new(df):

    len_of_df = len(df)
    rec_image_list = []

    for i in range(len_of_df):
        info = df.loc[i, :]
        string = info['emotion']
        pth = cv2.imread(info['frame'])
        rec = (info['x'], info['y'], info['w'], info['h'])
        x = rec[0]
        y = rec[1]
        pos = (x, y-10)
        rec_image = cv2.rectangle(pth, rec, (0, 255, 0), thickness=4)
        rec_image = cv2.putText(
            rec_image,
            string,
            pos,
            cv2.FONT_HERSHEY_SIMPLEX,
            2,
            (36, 255, 12),
            3,
        )

        rec_image_list.append(rec_image)

    return rec_image_list


def frame_to_video(rec_image_list, video_path):
    cap = cv2.VideoCapture(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    # fps = mmcv.VideoReader(video_path).fps

    fourcc = cv2.VideoWriter_fourcc(*"vp80")
    
    vid_save_name = f"./{video_path.split('/')[1]}/{video_path.split('/')[2]}/face_{video_path.split('/')[-1]}"
    out = cv2.VideoWriter(vid_save_name, fourcc, fps, (width, height))
    # out = cv2.VideoWriter(vid_save_name, fourcc, fps/2, (width, height))
    for rec_frame in rec_image_list:
        out.write(rec_frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()

    return vid_save_name

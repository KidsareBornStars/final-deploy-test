# Copyright (c) OpenMMLab. All rights reserved.
import os
import warnings
from datetime import datetime
from argparse import ArgumentParser

import cv2
import mmcv
import numpy as np
from mmpose.apis import inference_top_down_pose_model, init_pose_model, vis_pose_result
from mmpose.datasets import DatasetInfo


def calculate_angle(a, b):
    a = np.array(a)
    b = np.array(b)

    radians = np.arctan2(b[1] - a[1], b[0] - a[0])
    angle = np.abs(radians * 180.0 / np.pi)

    return angle

VIDEO_PATH = 'configs/heyi/mobilenetv2_aihub_256x192.py'
SAVED_DIR = 'https://download.openmmlab.com/mmpose/top_down/mobilenetv2/mobilenetv2_coco_256x192-d1e58e7b_20200727.pth'

def main(VIDEO_PATH,SAVED_DIR):
    """Visualize the demo images.

    Using mmdet to detect the human.
    """
    parser = ArgumentParser()
    parser.add_argument("pose_config", default= 'configs/heyi/mobilenetv2_aihub_256x192.py',
help="Config file for pose")
    parser.add_argument("pose_checkpoint", default='https://download.openmmlab.com/mmpose/top_down/mobilenetv2/mobilenetv2_coco_256x192-d1e58e7b_20200727.pth',
help="Checkpoint file for pose")
    parser.add_argument("--video-path", default=VIDEO_PATH, type=str, help="Video path")
    parser.add_argument(
        "--show",
        action="store_true",
        default=False,
        help="whether to show visualizations.",
    )
    parser.add_argument(
        "--out-video-root",
        default=SAVED_DIR,
        help="Root of the output video file. "
        "Default not saving the visualization video.",
    )
    parser.add_argument("--device", default="cuda:0", help="Device used for inference")
    parser.add_argument(
        "--kpt-thr", type=float, default=0.3, help="Keypoint score threshold"
    )
    parser.add_argument(
        "--radius", type=int, default=4, help="Keypoint radius for visualization"
    )
    parser.add_argument(
        "--thickness", type=int, default=1, help="Link thickness for visualization"
    )

    args = parser.parse_args()

    assert args.show or (args.out_video_root != "")
    print("Initializing model...")
    # build the pose model from a config file and a checkpoint file
    pose_model = init_pose_model(
        args.pose_config, args.pose_checkpoint, device=args.device.lower()
    )

    dataset = pose_model.cfg.data["test"]["type"]
    dataset_info = pose_model.cfg.data["test"].get("dataset_info", None)
    if dataset_info is None:
        warnings.warn(
            "Please set `dataset_info` in the config."
            "Check https://github.com/open-mmlab/mmpose/pull/663 for details.",
            DeprecationWarning,
        )
    else:
        dataset_info = DatasetInfo(dataset_info)

    # read video
    video = mmcv.VideoReader(args.video_path)
    assert video.opened, f"Faild to load video file {args.video_path}"

    fps = video.fps
    size = (video.width, video.height)

    if args.out_video_root == "":
        save_out_video = False
    else:
        os.makedirs(args.out_video_root, exist_ok=True)
        save_out_video = True

    if save_out_video:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        videoWriter = cv2.VideoWriter(
            os.path.join(
                args.out_video_root, f"vis_{os.path.basename(args.video_path)}"
            ),
            fourcc,
            fps,
            size,
        )

    # whether to return heatmap, optional
    return_heatmap = False

    # return the output of some desired layers,
    # e.g. use ('backbone', ) to return backbone feature
    output_layer_names = None

    times = {"shoulder": {}, "hand": {}}

    print("Running inference...")
    start_time = datetime.now()

    for frame_id, cur_frame in enumerate(mmcv.track_iter_progress(video)):
        # keep the person class bounding boxes.
        person_results = [{"bbox": np.array([0, 0, size[0], size[1]])}]

        # test a single image, with a list of bboxes.
        pose_results, returned_outputs = inference_top_down_pose_model(
            pose_model,
            cur_frame,
            person_results,
            format="xyxy",
            dataset=dataset,
            dataset_info=dataset_info,
            return_heatmap=return_heatmap,
            outputs=output_layer_names,
        )
        keypoints = pose_results[0]["keypoints"]
        current_time = datetime.now()
        elapsed_time = f"{(current_time - start_time).total_seconds():.3f}초"

        left_shoulder = keypoints[5][:2]
        right_shoulder = keypoints[6][:2]
        left_wrist = keypoints[9][:2]
        right_wrist = keypoints[10][:2]

        angle = f"{calculate_angle(left_shoulder, right_shoulder):.3f}도"
        times["shoulder"][elapsed_time] = angle
        if left_wrist.any() or right_wrist.any():
            times["hand"][elapsed_time] = True

        # show the results
        vis_frame = vis_pose_result(
            pose_model,
            cur_frame,
            pose_results,
            radius=args.radius,
            thickness=args.thickness,
            dataset=dataset,
            dataset_info=dataset_info,
            kpt_score_thr=args.kpt_thr,
            show=False,
        )

        if args.show:
            cv2.imshow("Frame", vis_frame)

        if save_out_video:
            videoWriter.write(vis_frame)

        if args.show and cv2.waitKey(1) & 0xFF == ord("q"):
            break

    if save_out_video:
        videoWriter.release()
    if args.show:
        cv2.destroyAllWindows()

    shoulder_times = times["shoulder"]
    hand_times = times["hand"]

    return shoulder_times, hand_times


if __name__ == "__main__":
    times = main(VIDEO_PATH,SAVED_DIR)
    print(times)

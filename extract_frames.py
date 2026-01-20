import cv2
import os

def extract_multi_frames(video_path, output_dir, intervals_sec):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    for sec in intervals_sec:
        frame_idx = int(sec * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(os.path.join(output_dir, f"frame_{sec}s.png"), frame)
    cap.release()

if __name__ == "__main__":
    os.makedirs("debug_frames", exist_ok=True)
    extract_multi_frames(
        "/home/tuilahiu/Desktop/Yep-project/video/yep_pickleball_trimmed.mp4",
        "/home/tuilahiu/Desktop/Yep-project/debug_frames",
        [0, 10, 20, 30, 40, 50]
    )

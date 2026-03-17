import cv2
import time

def capture_one_frame(camera_index: int = 0, warmup_frames: int = 10):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"Camera open failed: index={camera_index}")
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 800)

    frame = None
    for _ in range(max(1, warmup_frames)):
        ok, fr = cap.read()
        if ok:
            frame = fr
        time.sleep(0.01)

    cap.release()

    if frame is None:
        raise RuntimeError("Failed to capture frame.")
    

    return frame

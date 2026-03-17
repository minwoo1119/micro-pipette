import os
import cv2

from worker.camera import capture_one_frame

OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "state",
    "last_frame.jpg"
)

def capture_one_frame_to_disk(camera_index=0):
    frame = capture_one_frame(camera_index)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    cv2.imwrite(OUTPUT_PATH, frame)
    print(f"[worker] frame saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    capture_one_frame_to_disk()

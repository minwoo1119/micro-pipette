import random
import os
import cv2
from datetime import datetime
from worker.camera import capture_one_frame

SNAPSHOT_DIR = "snapshots"

def ensure_dirs():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    os.makedirs("logs", exist_ok=True)

def generate_random_target():
    """
    0.500 ~ 5.000 ml (500 ~ 5000 uL)
    """
    value_ml = round(random.uniform(0.5, 5.0), 3)
    return int(value_ml * 1000), value_ml

def take_snapshot(order: int, value_ml: float):
    frame = capture_one_frame(0)
    fname = f"{order:04d}_{value_ml:.3f}.jpg"
    path = os.path.join(SNAPSHOT_DIR, fname)
    cv2.imwrite(path, frame)
    return path

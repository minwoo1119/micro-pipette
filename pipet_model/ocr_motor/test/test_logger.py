import csv
from datetime import datetime

LOG_PATH = "logs/batch_test_log.csv"

def init_log():
    with open(LOG_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "order",
            "target_ul",
            "target_ml",
            "final_ocr_ul",
            "success",
            "elapsed_sec",
            "timestamp"
        ])

def append_log(order, target_ul, target_ml, final_ul, success, elapsed):
    with open(LOG_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            order,
            target_ul,
            target_ml,
            final_ul,
            success,
            round(elapsed, 2),
            datetime.now().isoformat()
        ])

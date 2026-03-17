import json
import os

from PyQt5.QtWidgets import (
    QGroupBox, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit
)
from PyQt5.QtGui import QPixmap, QPainter, QPen
from PyQt5.QtCore import Qt


class YoloPanel(QGroupBox):
    def __init__(self, controller, video_panel):
        super().__init__("YOLO ROI Detection (4 boxes)")

        self.controller = controller
        self.video_panel = video_panel

        self.btn_detect = QPushButton("Detect ROIs")
        self.btn_reset  = QPushButton("Re-Detect (reset)")

        self.btn_detect.clicked.connect(self.on_detect)
        self.btn_reset.clicked.connect(self.on_reset)

        self.roi_text = QTextEdit()
        self.roi_text.setReadOnly(True)
        self.roi_text.setFixedHeight(120)

        top = QHBoxLayout()
        top.addWidget(self.btn_detect)
        top.addWidget(self.btn_reset)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(QLabel("Detected ROIs (x,y,w,h):"))
        layout.addWidget(self.roi_text)
        self.setLayout(layout)

    def _run(self, reset: bool):
        cam = int(self.video_panel.camera_spin.value())
        res = self.controller.yolo_detect(reset=reset, camera_index=cam)

        if not res.ok:
            self.roi_text.setPlainText("YOLO failed.\nCheck terminal logs.")
            return

        raw_rois = res.data.get("rois", [])
        fixed_rois = self.normalize_vertical_rois(raw_rois, expected_count=4)

        self.roi_text.setPlainText(
            json.dumps(
                {"raw": raw_rois, "fixed": fixed_rois},
                indent=2,
                ensure_ascii=False
            )
        )

        frame_path = res.data.get("frame_path")
        if frame_path and os.path.exists(frame_path):
            self.show_fixed_rois(frame_path, fixed_rois)

    def on_detect(self):
        print("[GUI] YOLO detect button clicked")
        self._run(reset=False)

    def on_reset(self):
        self._run(reset=True)

    @staticmethod
    def normalize_vertical_rois(rois, expected_count=4):
        """
        return format:
        [
        [x, y, size, size],
        [x, y + gap, size, size],
        [x, y + 2*gap, size, size],
        [x, y + 3*gap, size, size],
        ]
        """

        if len(rois) < expected_count:
            return rois
        
        centers = []
        heights = []

        for x, y, w, h in rois:
            centers.append((x + w / 2, y + h / 2))
            heights.append(h)

        size = int(sum(heights) / len(heights))

        avg_cx = sum(cx for cx, _ in centers) / len(centers)
        fixed_x = int(avg_cx - size / 2)
        centers.sort(key=lambda c: c[1])
        gaps = [
            centers[i + 1][1] - centers[i][1]
            for i in range(len(centers) - 1)
        ]
        avg_gap = sum(gaps) / len(gaps)
        start_y = int(centers[0][1] - size / 2)

        normalized = []
        for i in range(expected_count):
            y = int(start_y + i * avg_gap)
            normalized.append([fixed_x, y, size, size]) 
        return normalized



    def show_fixed_rois(self, image_path, fixed_rois):
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print("[WARN] Failed to load image:", image_path)
            return

        painter = QPainter(pixmap)
        pen = QPen(Qt.green)
        pen.setWidth(2)
        painter.setPen(pen)

        for idx, (x, y, w, h) in enumerate(fixed_rois):
            painter.drawRect(x, y, w, h)
            painter.drawText(x, y - 4, f"ROI {idx}")

        painter.end()

        self.video_panel.show_pixmap(pixmap)

from PyQt5.QtWidgets import (
    QGroupBox, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QSpinBox
)
from worker.paths import FRAME_JPG_PATH
import os
from PyQt5.QtGui import QPixmap


class TargetPanel(QGroupBox):
    def __init__(self, controller):
        super().__init__("Target Control (OCR(TRT) + Motor)")

        self.controller = controller

        self.target_spin = QSpinBox()
        self.target_spin.setRange(0, 9999)
        self.target_spin.setValue(0)

        self.btn_read = QPushButton("Read Current Volume (OCR)")
        self.btn_start = QPushButton("Run To Target")
        self.btn_stop = QPushButton("Stop Run")

        self.status = QLabel("Status: Idle")
        self.status.setWordWrap(True)

        self.btn_read.clicked.connect(self.on_read)
        self.btn_start.clicked.connect(self.on_start)
        self.btn_stop.clicked.connect(self.on_stop)

        top = QHBoxLayout()
        top.addWidget(QLabel("Target Volume:"))
        top.addWidget(self.target_spin)
        top.addStretch(1)
        top.addWidget(self.btn_read)
        top.addWidget(self.btn_start)
        top.addWidget(self.btn_stop)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.status)
        self.setLayout(layout)

    def on_read(self):
        res = self.controller.ocr_read_volume(camera_index=0)
        if not res.ok:
            self.status.setText("Status: OCR failed.")
            return

        v = int(res.data.get("volume", -1))
        self.status.setText(f"Status: OCR OK, current={v:04d}")


    def on_start(self):
        t = int(self.target_spin.value())
        self.status.setText(f"Status: Running to target {t:04d} (see terminal logs)...")
        self.controller.start_run_to_target(target=t, camera_index=0)

    def on_stop(self):
        self.controller.stop_run_to_target()
        self.status.setText("Status: Stopped.")

    def update_camera_frame(self):
        if not os.path.exists(FRAME_JPG_PATH):
            return

        pixmap = QPixmap(FRAME_JPG_PATH)
        self.camera_label.setPixmap(pixmap)
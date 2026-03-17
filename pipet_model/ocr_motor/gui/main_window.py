from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from gui.controller import Controller
from gui.panels.video_panel import VideoPanel
from gui.panels.yolo_panel import YoloPanel
from gui.panels.target_panel import TargetPanel
from gui.panels.pipette_panel import PipettePanel
from gui.panels.run_status_panel import RunStatusPanel


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Pipette Integrated Control (GUI = single serial session)"
        )
        self.resize(1100, 1050)

        # Controller만 생성 (정상)
        self.controller = Controller(conda_env="pipet_env")

        # ---------- Panels ----------
        self.video_panel = VideoPanel(self.controller)
        self.controller.set_video_panel(self.video_panel)
        self.yolo_panel = YoloPanel(self.controller, self.video_panel)
        self.target_panel = TargetPanel(self.controller)
        self.run_status_panel = RunStatusPanel(self.controller)
        self.pipette_panel = PipettePanel(self.controller)

        # ---------- Right side ----------
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.yolo_panel)
        right_layout.addWidget(self.target_panel)
        right_layout.addWidget(self.run_status_panel)
        right_layout.addWidget(self.pipette_panel)
        right_layout.addStretch(1)

        # ---------- Main layout ----------
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.video_panel)
        main_layout.addLayout(right_layout)

        main_layout.setStretch(0, 3)
        main_layout.setStretch(1, 2)

        self.setLayout(main_layout)

    def closeEvent(self, event):
        """GUI 종료 시 컨트롤러 정리"""
        try:
            self.controller.close()
        except Exception:
            pass
        event.accept()

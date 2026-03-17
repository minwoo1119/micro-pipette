from PyQt5.QtWidgets import (
    QGroupBox, QTextEdit, QVBoxLayout
)
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import Qt
from datetime import datetime


class RunStatusPanel(QGroupBox):
    def __init__(self, controller):
        super().__init__("Run-To-Target Log")

        self.controller = controller

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setLineWrapMode(QTextEdit.NoWrap)

        layout = QVBoxLayout()
        layout.addWidget(self.log)
        self.setLayout(layout)

        if hasattr(controller, "run_state_updated"):
            controller.run_state_updated.connect(self.on_state_updated)

    def on_state_updated(self, s: dict):
        """
        매 step마다 append 되는 로그
        """
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        line = (
            f"[{ts}] "
            f"step={s.get('step')} "
            f"cur={s.get('current')} "
            f"target={s.get('target')} "
            f"err={s.get('error')} "
            f"dir={s.get('direction')} "
            f"duty={s.get('duty')} "
            f"status={s.get('status')}"
        )

        self.log.append(line)
        self.log.moveCursor(QTextCursor.End)


import json
import time
import os
import subprocess
import threading
from dataclasses import dataclass
from typing import Any, Dict, Optional, List

from PyQt5.QtCore import QObject, pyqtSignal

from worker.serial_controller import SerialController
from worker.actuator_linear import LinearActuator
from worker.actuator_volume_dc import VolumeDCActuator
from worker.paths import FRAME_JPG_PATH


@dataclass
class WorkerResult:
    ok: bool
    data: Dict[str, Any]
    raw: str


class Controller(QObject):
    run_state_updated = pyqtSignal(dict)

    def __init__(self, conda_env: str = "pipet_env"):
        super().__init__()

        self.conda_env = conda_env
        self.root_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )

        self.long_proc: Optional[subprocess.Popen] = None

        self.video_panel = None

        self.serial = SerialController("/dev/ttyUSB0")
        self.serial.connect()

        self.pipetting_linear = LinearActuator(self.serial, 0x0B)
        self.volume_linear = LinearActuator(self.serial, 0x0A)
        self.volume_dc = VolumeDCActuator(self.serial, 0x0C)

        for aid in (0x0B, 0x0A):
            self.serial.send_mightyzap_force_onoff(aid, 1)
            time.sleep(0.1)
            self.serial.send_mightyzap_set_speed(aid, 500)
            time.sleep(0.1)
            self.serial.send_mightyzap_set_current(aid, 300)
            time.sleep(0.1)
            self.serial.send_mightyzap_set_position(aid, 300)
            time.sleep(0.1)

        self.run_state: Dict[str, Any] = {
            "running": False,
            "step": 0,
            "current": 0,
            "target": 0,
            "error": 0,
            "direction": None,
            "duty": 0,
            "status": "Idle",
        }

    def set_video_panel(self, panel):
        self.video_panel = panel

    def refresh_camera_view(self):
        if self.video_panel and os.path.exists(FRAME_JPG_PATH):
            self.video_panel.show_image(FRAME_JPG_PATH)

    def _run_worker(self, args: List[str], timeout: Optional[int] = 120) -> WorkerResult:
        cmd = [
            "conda", "run", "-n", self.conda_env,
            "python", "-u", "-m", "worker.worker",
        ] + args

        p = subprocess.run(
            cmd,
            cwd=self.root_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )

        raw = (p.stdout or "").strip()

        if p.returncode != 0:
            return WorkerResult(False, {}, raw)

        try:
            data = json.loads(raw.splitlines()[-1])
            return WorkerResult(bool(data.get("ok", True)), data, raw)
        except Exception:
            return WorkerResult(False, {}, raw)

    def capture_frame(self, camera_index: int = 0) -> WorkerResult:
        res = self._run_worker(["--capture", f"--camera={camera_index}"], 60)
        if res.ok:
            self.refresh_camera_view()
        return res

    def yolo_detect(self, reset: bool = False, camera_index: int = 0) -> WorkerResult:
        args = ["--yolo", f"--camera={camera_index}"]
        if reset:
            args.append("--reset-rois")
        res = self._run_worker(args, 120)
        if res.ok:
            self.refresh_camera_view()
        return res

    def ocr_read_volume(self, camera_index: int = 0) -> WorkerResult:
        res = self._run_worker(["--ocr", f"--camera={camera_index}"], 120)
        if res.ok:
            self.refresh_camera_view()
        return res

    def start_run_to_target(self, target: int, camera_index: int = 0) -> None:
        self.stop_run_to_target()

        # 초기 상태 emit (패널 즉시 갱신)
        self.run_state.update({
            "running": True,
            "step": 0,
            "current": 0,
            "target": target,
            "error": 0,
            "direction": None,
            "duty": 0,
            "status": "Running",
        })
        self.run_state_updated.emit(dict(self.run_state))

        cmd = [
            "conda", "run", "-n", self.conda_env,
            "python", "-u", "-m", "worker.worker",
            "--run-target",
            f"--target={target}",
            f"--camera={camera_index}",
        ]

        self.long_proc = subprocess.Popen(
            cmd,
            cwd=self.root_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        threading.Thread(target=self._run_to_target_stdout_loop, daemon=True).start()
        threading.Thread(target=self._run_to_target_stderr_loop, daemon=True).start()

    def _run_to_target_stdout_loop(self):
        proc = self.long_proc
        if not proc or not proc.stdout:
            return

        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue

            try:
                msg = json.loads(line)
            except Exception:
                # 혹시 stdout에 섞이면 여기 찍히게 됨
                print("[WORKER][STDOUT-NONJSON]", line)
                continue

            cmd = msg.get("cmd")

            if cmd == "volume":
                # 상태 갱신 + emit
                self.run_state.update({
                    "running": True,
                    "step": msg.get("step", 0),
                    "current": msg.get("current", 0),
                    "target": msg.get("target", self.run_state["target"]),
                    "error": msg.get("error", 0),
                    "direction": msg.get("direction", None),
                    "duty": msg.get("duty", 0),
                    "status": "Running",
                })
                self.run_state_updated.emit(dict(self.run_state))

                # 모터 제어
                direction = int(msg["direction"])
                duty = int(msg["duty"])
                duration_ms = int(msg["duration_ms"])

                self.volume_dc.run(direction=direction, duty=duty)
                time.sleep(duration_ms / 1000.0)
                self.volume_dc.stop()

            elif cmd == "done":
                self.run_state.update({
                    "running": False,
                    "step": msg.get("step", self.run_state["step"]),
                    "current": msg.get("current", self.run_state["current"]),
                    "target": msg.get("target", self.run_state["target"]),
                    "error": msg.get("error", 0),
                    "status": "Done",
                })
                self.run_state_updated.emit(dict(self.run_state))
                break

            elif cmd == "warn":
                self.run_state.update({
                    "running": False,
                    "status": "Max iteration reached",
                })
                self.run_state_updated.emit(dict(self.run_state))
                break

        # 프로세스 종료 처리
        self.run_state["running"] = False
        self.run_state_updated.emit(dict(self.run_state))

    def _run_to_target_stderr_loop(self):
        proc = self.long_proc
        if not proc or not proc.stderr:
            return

        # stderr는 사람이 보는 로그
        for line in proc.stderr:
            line = line.rstrip()
            if not line:
                continue
            print("[WORKER][STDERR]", line)

        if self.long_proc and self.long_proc.poll() is not None:
            rc = self.long_proc.returncode
            if self.run_state.get("status") == "Running" and self.run_state.get("step", 0) == 0:
                self.run_state.update({
                    "running": False,
                    "status": f"Worker exited (rc={rc})",
                })
                self.run_state_updated.emit(dict(self.run_state))

    def stop_run_to_target(self) -> None:
        if self.long_proc and self.long_proc.poll() is None:
            try:
                self.long_proc.terminate()
            except Exception:
                pass

        try:
            self.volume_dc.stop()
        except Exception:
            pass

        self.run_state.update({
            "running": False,
            "status": "Stopped",
        })
        self.run_state_updated.emit(dict(self.run_state))

        self.long_proc = None

    def close(self):
        try:
            self.volume_dc.stop()
        except Exception:
            pass
        self.serial.close()

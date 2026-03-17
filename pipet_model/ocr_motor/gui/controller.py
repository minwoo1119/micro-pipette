"""GUI에서 worker 호출과 실제 시리얼 제어를 함께 조정하는 핵심 컨트롤러."""

import json
import time
import os
import re
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
    """패널별 처리 방식을 단순화하기 위해 worker 결과를 공통 형태로 묶은 객체."""
    ok: bool
    data: Dict[str, Any]
    raw: str


class Controller(QObject):
    """각 패널과 worker, 시리얼 제어 계층 사이를 연결하는 중심 계층."""

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

        self._init_linear_actuators()

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

    def _init_linear_actuators(self):
        """GUI가 시리얼을 다시 잡았을 때 기본 선형 액추에이터 설정을 복원한다."""
        for aid in (0x0B, 0x0A):
            self.serial.send_mightyzap_force_onoff(aid, 1)
            time.sleep(0.1)
            self.serial.send_mightyzap_set_speed(aid, 500)
            time.sleep(0.1)
            self.serial.send_mightyzap_set_current(aid, 300)
            time.sleep(0.1)
            self.serial.send_mightyzap_set_position(aid, 300)
            time.sleep(0.1)

    def _release_gui_serial(self):
        """외부 테스트 스크립트가 포트를 직접 사용할 수 있도록 GUI 시리얼을 해제한다."""
        try:
            self.volume_dc.stop()
        except Exception:
            pass
        self.serial.close()

    def _reconnect_gui_serial(self):
        """외부 스크립트 종료 후 GUI가 다시 시리얼을 잡고 초기 상태를 복원한다."""
        ser = getattr(self.serial, "ser", None)
        if ser is not None and getattr(ser, "is_open", False):
            return

        self.serial.connect()
        self._init_linear_actuators()

    def set_video_panel(self, panel):
        """worker 결과 이미지가 생길 때 preview를 갱신할 수 있도록 패널 참조를 저장한다."""
        self.video_panel = panel

    def refresh_camera_view(self):
        """state 디렉터리의 최신 프레임을 preview 패널에 다시 반영한다."""
        if self.video_panel and os.path.exists(FRAME_JPG_PATH):
            self.video_panel.show_image(FRAME_JPG_PATH)

    def _run_worker(self, args: List[str], timeout: Optional[int] = 120) -> WorkerResult:
        """단발성 worker 작업을 실행할 때 공통으로 사용하는 내부 헬퍼다."""
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
        """프레임 1장 캡처 요청을 worker에 위임하고 성공 시 화면을 갱신한다."""
        res = self._run_worker(["--capture", f"--camera={camera_index}"], 60)
        if res.ok:
            self.refresh_camera_view()
        return res

    def yolo_detect(self, reset: bool = False, camera_index: int = 0) -> WorkerResult:
        """ROI 검출을 worker에 맡기고 성공하면 결과 이미지를 다시 보여준다."""
        args = ["--yolo", f"--camera={camera_index}"]
        if reset:
            args.append("--reset-rois")
        res = self._run_worker(args, 120)
        if res.ok:
            self.refresh_camera_view()
        return res

    def ocr_read_volume(self, camera_index: int = 0) -> WorkerResult:
        """현재 용량 읽기를 worker에 맡기고, 호출 후 최신 프레임을 화면에 반영한다."""
        res = self._run_worker(["--ocr", f"--camera={camera_index}"], 120)
        if res.ok:
            self.refresh_camera_view()
            if self.video_panel and "volume" in res.data:
                self.video_panel.set_latest_volume(int(res.data["volume"]))
        return res

    def linear_move(self, actuator_id: int, position: int):
        """입력값 기반 수동 이동 기능에서 사용하는 범용 리니어 이동 메서드다."""
        if actuator_id == 0x0A:
            return self.volume_linear.move_to(position)
        if actuator_id == 0x0B:
            return self.pipetting_linear.move_to(position)
        raise ValueError(f"Unsupported actuator id: {hex(int(actuator_id))}")

    def start_run_to_target(self, target: int, camera_index: int = 0) -> None:
        """Run To Target 버튼이 Paddle 테스트 스크립트를 실행하도록 연결한 진입점이다."""
        self.stop_run_to_target()

        # worker 첫 메시지를 기다리지 않고도 패널이 즉시 Running 상태를 보이게 한다.
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

        # 이 경로는 테스트 스크립트가 시리얼 포트를 직접 열기 때문에 GUI 쪽 포트를 잠시 내려놓는다.
        self._release_gui_serial()

        cmd = [
            "conda", "run", "-n", self.conda_env,
            "python", "-u", "test/single_target_paddleOCR_test.py",
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
        """Paddle 테스트 스크립트 stdout을 읽어 UI 상태를 가능한 범위까지 갱신한다."""
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
                msg = None

            if isinstance(msg, dict) and "success" in msg:
                self.run_state.update({
                    "running": False,
                    "step": msg.get("steps", self.run_state["step"]),
                    "current": msg.get("final_ul", self.run_state["current"]),
                    "target": msg.get("target_ul", self.run_state["target"]),
                    "error": (
                        msg.get("target_ul", self.run_state["target"])
                        - msg.get("final_ul", self.run_state["current"])
                    ) if msg.get("final_ul") is not None else self.run_state["error"],
                    "status": "Done" if msg.get("success") else msg.get("reason", "Failed"),
                })
                if self.video_panel and msg.get("final_ul") is not None:
                    self.video_panel.set_latest_volume(int(msg["final_ul"]))
                self.run_state_updated.emit(dict(self.run_state))
                continue

            step_match = re.search(r"\[STEP\s+(\d+)\]\s+cur=(\d+)\s+err=(-?\d+)", line)
            if step_match:
                step = int(step_match.group(1))
                cur = int(step_match.group(2))
                err = int(step_match.group(3))
                self.run_state.update({
                    "running": True,
                    "step": step,
                    "current": cur,
                    "error": err,
                    "status": "Running",
                })
                if self.video_panel:
                    self.video_panel.set_latest_volume(cur)
                self.run_state_updated.emit(dict(self.run_state))
                continue

            target_match = re.search(r"\[TEST\]\s+target=(\d+)", line)
            if target_match:
                self.run_state.update({
                    "target": int(target_match.group(1)),
                })
                self.run_state_updated.emit(dict(self.run_state))
                continue

            print("[PADDLE][STDOUT]", line)

        # 프로세스 종료 처리
        self.run_state["running"] = False
        self.run_state_updated.emit(dict(self.run_state))
        try:
            self._reconnect_gui_serial()
        except Exception:
            pass

    def _run_to_target_stderr_loop(self):
        """테스트 스크립트 stderr 로그를 터미널에 그대로 전달한다."""
        proc = self.long_proc
        if not proc or not proc.stderr:
            return

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
                    "status": f"Paddle script exited (rc={rc})",
                })
                self.run_state_updated.emit(dict(self.run_state))

    def stop_run_to_target(self) -> None:
        """중단 요청 시 테스트 스크립트를 종료하고 GUI 시리얼 연결을 복구한다."""
        if self.long_proc and self.long_proc.poll() is None:
            try:
                self.long_proc.terminate()
            except Exception:
                pass

        try:
            self.volume_dc.stop()
        except Exception:
            pass

        try:
            self._reconnect_gui_serial()
        except Exception:
            pass

        self.run_state.update({
            "running": False,
            "status": "Stopped",
        })
        self.run_state_updated.emit(dict(self.run_state))

        self.long_proc = None

    def close(self):
        """프로그램 종료 시 남아 있는 모터/시리얼 자원을 정리하는 마무리 메서드다."""
        try:
            self.volume_dc.stop()
        except Exception:
            pass
        self.serial.close()

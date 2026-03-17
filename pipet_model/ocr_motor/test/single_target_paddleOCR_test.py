import subprocess
import json
import time
import os
import sys
import cv2 

from worker.capture_frame import OUTPUT_PATH
from worker.serial_controller import SerialController
from worker.actuator_volume_dc import VolumeDCActuator

SNAP_DIR = "snapshots_paddle"
CALIB_JSON_PATH = "calibration_paddle.json"

VOLUME_TOLERANCE = 1
SETTLE_TIME = 0.9
MAX_ITER = 60
OCR_TIMEOUT = 40  # PaddleOCR 첫 로딩 느릴 수 있어 넉넉히

VALID_MIN_UL = 500
VALID_MAX_UL = 5000
BOUND_MARGIN = 5

CALIB_TOL = 5
CALIB_MAX_TRY = 6

ROTATE = 1
CAMERA_INDEX = 0

# Paddle 우선 OCR 재시도
PADDLE_RETRIES = 2
PADDLE_RETRY_DELAY = 0.25

_serial = None
_volume_dc = None


def ensure_dirs():
    os.makedirs(SNAP_DIR, exist_ok=True)


def ensure_volume_dc():
    """
    기존에 잘 되던 코드와 동일한 초기화 방식 유지.
    actuator_id=0x0C 를 그대로 사용.
    """
    global _serial, _volume_dc
    if _serial is None:
        _serial = SerialController()
        _serial.connect()
    if _volume_dc is None:
        _volume_dc = VolumeDCActuator(
            serial=_serial,
            actuator_id=0x0C,
        )
    return _volume_dc


def _run_worker_and_parse_ok(cmd, timeout_sec: int) -> int:
    """
    worker subprocess 실행 후 stdout에서 {"ok": true, "volume": ...} JSON을 찾아 반환.
    (ppocr 디버그 로그가 stdout에 섞여도 JSON 라인만 골라 파싱)
    """
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        stdout, stderr = p.communicate(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        p.kill()
        stdout, stderr = p.communicate()
        raise RuntimeError(
            f"worker timeout.\ncmd={cmd}\n[stdout]\n{stdout}\n\n[stderr]\n{stderr}"
        )

    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            if msg.get("ok"):
                return int(msg["volume"])
        except Exception:
            continue

    raise RuntimeError(
        f"worker returned no ok json.\ncmd={cmd}\n[stdout]\n{stdout}\n\n[stderr]\n{stderr}"
    )


def read_ocr_volume_legacy(camera_index=0, rotate=1) -> int:
    """
    기존 custom OCR worker (worker.worker)를 호출.
    """
    cmd = [
        sys.executable, "-m", "worker.worker",
        "--ocr",
        f"--camera={camera_index}",
        f"--rotate={rotate}",
    ]
    return _run_worker_and_parse_ok(cmd, timeout_sec=OCR_TIMEOUT)


def read_ocr_volume_paddle_only(camera_index=0, rotate=1, auto_rois=True, debug_save=False) -> int:
    """
    PaddleOCR worker (worker.worker_paddle)를 호출.
    """
    cmd = [
        sys.executable, "-m", "worker.worker_paddle",
        "--ocr",
        f"--camera={camera_index}",
        f"--rotate={rotate}",
    ]
    if auto_rois:
        cmd.append("--ocr-auto-rois")
    if debug_save:
        cmd.append("--debug-save")

    return _run_worker_and_parse_ok(cmd, timeout_sec=OCR_TIMEOUT)


def read_ocr_volume(camera_index=0, rotate=1, auto_rois=True, debug_save=False,
                    paddle_retries: int = PADDLE_RETRIES,
                    retry_delay: float = PADDLE_RETRY_DELAY) -> int:
    """
    PaddleOCR을 우선 사용하고,
    실패하면 (재시도 후) legacy(custom OCR)로 fallback.
    """
    last_paddle_err = None

    # 1) Paddle 우선 (재시도)
    for attempt in range(1, paddle_retries + 1):
        try:
            return read_ocr_volume_paddle_only(
                camera_index=camera_index,
                rotate=rotate,
                auto_rois=auto_rois,
                debug_save=debug_save,
            )
        except Exception as e:
            last_paddle_err = e
            if attempt < paddle_retries:
                time.sleep(retry_delay)

    # 2) Paddle 실패 → Legacy fallback
    try:
        return read_ocr_volume_legacy(camera_index=camera_index, rotate=rotate)
    except Exception as e2:
        raise RuntimeError(
            "Both PaddleOCR and Legacy OCR failed.\n"
            f"[Paddle last error]\n{last_paddle_err}\n\n"
            f"[Legacy error]\n{e2}"
        )


def move_motor(direction: int, duty: int, duration_ms: int):
    """
    run()에는 duration_ms를 넘기지 않고,
    sleep으로 duration을 맞춘 뒤 stop() 호출
    """
    dc = ensure_volume_dc()
    dc.run(direction=direction, duty=duty)
    time.sleep(duration_ms / 1000.0)
    dc.stop()


def save_calibration(calib: dict):
    to_save = {str(k): v for k, v in calib.items()}
    with open(CALIB_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(to_save, f, indent=2, ensure_ascii=False)
    print(f"[CALIB] saved → {CALIB_JSON_PATH}")


def load_calibration():
    if not os.path.exists(CALIB_JSON_PATH):
        return None

    with open(CALIB_JSON_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    calib = {int(k): v for k, v in raw.items()}
    print(f"[CALIB] loaded ← {CALIB_JSON_PATH}")
    return calib


def calibrate_one_target(
    target_ul: int,
    base_duty: int,
    base_dur: int,
    camera_index: int,
    rotate: int,
):
    print(f"[CALIB] target={target_ul}uL")

    duty = base_duty
    dur = base_dur

    for i in range(CALIB_MAX_TRY):
        before = read_ocr_volume(camera_index, rotate, auto_rois=True, debug_save=False)
        move_motor(1, duty, dur)
        time.sleep(SETTLE_TIME)
        after = read_ocr_volume(camera_index, rotate, auto_rois=True, debug_save=False)

        delta = abs(after - before)

        print(
            f"[CALIB] try={i+1} "
            f"duty={duty} dur={dur}ms delta={delta}"
        )

        if abs(delta - target_ul) <= CALIB_TOL:
            print("[CALIB] accepted")
            return {
                "duty": duty,
                "duration_ms": dur,
                "delta_ul": delta,
            }

        if delta < target_ul:
            dur += 80
        else:
            dur -= 60

        dur = max(80, min(1500, dur))

    raise RuntimeError(f"[CALIB] failed for {target_ul}uL")


def run_calibration(camera_index=0, rotate=1):
    print("=" * 40)
    print("[CALIB] start calibration (one-time) [PaddleOCR→Legacy fallback]")
    print("=" * 40)

    calib = {}

    calib[100] = calibrate_one_target(100, 55, 900, camera_index, rotate)
    calib[50]  = calibrate_one_target(50,  40, 500, camera_index, rotate)
    calib[10]  = calibrate_one_target(10,  30, 150, camera_index, rotate)
    calib[5]   = calibrate_one_target(5,   25, 80,  camera_index, rotate)

    print("[CALIB] DONE")
    for k, v in calib.items():
        print(f"  {k}uL → {v}")

    save_calibration(calib)
    return calib


def single_target_test_paddle(
    target_ul: int,
    calib: dict,
    camera_index: int = 0,
    rotate: int = 1,
):
    print(f"[TEST] target={target_ul}")

    cur = None
    for step in range(MAX_ITER):
        cur = read_ocr_volume(camera_index, rotate, auto_rois=True, debug_save=False)
        err = target_ul - cur

        print(f"[STEP {step}] cur={cur} err={err}")

        if abs(err) <= VOLUME_TOLERANCE:
            return {
                "success": True,
                "final_ul": cur,
                "target_ul": target_ul,
                "steps": step + 1,
            }

        # HARD BOUND
        if cur <= VALID_MIN_UL + BOUND_MARGIN and err < 0:
            print("[BOUND] lower limit reached")
            break
        if cur >= VALID_MAX_UL - BOUND_MARGIN and err > 0:
            print("[BOUND] upper limit reached")
            break

        abs_err = abs(err)
        direction = 0 if err < 0 else 1

        if abs_err >= 110:
            cfg = calib[100]
        elif abs_err >= 60:
            cfg = calib[50]
        elif abs_err >= 12:
            cfg = calib[10]
        else:
            cfg = calib[5]

        move_motor(direction, cfg["duty"], cfg["duration_ms"])
        time.sleep(SETTLE_TIME)

    return {
        "success": False,
        "final_ul": cur,
        "target_ul": target_ul,
        "reason": "max_iter_or_bound",
    }


if __name__ == "__main__":
    ensure_dirs()

    calib = load_calibration()
    if calib is None:
        calib = run_calibration(CAMERA_INDEX, ROTATE)

    # 임의 목표값 테스트
    import random
    tgt = random.randrange(1000, 4501, 5)

    res = single_target_test_paddle(tgt, calib, CAMERA_INDEX, ROTATE)
    print(json.dumps(res, ensure_ascii=False, indent=2))

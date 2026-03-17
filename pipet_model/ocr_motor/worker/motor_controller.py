"""모터 펌웨어를 간단히 수동 테스트할 때 남겨둔 legacy 시리얼 헬퍼입니다."""

import time
import serial

SERIAL_PORT = "/dev/ttyUSB0"
BAUDRATE = 115200

def _connect():
    """모터 컨트롤러와 짧게 쓰는 raw 시리얼 세션을 여는 함수입니다."""
    return serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)

def motor_test(direction, power, duration):
    """수동 모터 테스트 명령을 보내고 지정 시간 후 정지하는 함수입니다."""
    print(f"[MOTOR TEST] {direction=} {power=} {duration=}")

    ser = _connect()
    cmd = f"TEST {direction} {power}\n"
    ser.write(cmd.encode())

    time.sleep(duration)

    ser.write(b"STOP\n")
    ser.close()

def run_to_target(target_value):
    """OCR 피드백 없이 펌웨어 측 legacy target 명령만 전송하는 함수입니다."""
    print(f"[TARGET RUN] target = {target_value}")

    ser = _connect()
    ser.write(f"TARGET {target_value}\n".encode())

    # 실제 운용에서는 여기서 OCR/TRT feedback loop가 들어가야 하는 구조입니다.
    time.sleep(3)

    ser.write(b"STOP\n")
    ser.close()

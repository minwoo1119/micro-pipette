# Micropipette OCR & Motor Control GUI

YOLO 기반 **마이크로피펫 분주량 OCR**, **모터 제어**, **목표 분주량 도달 자동화**를  
GUI 환경에서 통합 제어하기 위한 프로젝트입니다.

본 프로젝트는 **시스템 Python(GUI)** 과 **conda 환경(worker)** 을 분리하여  
CUDA / TensorRT / PyTorch 환경 충돌 없이 안정적으로 동작하도록 설계되었습니다.

---

## 주요 기능

### Camera / Preview
- 카메라 프레임 **1장 단위 캡처**
- 해상도 **1280 × 800 고정**
- GUI에서 현재 캡처 이미지 미리보기 가능

### YOLO 객체 인식
- YOLO 모델로 **분주량 숫자 영역(ROI) 4개 자동 검출**
- ROI 초기 인식 / 재인식 버튼 제공
- 인식 결과 GUI에서 확인 가능

### OCR (TensorRT)
- TensorRT(`.trt`) 기반 EfficientNet OCR
- 현재 분주량 숫자 인식
- 최근 인식된 분주량을 GUI에 표시

### 목표 분주량 도달 (모터 제어)
- 현재 분주량 ↔ 목표 분주량 차이 계산
- 모터 제어로 목표값까지 자동 이동
- 중간 상태 확인 가능

### 모터 동작 테스트
- 방향 / 세기 / 지속시간 직접 입력
- GUI 버튼으로 즉시 테스트 가능

---

## 프로젝트 구조

```
ocr_motor/
├── gui/                    # GUI (system python)
│   ├── main.py
│   ├── main_window.py
│   ├── controller.py
│   └── panels/
│       ├── video_panel.py
│       ├── yolo_panel.py
│       ├── target_panel.py
│       └── motor_test_panel.py
│
├── worker/                 # Worker (conda pipet_env)
│   ├── worker.py
│   ├── camera.py
│   ├── yolo_worker.py
│   ├── ocr_worker.py
│   ├── motor_worker.py
│   ├── paths.py
│   └── __init__.py
│
├── models/
│   ├── ocr/
│   │   └── efficientnet_b0_fp16_dynamic.trt
│   └── yolo/
│       └── best_rotate_yolo.pt
│
├── assets/
│   └── samples/
│
├── requirements.txt
└── README.md
```

---

## 실행 환경

### System Python (GUI)
- Ubuntu 22.04 / 24.04
- Python 3.10+
- PyQt5 (APT 설치 권장)

```bash
sudo apt update
sudo apt install -y python3-pyqt5
```

> **conda 환경에서 PyQt 실행 ❌ (segmentation fault 발생 가능)**  
> GUI는 반드시 **system python** 사용

---

### Conda Environment (Worker)

```bash
conda create -n pipet_env python=3.10 -y
conda activate pipet_env
```

#### 필수 패키지
```bash
pip install torch torchvision ultralytics opencv-python pyserial numpy
pip install tensorrt pycuda
```

---

## 실행 방법

```bash
cd ocr_motor
python3 -m gui.main
```

---

## 설계 철학

- 실시간 스트리밍 대신 **프레임 단위 캡처**
- OCR / YOLO는 필요 시점에만 실행
- TensorRT는 반복 추론 지연 최소화 목적

---

## 최근 변경 사항

```
fix(camera): enforce 1280x800 resolution for worker frame capture

- Set camera resolution explicitly in worker layer
- Ensure YOLO and OCR operate on consistent frame size
- Prevent ROI mismatch caused by implicit OpenCV defaults
```
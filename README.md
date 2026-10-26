# Micro-Pipette Automation System

비전 인식과 로봇 제어를 결합한 **마이크로피펫 자동화 프로젝트**입니다.

카메라 영상에서 마이크로피펫의 현재 용량을 인식하고 목표 용량까지 모터로 자동 보정하는 시스템과, AprilTag를 기준으로 Well Plate의 위치를 추정하여 UR 로봇의 피펫팅 동작을 수행하는 시스템으로 구성되어 있습니다.

## 주요 기능

- YOLO 기반 마이크로피펫 숫자 영역(ROI) 검출
- TensorRT EfficientNet 및 PaddleOCR 기반 용량 판독
- 현재 용량과 목표 용량의 차이를 이용한 자동 보정
- 시리얼 통신 기반 리니어 액추에이터 및 용량 조절 모터 제어
- AprilTag 기반 위치 및 자세 추정
- 카메라와 로봇 툴의 장착각을 고려한 좌표 변환
- 4×6 Well Plate의 목표 웰(A1~D6) 자동 이동
- ROS 2·MoveIt 2 기반 UR 로봇 IK 계산 및 궤적 제어
- PyQt5 및 Tkinter 기반 운영 GUI

## 시스템 구성

이 저장소에는 서로 다른 역할을 담당하는 두 개의 하위 시스템이 포함되어 있습니다.

| 폴더 | 담당자 | 역할 |
|---|---|---|
| `pipet_model` | [이민우](https://github.com/minwoo1119) | 피펫 용량 인식, 목표 용량 자동 보정, 액추에이터 제어 및 PyQt5 GUI |
| `pipette_robot` | [정성윤](https://github.com/jsy0605) | AprilTag 비전, Well Plate 좌표 계산, UR 로봇 이동 및 피펫팅 시퀀스 |

현재 코드 기준으로 두 하위 시스템은 각각 별도의 GUI와 실행 환경을 사용합니다.

### 1. 피펫 용량 인식 및 보정

```text
Camera
   ↓
Frame Capture
   ↓
YOLO ROI Detection
   ↓
TensorRT OCR / PaddleOCR
   ↓
Current Volume
   ↓
Target Error Calculation
   ↓
Serial Motor Control
   ↓
Target Volume Adjustment
```

`pipet_model`은 카메라로 피펫의 용량 표시부를 촬영하고, YOLO로 숫자 ROI를 검출한 뒤 OCR로 현재 용량을 판독합니다. 판독값과 목표값의 차이에 따라 용량 조절 모터를 구동하며, 피펫팅·팁 교체용 리니어 액추에이터도 함께 제어합니다.

GUI와 추론 환경의 충돌을 줄이기 위해 다음과 같이 실행 환경을 분리합니다.

- 시스템 Python: PyQt5 GUI 및 시리얼 연결
- Conda `pipet_env`: YOLO, OCR, TensorRT 및 worker 프로세스

### 2. UR 로봇 피펫팅 자동화

```text
Alvium Camera
   ↓
AprilTag Detection / Pose Estimation
   ↓
Tag Centering and Coordinate Transform
   ↓
Well Position Calculation
   ↓
MoveIt 2 IK
   ↓
UR Robot Trajectory
   ↓
Pipetting Sequence
```

`pipette_robot`은 Alvium 카메라에서 AprilTag를 검출하고 태그 기준 좌표를 계산합니다. 카메라와 툴의 장착각을 보정한 뒤 4×6 Well Plate의 목표 웰로 UR 로봇을 이동시키며, 오프셋 이동·Z축 하강·상승·복귀로 구성된 피펫팅 시퀀스를 수행합니다.

## 프로젝트 구조

```text
micro-pipette/
├── pipet_model/                         # 이민우
│   ├── 설명서.md                        # 모델·모터 시스템 인수인계 문서
│   └── ocr_motor/
│       ├── gui/                         # PyQt5 운영 GUI
│       │   ├── main.py
│       │   ├── main_window.py
│       │   ├── controller.py
│       │   └── panels/
│       ├── worker/                      # 비전 추론 및 모터 제어 worker
│       │   ├── worker.py
│       │   ├── yolo_worker.py
│       │   ├── ocr_trt.py
│       │   ├── ocr_paddle.py
│       │   ├── control_worker.py
│       │   ├── serial_controller.py
│       │   └── motor_controller.py
│       ├── test/                        # OCR·캘리브레이션 테스트
│       ├── models/                      # YOLO·OCR 모델 및 TensorRT 엔진
│       ├── state/                       # 최근 프레임, ROI 및 검출 결과
│       ├── requirements_gui.txt
│       ├── requirements_worker.txt
│       └── README.md
│
├── pipette_robot/                       # 정성윤
│   ├── 설명서.md                        # 로봇 시스템 인수인계 문서
│   └── pipetting_system/
│       ├── main.py                      # Tkinter GUI 진입점
│       ├── automation_controller.py     # 자동화 및 피펫팅 시퀀스
│       ├── robot_interface.py           # ROS 2·MoveIt 2 로봇 인터페이스
│       ├── vision_module.py             # AprilTag 검출 및 포즈 추정
│       ├── alvium_driver.py             # Alvium 카메라 드라이버
│       └── config.py                    # 로봇·플레이트·제어 파라미터
│
└── README.md
```

## 기술 스택

### 피펫 용량 인식 및 모터 제어

- Python 3.10+
- PyQt5
- PyTorch
- Ultralytics YOLO
- EfficientNet
- TensorRT / PyCUDA
- PaddleOCR
- OpenCV
- PySerial

### 로봇 피펫팅 자동화

- Python
- ROS 2 Jazzy
- MoveIt 2
- Universal Robots ROS 2 Driver
- OpenCV
- pupil-apriltags
- SciPy / NumPy
- Tkinter
- Allied Vision `vmbpy`

## 하드웨어 구성

- 마이크로피펫 및 용량 조절 모터
- 피펫팅·팁 교체용 리니어 액추에이터
- USB 카메라
- Universal Robots 로봇(현재 설정 예시: UR5e)
- Allied Vision Alvium 1800 U-511c 카메라
- `tag36h11` AprilTag
- 4×6 Well Plate

## 실행 환경

두 하위 시스템의 의존성과 GUI 구성이 다르므로 각각 별도로 환경을 준비합니다.

### 피펫 용량 인식 및 모터 제어

기준 환경은 Ubuntu 22.04 또는 24.04입니다. GUI는 시스템 Python으로, 추론 worker는 Conda 환경으로 실행합니다.

#### 1. GUI 환경

```bash
sudo apt update
sudo apt install -y python3-pyqt5
```

#### 2. Worker 환경

```bash
conda create -n pipet_env python=3.10 -y
conda activate pipet_env
pip install -r pipet_model/ocr_motor/requirements_worker.txt
```

#### 3. GUI 실행

저장소 루트에서 다음 명령을 실행합니다.

```bash
cd pipet_model/ocr_motor
python3 -m gui.main
```

기본 시리얼 포트는 `/dev/ttyUSB0`, baud rate는 `115200`, 카메라 인덱스는 `0`으로 설정되어 있습니다. 실제 장비 연결 환경이 다르면 관련 설정을 변경해야 합니다.

> TensorRT 엔진은 생성한 GPU 및 TensorRT 환경에 영향을 받을 수 있습니다. 엔진이 현재 장치와 호환되지 않으면 저장된 ONNX 또는 PyTorch 모델을 이용해 해당 환경에서 다시 빌드해야 합니다.

### UR 로봇 피펫팅 자동화

Ubuntu와 ROS 2 Jazzy 환경을 기준으로 하며, UR Driver와 MoveIt 2가 먼저 실행되어야 합니다.

Python 패키지의 최소 설치 예시는 다음과 같습니다.

```bash
pip install numpy scipy opencv-python pillow pupil-apriltags
```

Alvium 카메라를 사용하려면 Allied Vision SDK와 `vmbpy`를 별도로 설치하고 장치 권한을 설정해야 합니다.

#### 터미널 1: UR Driver

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch ur_robot_driver ur_control.launch.py \
  ur_type:=ur5e \
  robot_ip:=192.168.64.106 \
  launch_rviz:=false
```

#### 터미널 2: MoveIt 2

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch ur_moveit_config ur_moveit.launch.py \
  ur_type:=ur5e \
  launch_rviz:=true \
  publish_robot_description_semantic:=true
```

#### 터미널 3: GUI

```bash
source /opt/ros/jazzy/setup.bash
cd pipette_robot/pipetting_system
python3 main.py
```

`robot_ip`과 `ur_type`은 실제 장비 환경에 맞게 변경해야 합니다.

## 주요 설정

### 피펫 용량 인식 시스템

- 카메라 및 worker 호출: `pipet_model/ocr_motor/gui/controller.py`
- YOLO 모델과 ROI 처리: `pipet_model/ocr_motor/worker/yolo_worker.py`
- TensorRT OCR: `pipet_model/ocr_motor/worker/ocr_trt.py`
- 목표 용량 제어: `pipet_model/ocr_motor/worker/control_worker.py`
- 시리얼 통신: `pipet_model/ocr_motor/worker/serial_controller.py`

### 로봇 시스템

로봇, 카메라, AprilTag, Well Plate 및 피펫 오프셋 관련 값은 `pipette_robot/pipetting_system/config.py`에서 관리합니다.

주요 튜닝 항목은 다음과 같습니다.

- UR 로봇의 base 및 tool frame
- 카메라·툴 장착각
- AprilTag 크기와 회전 오프셋
- Well 간격 및 태그에서 기준 웰까지의 거리
- 태그 중앙 정렬 허용 오차
- Well 이동 속도와 Z축 분할 이동 간격
- 피펫 XY 오프셋 및 하강 거리

## 운용 시 주의사항

- 실제 로봇을 움직이기 전에 비상 정지 장치와 작업 공간을 확인해야 합니다.
- 로봇을 저속으로 설정한 상태에서 좌표축 방향, 장착각, 오프셋을 먼저 검증해야 합니다.
- AprilTag의 실제 크기와 코드의 `TAG_SIZE_M` 값이 다르면 거리 및 위치 추정 오차가 발생합니다.
- `/compute_ik`, FollowJointTrajectory Action, `/joint_states`, `base_link` ↔ `tool0` TF가 준비되지 않으면 로봇 기능이 정상 동작하지 않습니다.
- 자동 용량 보정 중에는 GUI와 외부 프로세스가 동일한 시리얼 포트를 동시에 사용하지 않도록 주의해야 합니다.
- 모델 파일과 TensorRT 엔진은 용량이 크므로 배포 방식과 Git LFS 사용 여부를 확인하는 것이 좋습니다.

## 상세 문서

- [피펫 용량 인식·모터 제어 인수인계 문서](pipet_model/설명서.md)
- [OCR·모터 GUI 실행 안내](pipet_model/ocr_motor/README.md)
- [UR 로봇 피펫팅 시스템 인수인계 문서](pipette_robot/설명서.md)

## Contributors

- [**이민우**](https://github.com/minwoo1119) — `pipet_model`: 비전 모델, OCR, 목표 용량 자동 보정 및 모터 제어
- [**정성윤**](https://github.com/jsy0605) — `pipette_robot`: AprilTag 비전, ROS 2·MoveIt 2 연동 및 로봇 피펫팅 자동화

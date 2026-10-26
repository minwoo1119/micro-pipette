# Industrial Anomaly Detection & Edge Deployment

산업용 비전 검사 환경을 가정하여 **PatchCore 기반 이상 탐지 모델을 개발하고, ONNX 및 TensorRT INT8 최적화를 거쳐 Jetson Orin Nano에 배포하는 End-to-End Edge AI 프로젝트**입니다.

모델의 정확도뿐 아니라 실제 엣지 디바이스에서의 **Latency, FPS, Memory Usage, Image AUROC, Pixel AUROC**를 함께 측정하여 정확도와 추론 성능 간의 trade-off를 분석하는 것을 목표로 합니다.

---

## 1. Project Overview

산업 현장에서는 정상 데이터는 충분히 확보할 수 있지만 모든 불량 유형을 사전에 수집하기 어려운 경우가 많습니다.

본 프로젝트에서는 이러한 상황을 가정하여 **정상 이미지만으로 학습 가능한 Unsupervised Anomaly Detection 모델인 PatchCore**를 사용합니다.

전체 파이프라인은 다음과 같습니다.

```text
MVTec AD
   ↓
PatchCore
   ↓
PyTorch Evaluation
   ↓
ONNX Export
   ↓
TensorRT
   ├── FP32
   ├── FP16
   └── INT8 PTQ
   ↓
C++ / OpenCV Runtime
   ↓
Jetson Orin Nano
   ↓
Latency / FPS / Memory / AUROC Benchmark
```

---

## 2. Goals

- MVTec AD `bottle` 데이터셋 기반 산업용 이상 탐지 파이프라인 구현
- PatchCore + WideResNet50-2 기반 정상 특징 학습
- Image-level / Pixel-level anomaly detection 성능 평가
- Ground Truth Mask와 Anomaly Heatmap 비교
- PyTorch 모델의 ONNX 변환 및 출력 일치 검증
- TensorRT FP32 / FP16 / INT8 엔진 비교
- INT8 Post-Training Quantization 적용
- Jetson Orin Nano에서 C++ / OpenCV 기반 실시간 추론 구현
- 정확도 및 엣지 추론 성능 비교 분석

---

## 3. System Architecture

```text
┌─────────────────────────────────────┐
│        Model Development            │
│        Google Colab GPU             │
│                                     │
│  MVTec AD                           │
│      ↓                              │
│  PatchCore                          │
│  WideResNet50-2                     │
│      ↓                              │
│  Memory Bank / Coreset Sampling     │
│      ↓                              │
│  Image / Pixel AUROC                │
│      ↓                              │
│  ONNX Export                        │
└──────────────────┬──────────────────┘
                   │
                model.onnx
                   │
                   ▼
┌─────────────────────────────────────┐
│         Edge Deployment             │
│         Jetson Orin Nano            │
│                                     │
│  TensorRT                           │
│  ├── FP32                           │
│  ├── FP16                           │
│  └── INT8 PTQ                       │
│        ↓                            │
│  C++ / OpenCV                       │
│        ↓                            │
│  Camera / Image Inference           │
│        ↓                            │
│  Benchmark                          │
└─────────────────────────────────────┘
```

---

## 4. Tech Stack

### Model Development

- Python
- PyTorch
- Anomalib
- PatchCore
- WideResNet50-2
- MVTec AD
- NumPy
- Matplotlib
- PIL
- Google Colab GPU

### Model Conversion / Optimization

- ONNX
- ONNX Runtime
- TensorRT
- INT8 Post-Training Quantization

### Edge Deployment

- NVIDIA Jetson Orin Nano
- C++17
- CUDA
- TensorRT Runtime
- OpenCV
- CMake

---

## 5. Development Environment

현재 모델 개발은 **Mac + VS Code + Google Colab GPU** 환경에서 진행합니다.

```text
Mac
 └── VS Code
      └── Colab Extension
           ↓
      Google Colab GPU
```

현재 사용 중인 주요 환경은 다음과 같습니다.

```text
Python   : 3.13
PyTorch  : 2.11.0 + CUDA 12.8
Anomalib : 2.6.x
NumPy    : 2.1.x
Numba    : 0.61.x
```

> Colab 런타임의 패키지 버전은 변경될 수 있으므로 실제 실행 환경은 Notebook에서 다시 확인합니다.

---

## 6. Project Structure

```text
micro-pipette/
│
├── pipet_model/                     # 모델 개발 - 이민우
│   └── ocr_motor/
│
├── pipette_robot/                   # 로봇 시스템 - 정성윤
│   └── pipetting_system/
│
├── notebooks/
│   ├── mvtec_exploration.ipynb
│   ├── patchcore_training.ipynb
│   ├── anomaly_evaluation.ipynb
│   └── model_export.ipynb
│
├── src/
│   ├── train.py
│   ├── evaluate.py
│   └── export_onnx.py
│
├── jetson/
│   ├── include/
│   ├── src/
│   ├── CMakeLists.txt
│   └── README.md
│
├── datasets/
├── models/
├── outputs/
│
├── requirements.txt
├── .gitignore
└── README.md
```

### 담당자

| 폴더 | 담당자 | 담당 영역 |
|---|---|---|
| `pipet_model` | 이민우 | 모델 개발 |
| `pipette_robot` | 정성윤 | 로봇 시스템 개발 |

### Notebook 역할

#### `mvtec_exploration.ipynb`

- MVTec AD `bottle` 데이터셋 구조 확인
- Train / Test 데이터 분포 확인
- 정상 / 이상 이미지 시각화
- Ground Truth Mask 확인
- Image-level / Pixel-level Anomaly 개념 확인

#### `patchcore_training.ipynb`

- PatchCore 모델 구성
- WideResNet50-2 Feature Extractor 설정
- 정상 이미지 특징 추출
- Coreset Sampling
- Memory Bank 생성

#### `anomaly_evaluation.ipynb`

- Image AUROC 평가
- Pixel AUROC 평가
- Anomaly Score 분석
- Ground Truth / Heatmap 비교
- 정상 및 이상 유형별 성능 비교

#### `model_export.ipynb`

- 학습된 PatchCore 모델 로드
- ONNX Export
- ONNX Runtime 추론
- PyTorch ↔ ONNX 출력 비교

---

## 7. Dataset

본 프로젝트에서는 **MVTec AD의 `bottle` 카테고리**를 사용합니다.

```text
bottle/
├── train/
│   └── good/
│
├── test/
│   ├── good/
│   ├── broken_large/
│   ├── broken_small/
│   └── contamination/
│
└── ground_truth/
    ├── broken_large/
    ├── broken_small/
    └── contamination/
```

PatchCore는 학습 단계에서 **정상 이미지(`train/good`)만 사용**합니다.

테스트 시 정상 이미지와 여러 이상 유형을 함께 사용하여 이상 탐지 성능을 평가합니다.

---

## 8. PatchCore Pipeline

PatchCore는 일반적인 CNN처럼 Loss와 Backpropagation을 통해 모델 weight를 학습하지 않습니다.

```text
Normal Image
    ↓
Pre-trained WideResNet50-2
    ↓
Layer2 / Layer3 Features
    ↓
Patch Embedding
    ↓
Coreset Sampling
    ↓
Memory Bank
```

테스트 시에는 다음과 같이 동작합니다.

```text
Test Image
    ↓
Patch Feature Extraction
    ↓
Nearest Neighbor Search
    ↓
Distance from Normal Memory Bank
    ↓
Anomaly Score
+
Anomaly Map
```

현재 `bottle` 학습에서 생성된 Memory Bank 예시는 다음과 같습니다.

```text
Memory Bank Shape : [21401, 1536]
Feature Precision : FP32
```

- `21401`: Coreset Sampling 이후 저장된 정상 patch feature 수
- `1536`: 각 patch feature vector의 차원

---

## 9. Evaluation Metrics

### Image AUROC

이미지 전체가 정상인지 이상인지 구분하는 성능을 평가합니다.

```text
Prediction Score
        ↕
Ground Truth Label
```

### Pixel AUROC

이미지 내부에서 실제 이상 위치를 얼마나 정확하게 찾는지 평가합니다.

```text
Anomaly Map
      ↕
Ground Truth Mask
```

---

## 10. Edge Optimization Plan

Jetson Orin Nano에서는 동일한 ONNX 모델을 기준으로 TensorRT 엔진을 생성하여 비교합니다.

| Runtime | Precision | Image AUROC | Pixel AUROC | Latency | FPS | Memory |
|---|---|---:|---:|---:|---:|---:|
| PyTorch | FP32 | TBD | TBD | TBD | TBD | TBD |
| TensorRT | FP32 | TBD | TBD | TBD | TBD | TBD |
| TensorRT | FP16 | TBD | TBD | TBD | TBD | TBD |
| TensorRT | INT8 | TBD | TBD | TBD | TBD | TBD |

실측 결과가 확보되기 전까지 수치는 기입하지 않습니다.

---

## 11. INT8 Quantization

INT8 단계에서는 MVTec AD의 정상 학습 이미지 일부를 calibration dataset으로 사용하여 Post-Training Quantization을 수행합니다.

```text
Normal Calibration Images
        ↓
INT8 Calibration
        ↓
TensorRT INT8 Engine
        ↓
Accuracy / Latency Trade-off Analysis
```

주요 확인 항목:

- Image AUROC 변화
- Pixel AUROC 변화
- Latency 감소율
- FPS 향상률
- GPU Memory 절감률
- Quantization에 민감한 연산 확인

---

## 12. Jetson C++ Inference Pipeline

최종 C++ Runtime은 다음 구조를 목표로 합니다.

```text
Camera / Image
      ↓
OpenCV
      ↓
Resize / Normalize
      ↓
CUDA Memory Transfer
      ↓
TensorRT Inference
      ↓
Anomaly Score / Map
      ↓
Heatmap Overlay
      ↓
Inspection Result
```

예상 프로젝트 구조:

```text
jetson/
├── include/
│   ├── TensorRTInferencer.hpp
│   └── Preprocessor.hpp
│
├── src/
│   ├── main.cpp
│   ├── TensorRTInferencer.cpp
│   └── Preprocessor.cpp
│
└── CMakeLists.txt
```

---

## 13. Benchmark Plan

최종적으로 다음 성능을 측정합니다.

### Accuracy

- Image AUROC
- Pixel AUROC

### Performance

- Model inference latency
- End-to-end latency
- Throughput (FPS)

### Resource Usage

- GPU Memory
- CPU Usage
- GPU Utilization

필요 시 Jetson의 power mode를 고정하여 동일 조건에서 비교합니다.

---

## 14. Progress

- [x] 프로젝트 구조 구성
- [x] Google Colab GPU 개발 환경 구성
- [x] Anomalib 환경 구성
- [x] MVTec AD `bottle` 데이터셋 탐색
- [x] Ground Truth Mask 시각화
- [x] PatchCore 모델 구성
- [x] 정상 특징 학습
- [x] Coreset 기반 Memory Bank 생성
- [ ] PatchCore 정량 성능 평가
- [ ] Anomaly Heatmap 시각화
- [ ] 정상 / 이상 유형별 Anomaly Score 분석
- [ ] ONNX Export
- [ ] PyTorch ↔ ONNX 결과 검증
- [ ] Jetson 환경 구성
- [ ] TensorRT FP32 Engine 생성
- [ ] TensorRT FP16 Engine 생성
- [ ] INT8 Calibration 및 Engine 생성
- [ ] C++ TensorRT Runtime 구현
- [ ] Jetson Benchmark
- [ ] 최종 결과 비교 및 분석

---

## 15. Expected Outcome

본 프로젝트의 최종 목표는 단순한 이상 탐지 모델 구현이 아니라,

> **산업용 이상 탐지 모델 개발부터 TensorRT INT8 최적화와 Jetson C++ 배포까지 연결되는 End-to-End Edge AI Pipeline을 구현하고 정량적으로 분석하는 것**

입니다.

특히 정확도뿐 아니라 실제 엣지 환경에서의 latency, throughput, memory usage를 함께 분석하여 모델 최적화가 실제 산업용 비전 시스템에 미치는 영향을 평가합니다.

---
title: "실용 가이드: Stable Diffusion 3.5 로컬 설치 및 LoRA 학습 구현"
date: "2026-04-14T09:28:20+09:00"
description: "ComfyUI/Forge를 사용하여 SD 3.5를 위한 견고한 로컬 환경을 구축하고 LoRA를 이용해 모델을 미세 조정합니다."
image: "/images/posts/2026/04/14/guide-Stable-Diffusion-3.5-Local-Installation-and-LoRA-Training.jpg"
type: "posts"
clusters: ["guides"]
categories: ["tutorials"]
tags: ["guide", "tutorial"]
difficulty: "Advanced"
time_to_complete: "45 minutes"
---

## 🎯 개요 (Overview)
본 가이드는 대규모 Stable Diffusion 3.5 모델을 로컬에 설치하고 포괄적인 LoRA 미세 조정 과정을 실행하는 데 필요한 고급 워크플로우를 상세히 설명합니다. 목표는 가상 환경과 전용 학습 파이프라인을 사용하여 재현 가능하고 고성능의 환경을 구축하는 것입니다.

## 🚀 Phase 1. 인프라 구축: 핵심 환경 구성 (Infrastructure Setup: Core Environment Build)
* **Step 1-1. 가상 환경 생성 및 활성화 (Create and Activate Virtual Environment)**
  * *목적:* 프로젝트 종속성을 전역 Python 설치와 격리하여 버전 충돌을 방지합니다.
  * `python3 -m venv sd3_venv`
  * `source sd3_venv/bin/activate`
  * **예상 결과:** 명령 프롬프트 접두사가 `(sd3_venv)`로 변경되어 가상 환경이 활성화되었음을 나타냅니다.

* **Step 1-2. 종속성 설치 (PyTorch/ComfyUI) (Install Dependencies (PyTorch/ComfyUI))**
  * *목적:* 필요한 딥러닝 프레임워크와 주요 UI 도구(ComfyUI/Forge)를 설치합니다. 참고: CUDA 호환성은 가정합니다.
  * `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121`
  * `git clone https://github.com/comfyanonymous/ComfyUI`
  * `cd ComfyUI`
  * `pip install -r requirements.txt`
  * **예상 결과:** PyTorch와 지정된 모든 종속성이 성공적으로 설치됩니다. `ComfyUI` 디렉터리에는 모든 필수 실행 파일과 커스텀 노드가 포함됩니다.

* **Step 1-3. 모델 가중치 다운로드 (Download Model Weights)**
  * *목적:* 대용량 Stable Diffusion 3.5 기본 모델 체크포인트를 확보합니다.
  * `wget https://huggingface.co/path/to/sd3.5/resolve/main/sd3.5_v1.zip`
  * `unzip sd3.5_v1.zip -d ./models/checkpoints`
  * **예상 결과:** ComfyUI 구조 내의 `models/checkpoints` 디렉터리에 기본 `sd3.5` 모델 파일(예: `sd3.5.safetensors`)이 포함됩니다.

## ⚙️ Phase 2. LoRA 학습 설정 및 실행 (LoRA Training Setup and Execution)
* **Step 2-1. 학습 환경 준비 (Kohya) (Prepare Training Environment (Kohya))**
  * *목적:* LoRA 학습은 종종 데이터셋 준비 및 학습 루프를 효율적으로 처리하는 Kohya의 스크립트와 같은 전용 도구를 필요로 합니다.
  * `git clone https://github.com/kohya-ss/sd-scripts`
  * `cd sd-scripts`
  * `pip install -r requirements.txt`
  * **예상 결과:** `sd-scripts` 폴더에는 `train_lora.py` 스크립트를 포함하여 모든 필수 학습 유틸리티가 채워집니다.

* **Step 2-2. 데이터셋 준비 및 정렬 (Dataset Preparation and Alignment)**
  * *목적:* 원본 이미지를 정리하고 캡션을 생성합니다. 모든 원본 이미지는 일관된 해상도(예: 512x512 또는 1024x1024)로 크기 조정 및 정렬되어야 합니다.
  * *작업:* `./training_data/my_subject/`라는 구조화된 폴더를 수동으로 생성하고, 여기에 `image_001.jpg`, `image_002.jpg` 등을 포함시키고, 이에 상응하는 `caption_001.txt` 파일을 만듭니다.
  * **예상 결과:** 학습 스크립트가 배치 처리할 수 있도록 깨끗하고 정리된 데이터셋 디렉터리가 준비됩니다.

* **Step 2-3. LoRA 학습 스크립트 실행 (Execute LoRA Training Script)**
  * *목적:* 준비된 데이터셋을 사용하여 기본 모델 가중치를 미세 조정하기 위해 명령줄 인터페이스를 실행합니다.
  * `python train_lora.py --pretrained_model_name_or_path="[Path to SD 3.5]" --output_dir="[Path to output]" --train_data_folder="training_data/my_subject" --resolution=1024 --train_batch_size=1 --max_train_steps=1000 --learning_rate=1e-5 --network_dim=64`
  * **예상 결과:** 스크립트가 학습 프로세스를 시작하고, 진행 상황 로그(예: 손실 값)를 출력하며, 지정된 출력 디렉터리에 최적화된 LoRA 체크포인트(`.safetensors`)를 생성합니다.

## 🚀 Phase 3. 추론 및 테스트 (Inference and Testing)
* **Step 3-1. ComfyUI에 LoRA 통합 (Integrate LoRA into ComfyUI)**
  * *목적:* 새로 학습된 LoRA 가중치를 이미지 생성을 위해 ComfyUI 워크플로우에 로드합니다.
  * *작업:* 결과 LoRA 파일(예: `my_subject_v1.safetensors`)을 ComfyUI의 `models/loras` 디렉터리에 배치합니다.
  * **예상 결과:** LoRA 파일이 ComfyUI 노드에 의해 인식되어 사용자가 워크플로우 UI에서 이를 선택할 수 있게 됩니다.

* **Step 3-2. 최종 이미지 생성 (Generate Final Image)**
  * *목적:* 기본 모델, LoRA 가중치, 그리고 정제된 프롬프트를 사용하여 최종 생성 패스를 실행합니다.
  * *작업:* ComfyUI에서 SD 3.5 체크포인트를 로드하고, 특정 LoRA를 로드한 후, 상세한 프롬프트(예: "A cinematic portrait of [Subject LoRA], highly detailed, volumetric lighting")를 사용하여 생성 그래프를 실행합니다.
  * **예상 결과:** 기본 모델에 의해 생성되었으며, 미세 조정된 LoRA 가중치에 의해 특정 방식으로 수정된, 고화질의 커스텀 스타일 이미지가 생성됩니다.
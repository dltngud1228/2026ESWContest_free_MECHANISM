# 비전 기반 택배 송장 주소 인식 및 오배송 방지 시스템

> 제24회 임베디드SW경진대회 출품 프로젝트  
> 팀명: **[팀명 입력]**  
> 팀원: **[팀원 입력]**

## 프로젝트 소개

Raspberry Pi와 USB 카메라를 이용하여 택배를 자동 감지하고,
촬영된 이미지에서 운송장 영역을 검출한 뒤 OCR을 통해 주소를 인식하여
등록된 주소와 비교하는 오배송 방지 시스템입니다.

정상 배송으로 판정되면 TFT LCD를 초록색으로 표시하고 배송 완료 음성을 출력하며,
오배송으로 판정되면 TFT LCD를 빨간색으로 표시하고 경고 음성을 출력합니다.

## 주요 기능

- 카메라 기반 택배 감지
- 택배 이미지 자동 촬영
- OpenCV 기반 운송장 영역 검출
- 운송장 원근 보정 및 방향 보정
- OCR 인식을 위한 이미지 전처리
- Tesseract OCR 기반 한글 문자 인식
- 등록 주소와 OCR 결과 비교
- 정상 배송 / 오배송 판정
- ST7789V TFT LCD 2개 상태 표시
- USB 스피커 음성 안내

## 시스템 동작 흐름

```text
택배 감지
   ↓
자동 촬영
   ↓
운송장 검출
   ↓
원근 및 방향 보정
   ↓
OCR 전처리
   ↓
Tesseract OCR
   ↓
주소 비교
   ↓
정상 배송 / 오배송 판정
   ↓
LCD 색상 표시 + 음성 출력
```

## 개발 환경

### Hardware
- Raspberry Pi 5 4GB
- Logitech C270 USB Camera
- ST7789V 2.0" TFT LCD 240×320 × 2
- USB Speaker
- [추가 하드웨어 입력]

### Software
- Raspberry Pi OS 64-bit
- Python 3
- OpenCV
- NumPy
- Tesseract OCR
- Adafruit Blinka
- Adafruit CircuitPython RGB Display

## 저장소 구성

```text
vision-delivery-guard/
├── main.py
├── README.md
├── requirements.txt
└── .gitignore
```

- `main.py` : 전체 시스템 통합 실행 코드
- `README.md` : 프로젝트 설명 및 실행 방법
- `requirements.txt` : Python 패키지 목록
- `.gitignore` : 실행 중 생성되는 파일 및 가상환경 제외 설정

## 설치

### Raspberry Pi 시스템 패키지

```bash
sudo apt update
sudo apt install -y python3-opencv python3-venv tesseract-ocr tesseract-ocr-kor mpg123
```

### Python 가상환경

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
```

### Python 라이브러리

```bash
python -m pip install -r requirements.txt
```

## SPI 설정

```bash
sudo raspi-config
```

`Interface Options → SPI → Enable` 선택 후 재부팅합니다.

```bash
sudo reboot
```

확인:

```bash
ls /dev/spidev*
```

## LCD 핀 구성

현재 `main.py` 기준입니다.

| 기능 | LCD 1 | LCD 2 |
|---|---|---|
| SCL | GPIO11 / Pin 23 | GPIO11 / Pin 23 공유 |
| SDA | GPIO10 / Pin 19 | GPIO10 / Pin 19 공유 |
| CS | GPIO8 / CE0 / Pin 24 | GPIO7 / CE1 / Pin 26 |
| DC | GPIO25 / Pin 22 | GPIO23 / Pin 16 |
| RST | GPIO27 / Pin 13 | GPIO22 / Pin 15 |
| BL | GPIO18 / Pin 12 | GPIO17 / Pin 11 |
| VCC | 3.3V | 3.3V |
| GND | GND | GND |

## 실행 전 수정할 부분

### 정상 배송 주소

`main.py`의 `TARGET_PARTS`를 실제 시연 주소에 맞게 수정합니다.

```python
TARGET_PARTS = [
    "[주소 구성요소 1]",
    "[주소 구성요소 2]",
    "[호수 또는 건물번호]",
]
```

### 음성 파일 경로

```python
COMPLETE_AUDIO = "/home/[사용자명]/complete.mp3"
ERROR_AUDIO = "/home/[사용자명]/error.mp3"
```

## 실행 방법

```bash
source .venv/bin/activate
python main.py
```

## 판정 결과

### 정상 배송
- LCD 2개 전체 초록색 출력
- 배송 완료 음성 재생

### 오배송
- LCD 2개 전체 빨간색 출력
- 오배송 경고 음성 재생

## 핵심 기술

### OpenCV 기반 운송장 검출
HSV 색 공간과 Morphology 연산을 이용하여 운송장 후보 영역을 생성하고,
Contour의 면적 비율, 가로세로 비율, 직사각형 유사도를 이용하여
운송장 가능성이 높은 영역을 선택합니다.

검출된 운송장의 네 모서리를 기준으로 Perspective Transform을 수행하여
OCR에 적합한 정면 이미지로 보정합니다.

### OCR 및 주소 비교
운송장 이미지를 확대하고 대비 및 선명도 보정을 수행한 뒤
Tesseract OCR을 이용하여 한글 문자열을 추출합니다.

OCR 결과와 등록 주소의 문자열 유사도를 비교하여
정상 배송과 오배송을 판정합니다.

## 시연 영상

- YouTube: **[시연 영상 링크 입력]**

## 개발 결과

- 택배 감지 테스트: **[결과 입력]**
- 운송장 검출 성공률: **[결과 입력]**
- OCR 주소 판별 성공률: **[결과 입력]**
- 전체 시스템 테스트: **[결과 입력]**

## 팀원 역할

| 이름 | 담당 업무 |
|---|---|
| [팀원 1] | [담당 업무 입력] |
| [팀원 2] | [담당 업무 입력] |
| [팀원 3] | [담당 업무 입력] |
| [팀원 4] | [담당 업무 입력] |

## 향후 개선 사항

- 다양한 형태와 색상의 운송장 검출 성능 개선
- 조명 및 촬영 각도 변화에 대한 강건성 향상
- OCR 인식 정확도 향상
- 사용자 주소 등록 UI 추가
- 모바일 알림 및 배송 이력 관리 기능 확장

## License

[필요한 경우 라이선스 입력]

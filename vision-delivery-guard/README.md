# 비전 기반 택배 송장 주소 인식 및 오배송 방지 시스템

> 제24회 임베디드SW경진대회
> 팀명: MECHANISM 
> 팀원: 유정화, 이수형, 이아린, 황태경

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

### Software
- Raspberry Pi OS 64-bit
- Python 3
- OpenCV
- NumPy
- Tesseract OCR
- Adafruit Blinka
- Adafruit CircuitPython RGB Display


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

- YouTube: (https://youtube.com/shorts/BGhTb5LXocY)

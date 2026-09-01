import time
import re
import subprocess
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import cv2
import numpy as np

try:
    import board
    import digitalio
    import adafruit_rgb_display.st7789 as st7789
    LCD_LIBRARY_AVAILABLE = True
except ImportError:
    LCD_LIBRARY_AVAILABLE = False


# ==========================================
# 1. 설정값
# ==========================================

CAPTURE_FILENAME = "package_capture-6.jpg"

OUTPUT_DIR_NAME = "final result1"

OCR_SCALE = 3.0

ORIENTATION_BLUE_MARGIN = 1.10

OCR_TEXT_MATCH_THRESHOLD = 0.85

OCR_PAGE_SEGMENTATION_MODES = (6, 11)


# 현재 테스트용 정상 배송 주소
TARGET_PARTS = [    
    "한국공학대학교",
    "제2생활관",
    "422호",
]


# 음성 파일
COMPLETE_AUDIO = "/home/mecha/complete.mp3"
ERROR_AUDIO = "/home/mecha/error.mp3"

LCD_WIDTH = 240
LCD_HEIGHT = 320
LCD_BAUDRATE = 8000000

lcd_displays = []
lcd_backlights = []


# ==========================================
# 2. 음성 출력
# ==========================================

def play_complete():
    print("배송 완료 음성을 출력합니다.")

    subprocess.run(
        [
            "mpg123",
            "-q",
            COMPLETE_AUDIO
        ]
    )


def play_error():
    print("오배송 음성을 출력합니다.")

    subprocess.run(
        [
            "mpg123",
            "-q",
            ERROR_AUDIO
        ]
    )


def init_lcd():

    global lcd_displays
    global lcd_backlights

    if not LCD_LIBRARY_AVAILABLE:

        print(
            "LCD 라이브러리가 설치되어 있지 않아 "
            "LCD 출력을 사용하지 않습니다."
        )

        return


    try:

        spi = board.SPI()


        bl1 = digitalio.DigitalInOut(board.D18)
        bl1.direction = digitalio.Direction.OUTPUT
        bl1.value = True


        bl2 = digitalio.DigitalInOut(board.D17)
        bl2.direction = digitalio.Direction.OUTPUT
        bl2.value = True


        lcd1 = st7789.ST7789(
            spi,
            rotation=0,
            width=LCD_WIDTH,
            height=LCD_HEIGHT,
            cs=digitalio.DigitalInOut(board.CE0),
            dc=digitalio.DigitalInOut(board.D25),
            rst=digitalio.DigitalInOut(board.D27),
            baudrate=LCD_BAUDRATE
        )


        lcd2 = st7789.ST7789(
            spi,
            rotation=0,
            width=LCD_WIDTH,
            height=LCD_HEIGHT,
            cs=digitalio.DigitalInOut(board.CE1),
            dc=digitalio.DigitalInOut(board.D23),
            rst=digitalio.DigitalInOut(board.D22),
            baudrate=LCD_BAUDRATE
        )


        lcd_displays = [
            lcd1,
            lcd2
        ]


        lcd_backlights = [
            bl1,
            bl2
        ]


        set_lcd_color(
            0x0000
        )


        print("LCD 2개 초기화 완료")


    except Exception as error:

        lcd_displays = []
        lcd_backlights = []

        print(
            f"LCD 초기화 실패: {error}"
        )



def set_lcd_color(
    color: int
) -> None:

    if not lcd_displays:
        return


    for display in lcd_displays:

        display.fill(
            color
        )



def show_delivery_complete() -> None:

    set_lcd_color(
        0x07E0
    )



def show_misdelivery() -> None:

    set_lcd_color(
        0xF800
    )



# ==========================================
# 3. 카메라 감지 및 촬영
# ==========================================

def detect_package() -> Path | None:

    cap = cv2.VideoCapture(0)

    capture_file_path = (
        Path(__file__).resolve().parent
        / CAPTURE_FILENAME
    )

    if not cap.isOpened():
        print("에러: 카메라를 찾을 수 없습니다.")
        return None


    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)

    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)


    print("카메라 켜는 중... 센서 안정화 대기")


    for _ in range(50):

        cap.read()

        time.sleep(0.05)


    print("시스템 준비 완료. 빈 구역을 기억합니다.")


    ret, bg_frame = cap.read()


    if not ret:

        print("에러: 카메라 프레임을 읽을 수 없습니다.")

        cap.release()

        return None


    bg_gray = cv2.cvtColor(
        bg_frame,
        cv2.COLOR_BGR2GRAY
    )


    bg_gray = cv2.GaussianBlur(
        bg_gray,
        (21, 21),
        0
    )


    print("택배 감지 대기 중...")


    saved_capture_path = None


    while True:

        ret, frame = cap.read()


        if not ret:
            break


        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )


        gray = cv2.GaussianBlur(
            gray,
            (21, 21),
            0
        )


        diff = cv2.absdiff(
            bg_gray,
            gray
        )


        thresh = cv2.threshold(
            diff,
            30,
            255,
            cv2.THRESH_BINARY
        )[1]


        changed_pixels = cv2.countNonZero(
            thresh
        )


        if changed_pixels > 30000:

            print(
                f"\n택배 감지! "
                f"(현재 변화량: {changed_pixels})"
            )


            print(
                "손을 치울 수 있도록 "
                "3초 기다립니다."
            )


            time.sleep(3)


            # 카메라 화면 안정화
            for _ in range(5):

                cap.read()


            ret, final_frame = cap.read()


            if ret:

                try:

                    save_image(
                        capture_file_path,
                        final_frame
                    )

                except RuntimeError as error:

                    print(f"에러: {error}")

                else:

                    print(
                        f"사진 촬영 완료: "
                        f"{capture_file_path}"
                    )


                    saved_capture_path = (
                        capture_file_path
                    )


            else:

                print(
                    "에러: 최종 사진 촬영 실패"
                )


            break


        time.sleep(0.2)


    cap.release()


    print("카메라 종료")


    return saved_capture_path


# ==========================================
# 4. 이미지 읽기
# ==========================================

def read_image(
    image_path: Path
) -> np.ndarray:

    try:

        image_bytes = np.fromfile(
            str(image_path),
            dtype=np.uint8
        )

    except OSError as error:

        raise RuntimeError(
            f"이미지 파일을 열 수 없습니다: "
            f"{image_path}"
        ) from error


    frame = cv2.imdecode(
        image_bytes,
        cv2.IMREAD_COLOR
    )


    if frame is None:

        raise RuntimeError(
            f"이미지를 읽을 수 없습니다: "
            f"{image_path}"
        )


    return frame


# ==========================================
# 5. 운송장 검출 전처리
# ==========================================

def preprocess(
    frame: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:

    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )


    blur = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )


    hsv = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2HSV
    )


    neutral_mask = cv2.inRange(
        hsv,
        np.array(
            [0, 0, 70],
            dtype=np.uint8
        ),
        np.array(
            [179, 45, 255],
            dtype=np.uint8
        )
    )


    blue_mask = cv2.inRange(
        hsv,
        np.array(
            [85, 35, 45],
            dtype=np.uint8
        ),
        np.array(
            [135, 255, 255],
            dtype=np.uint8
        )
    )


    blue_ratio = (
        cv2.countNonZero(blue_mask)
        / blue_mask.size
    )


    if blue_ratio >= 0.01:

        binary = blue_mask

    else:

        binary = neutral_mask


    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (13, 13)
    )


    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=1
    )


    small_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (3, 3)
    )


    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        small_kernel
    )


    return gray, blur, binary


# ==========================================
# 6. 운송장 윤곽선 찾기
# ==========================================

def find_label_contour(
    binary: np.ndarray
) -> np.ndarray:

    contours, _ = cv2.findContours(
        binary,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )


    image_area = (
        binary.shape[0]
        * binary.shape[1]
    )


    best_contour = None

    best_score = 0.0


    for contour in contours:

        area = cv2.contourArea(
            contour
        )


        area_ratio = (
            area
            / image_area
        )


        if not 0.02 <= area_ratio <= 0.90:
            continue


        x, y, bounding_width, bounding_height = (
            cv2.boundingRect(contour)
        )


        width_ratio = (
            bounding_width
            / binary.shape[1]
        )


        height_ratio = (
            bounding_height
            / binary.shape[0]
        )


        if (
            width_ratio >= 0.97
            and height_ratio >= 0.97
        ):
            continue


        rotated_rect = cv2.minAreaRect(
            contour
        )


        width, height = rotated_rect[1]


        if width <= 0 or height <= 0:
            continue


        long_side = max(
            width,
            height
        )


        short_side = min(
            width,
            height
        )


        aspect_ratio = (
            long_side
            / short_side
        )


        rectangularity = (
            area
            / (width * height)
        )


        if not 1.15 <= aspect_ratio <= 5.0:
            continue


        if rectangularity < 0.55:
            continue


        score = (
            area_ratio
            * rectangularity
        )


        if score > best_score:

            best_score = score

            best_contour = contour


    if best_contour is None:

        raise RuntimeError(
            "운송장 후보를 찾지 못했습니다."
        )


    return best_contour


# ==========================================
# 7. 모서리 찾기
# ==========================================

def contour_corners(
    contour: np.ndarray
) -> np.ndarray:

    perimeter = cv2.arcLength(
        contour,
        True
    )


    polygon = cv2.approxPolyDP(
        contour,
        0.02 * perimeter,
        True
    )


    if len(polygon) == 4:

        return (
            polygon
            .reshape(4, 2)
            .astype(np.float32)
        )


    rotated_rect = cv2.minAreaRect(
        contour
    )


    return cv2.boxPoints(
        rotated_rect
    ).astype(np.float32)


# ==========================================
# 8. 모서리 순서 정렬
# ==========================================

def order_corners(
    points: np.ndarray
) -> np.ndarray:

    ordered = np.zeros(
        (4, 2),
        dtype=np.float32
    )


    coordinate_sum = (
        points.sum(axis=1)
    )


    coordinate_difference = (
        np.diff(
            points,
            axis=1
        )
        .reshape(-1)
    )


    ordered[0] = points[
        np.argmin(coordinate_sum)
    ]


    ordered[2] = points[
        np.argmax(coordinate_sum)
    ]


    ordered[1] = points[
        np.argmin(
            coordinate_difference
        )
    ]


    ordered[3] = points[
        np.argmax(
            coordinate_difference
        )
    ]


    return ordered


# ==========================================
# 9. 원근 보정
# ==========================================

def warp_label(
    frame: np.ndarray,
    corners: np.ndarray
) -> np.ndarray:

    (
        top_left,
        top_right,
        bottom_right,
        bottom_left
    ) = order_corners(corners)


    width_top = np.linalg.norm(
        top_right - top_left
    )


    width_bottom = np.linalg.norm(
        bottom_right - bottom_left
    )


    height_right = np.linalg.norm(
        bottom_right - top_right
    )


    height_left = np.linalg.norm(
        bottom_left - top_left
    )


    output_width = max(
        1,
        int(
            max(
                width_top,
                width_bottom
            )
        )
    )


    output_height = max(
        1,
        int(
            max(
                height_right,
                height_left
            )
        )
    )


    destination = np.array(
        [
            [0, 0],

            [
                output_width - 1,
                0
            ],

            [
                output_width - 1,
                output_height - 1
            ],

            [
                0,
                output_height - 1
            ]
        ],
        dtype=np.float32
    )


    transform = (
        cv2.getPerspectiveTransform(
            np.array(
                [
                    top_left,
                    top_right,
                    bottom_right,
                    bottom_left
                ]
            ),
            destination
        )
    )


    warped = cv2.warpPerspective(
        frame,
        transform,
        (
            output_width,
            output_height
        )
    )


    if (
        warped.shape[0]
        > warped.shape[1]
    ):

        warped = cv2.rotate(
            warped,
            cv2.ROTATE_90_CLOCKWISE
        )


    return warped


# ==========================================
# 10. 운송장 방향 보정
# ==========================================

def correct_label_orientation(
    label: np.ndarray
) -> tuple[np.ndarray, bool]:

    hsv = cv2.cvtColor(
        label,
        cv2.COLOR_BGR2HSV
    )


    blue_mask = cv2.inRange(
        hsv,
        np.array(
            [85, 35, 45],
            dtype=np.uint8
        ),
        np.array(
            [135, 255, 255],
            dtype=np.uint8
        )
    )


    height = blue_mask.shape[0]


    section_height = max(
        1,
        height // 3
    )


    top_section = (
        blue_mask[:section_height]
    )


    bottom_section = (
        blue_mask[-section_height:]
    )


    top_blue_ratio = (
        cv2.countNonZero(top_section)
        / top_section.size
    )


    bottom_blue_ratio = (
        cv2.countNonZero(bottom_section)
        / bottom_section.size
    )


    total_blue_ratio = (
        cv2.countNonZero(blue_mask)
        / blue_mask.size
    )


    if total_blue_ratio < 0.01:

        return label, False


    if (
        bottom_blue_ratio
        > top_blue_ratio
        * ORIENTATION_BLUE_MARGIN
    ):

        return (
            cv2.rotate(
                label,
                cv2.ROTATE_180
            ),
            True
        )


    return label, False


# ==========================================
# 11. OCR용 이미지 보정
# ==========================================

def enhance_label_for_ocr(
    label: np.ndarray,
    scale: float = OCR_SCALE
) -> tuple[np.ndarray, np.ndarray]:

    enlarged = cv2.resize(
        label,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_CUBIC
    )


    gray = cv2.cvtColor(
        enlarged,
        cv2.COLOR_BGR2GRAY
    )


    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )


    contrast = clahe.apply(
        gray
    )


    denoised = cv2.bilateralFilter(
        contrast,
        7,
        35,
        35
    )


    soft = cv2.GaussianBlur(
        denoised,
        (0, 0),
        1.0
    )


    sharpened = cv2.addWeighted(
        denoised,
        1.8,
        soft,
        -0.8,
        0
    )


    return enlarged, sharpened


# ==========================================
# 12. 이미지 저장
# ==========================================

def save_image(
    path: Path,
    image: np.ndarray
) -> None:

    extension = (
        path.suffix.lower()
    )


    success, encoded_image = (
        cv2.imencode(
            extension,
            image
        )
    )


    if not success:

        raise RuntimeError(
            f"이미지 저장 실패: {path}"
        )


    encoded_image.tofile(
        str(path)
    )


# ==========================================
# 13. 운송장 추출
# ==========================================

def extract_label(
    frame: np.ndarray,
    output_dir: Path
) -> Path:

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    _, _, binary = preprocess(
        frame
    )


    contour = find_label_contour(
        binary
    )


    corners = contour_corners(
        contour
    )


    warped_label = warp_label(
        frame,
        corners
    )


    (
        warped_label,
        rotated_180
    ) = correct_label_orientation(
        warped_label
    )


    (
        _,
        ocr_ready_label
    ) = enhance_label_for_ocr(
        warped_label
    )


    if rotated_180:

        print(
            "운송장이 거꾸로 검출되어 "
            "180도 회전했습니다."
        )


    result_path = (
        output_dir
        / "ocr_ready_label.png"
    )


    save_image(
        result_path,
        ocr_ready_label
    )


    return result_path


# ==========================================
# 14. OCR + 주소 비교
# ==========================================

def normalize_ocr_text(text: str) -> str:

    normalized = unicodedata.normalize(
        "NFKC",
        text
    )


    return re.sub(
        r"[^0-9A-Za-z가-힣]",
        "",
        normalized
    ).lower()


def best_partial_similarity(
    target: str,
    text: str
) -> float:

    if not target or not text:
        return 0.0


    if target in text:
        return 1.0


    shortest_window = max(
        1,
        len(target) - 1
    )

    longest_window = min(
        len(text),
        len(target) + 1
    )

    best_score = 0.0


    for window_length in range(
        shortest_window,
        longest_window + 1
    ):

        for start in range(
            len(text) - window_length + 1
        ):

            candidate = text[
                start:start + window_length
            ]

            score = SequenceMatcher(
                None,
                target,
                candidate
            ).ratio()

            best_score = max(
                best_score,
                score
            )


    return best_score


def run_tesseract(
    image_path: Path,
    page_segmentation_mode: int
) -> str:

    try:

        ocr_result = subprocess.run(
            [
                "tesseract",
                str(image_path),
                "stdout",
                "-l",
                "kor",
                "--psm",
                str(page_segmentation_mode)
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30
        )

    except FileNotFoundError as error:

        raise RuntimeError(
            "Tesseract가 설치되어 있지 않거나 "
            "실행 경로에 없습니다."
        ) from error

    except subprocess.TimeoutExpired as error:

        raise RuntimeError(
            "Tesseract OCR 실행 시간이 초과되었습니다."
        ) from error


    if ocr_result.returncode != 0:

        error_message = (
            ocr_result.stderr.strip()
            or "원인을 확인할 수 없습니다."
        )

        raise RuntimeError(
            "Tesseract OCR 실행 실패: "
            f"{error_message}"
        )


    return ocr_result.stdout


def compare_address_text(text: str) -> bool:

    clean_text = normalize_ocr_text(text)

    number_tokens = re.findall(
        r"\d+",
        unicodedata.normalize("NFKC", text)
    )


    if not clean_text:

        raise RuntimeError(
            "OCR 결과가 비어 있어 주소를 판정할 수 없습니다."
        )


    print("\n=== 주소 비교 ===")


    all_match = True


    for part in TARGET_PARTS:

        clean_part = normalize_ocr_text(part)


        if clean_part.isdigit():

            score = (
                1.0
                if clean_part in number_tokens
                else 0.0
            )

            matched = score == 1.0

        else:

            score = best_partial_similarity(
                clean_part,
                clean_text
            )

            matched = (
                score
                >= OCR_TEXT_MATCH_THRESHOLD
            )


        status = "일치" if matched else "불일치"

        print(
            f"{part} → {status} "
            f"(유사도: {score:.0%})"
        )


        if not matched:
            all_match = False


    return all_match

def check_address(
    image_path: Path
) -> bool:

    print("\n[3단계] OCR을 시작합니다...")


    print("\n=== OCR 결과 ===")

    ocr_texts = []


    for mode in OCR_PAGE_SEGMENTATION_MODES:

        mode_text = run_tesseract(
            image_path,
            mode
        )

        print(f"\n--- PSM {mode} ---")

        print(mode_text)

        ocr_texts.append(mode_text)


    combined_text = "\n".join(ocr_texts)


    return compare_address_text(
        combined_text
    )


# ==========================================
# 15. 전체 실행
# ==========================================

def main() -> None:

    init_lcd()


    print(
        "\n[1단계] "
        "택배 감지 및 촬영"
    )


    captured_path = (
        detect_package()
    )


    if not captured_path:

        print(
            "촬영에 실패했습니다."
        )

        return


    print(
        "\n[2단계] "
        "운송장 검출 및 자르기"
    )


    script_dir = (
        Path(__file__)
        .resolve()
        .parent
    )


    image_path = captured_path


    output_dir = (
        script_dir
        / OUTPUT_DIR_NAME
    )


    try:

        frame = read_image(
            image_path
        )


        result_path = extract_label(
            frame,
            output_dir
        )


        print(
            f"\n운송장 추출 완료:"
            f"\n{result_path.resolve()}"
        )


        # OCR + 주소 비교
        address_match = check_address(
            result_path
        )


        print(
            "\n[4단계] 최종 판정"
        )


        if address_match:

            print(
                "결과: 1 - 정상 배송"
            )

            show_delivery_complete()


            play_complete()


        else:

            print(
                "결과: 2 - 오배송"
            )

            show_misdelivery()


            play_error()


    except Exception as error:

        print(
            f"\n에러 발생: {error}"
        )


# ==========================================
# 프로그램 시작
# ==========================================

if __name__ == "__main__":

    main()

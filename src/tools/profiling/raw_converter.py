import traceback

import rawpy
import exiv2
from fractions import Fraction
import imageio.v3 as iio
import numpy as np
from pathlib import Path
from typing import List, Union, Optional, Dict, Tuple
import glob
from const import GENERIC_ERROR, GENERIC_OK, NEGATIVE_FILM, POSITIVE_FILM

# Qt translation support
def get_translator():
    """Get Qt translator function"""
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            return lambda text, context="RawConverter": app.translate(context, text)
    except ImportError:
        pass
    return lambda text, context="RawConverter": text

# Global translation function
tr = get_translator()


def sanitize_filename(text):
    """Clean filename from problematic characters"""
    if not text:
        return "unknown"

    # Replace problematic characters with readable ones
    replacements = {
        '.': '_',  # dot → underscore
        '/': '-',  # slash → dash
        '\\': '-',  # backslash → dash
        ' ': '_',  # space → underscore
        ':': '-',  # colon → dash
        '*': 'x',  # asterisk → x
        '?': '',  # question mark → remove
        '"': '',  # quotes → remove
        '<': '',  # brackets → remove
        '>': '',
        '|': '-',  # pipe → dash
    }

    result = str(text)
    for old, new in replacements.items():
        result = result.replace(old, new)

    return result


def _is_valid_multipliers(r_mul, g_mul, b_mul):
    """Проверка multipliers на разумность"""
    try:
        # Нормализация
        r_norm = r_mul / g_mul
        b_norm = b_mul / g_mul

        # Проверка диапазонов (типичные значения 0.5-4.0)
        if not (0.3 < r_norm < 5.0 and 0.3 < b_norm < 5.0):
            return False

        # Проверка что каналы не равны (признак битых данных)
        if abs(r_norm - 1.0) < 0.1 and abs(b_norm - 1.0) < 0.1:
            return False

        return True

    except (ZeroDivisionError, TypeError):
        return False


def _calculate_wb_data(r_mul, g_mul, b_mul, raw_multipliers, source, confidence):
    """Вычисление данных WB из multipliers"""

    # Нормализация по G каналу
    r_norm = float(r_mul) / g_mul
    b_norm = float(b_mul) / g_mul
    ratio = r_norm / b_norm

    # Расчет температуры (существующий алгоритм)
    if ratio > 1.0:
        temperature = int(6500 / (ratio ** 0.6))
    else:
        temperature = int(6500 * (1.0 / ratio) ** 0.4)

    # Ограничение диапазона
    temperature = max(2000, min(12000, temperature))

    return {
        'temperature': temperature,
        'multipliers': [r_norm, 1.0, b_norm],
        'raw_multipliers': list(raw_multipliers[:3]),
        'ratio': ratio,
        'source': source,
        'confidence': confidence
    }

def get_extended_metadata(raw_file_path: Path) -> Dict[str, Union[str, float, int, None]]:
    """
    Extract comprehensive metadata from RAW file using python-exiv2.

    Args:
        raw_file_path: Path to RAW file

    Returns:
        Dictionary with extended metadata fields
    """
    try:

        # Open image and read metadata
        image = exiv2.ImageFactory.open(str(raw_file_path))

        image.readMetadata()

        exif_data = image.exifData()

        # Helper function to safely extract tag value
        def get_tag_value(tag_name: str, default=None):
            try:
                if tag_name in exif_data:
                    return str(exif_data[tag_name].value())
                return default
            except:
                return default

        # Helper function to convert fraction string to float
        def fraction_to_float(fraction_str: str) -> float:
            if not fraction_str:
                return 0.0
            try:
                if '/' in fraction_str:
                    num, den = fraction_str.split('/')
                    return float(num) / float(den)
                else:
                    return float(fraction_str)
            except:
                return 0.0

        # Helper function to get numeric value directly

        def get_numeric_value(tag_name: str, default=0):
            try:
                if tag_name in exif_data:
                    value = exif_data[tag_name].value()

                    # Convert any exiv2 value to string first, then to float
                    str_value = str(value)
                    return fraction_to_float(str_value)
                return default
            except Exception as e:
                print(f"Error getting numeric value for {tag_name}: {e}")
                return default

        def get_WB(image_path, default=0):
            """
            Извлекает данные баланса белого из RAW файла.

            Returns:
                dict: Словарь с данными WB или пустой dict при неудаче
                {
                    'temperature': int,           # CCT в Kelvin (2000-12000)
                    'multipliers': [float, float, float],  # [R, G, B] нормализованные
                    'raw_multipliers': [float, float, float],  # Исходные значения
                    'ratio': float,               # R/B соотношение
                    'source': str,               # 'camera_wb' | 'daylight_wb' | 'default'
                    'confidence': str            # 'high' | 'medium' | 'low'
                }
            """
            try:
                with rawpy.imread(str(image_path)) as raw:
                    # Попытка 1: camera_whitebalance (основной)
                    cam_mul = raw.camera_whitebalance

                    if (cam_mul is not None and len(cam_mul) >= 3 and
                            all(x > 0 for x in cam_mul[:3])):

                        r_mul, g_mul, b_mul = cam_mul[0], cam_mul[1], cam_mul[2]

                        # Проверка на разумность данных
                        if _is_valid_multipliers(r_mul, g_mul, b_mul):
                            return _calculate_wb_data(r_mul, g_mul, b_mul,
                                                      cam_mul, 'camera_wb', 'high')

                    # Попытка 2: daylight_whitebalance (запасной)
                    day_mul = raw.daylight_whitebalance

                    if (day_mul is not None and len(day_mul) >= 3 and
                            all(x > 0 for x in day_mul[:3])):

                        r_mul, g_mul, b_mul = day_mul[0], day_mul[1], day_mul[2]

                        if _is_valid_multipliers(r_mul, g_mul, b_mul):
                            return _calculate_wb_data(r_mul, g_mul, b_mul,
                                                      day_mul, 'daylight_wb', 'medium')

                    # Попытка 3: Значения по умолчанию (D65)
                    return {}

            except Exception as e:
                print(f"Warning: Ошибка чтения RAW файла {image_path}: {e}")
                return {}  # Пустой dict при полном провале

        metadata = {
            # Basic camera info
            'camera_make': get_tag_value('Exif.Image.Make'),
            'camera_model': get_tag_value('Exif.Image.Model'),
            'datetime': get_tag_value('Exif.Photo.DateTimeOriginal') or get_tag_value('Exif.Image.DateTime'),

            # Exposure settings
            'exposure_time': get_tag_value('Exif.Photo.ExposureTime'),
            'exposure_time_float': get_numeric_value('Exif.Photo.ExposureTime'),
            'f_number': get_tag_value('Exif.Photo.FNumber'),
            'f_number_float': get_numeric_value('Exif.Photo.FNumber'),
            'iso': get_tag_value('Exif.Photo.ISOSpeedRatings'),
            'exposure_compensation': get_tag_value('Exif.Photo.ExposureBiasValue'),
            'exposure_mode': get_tag_value('Exif.Photo.ExposureMode'),
            'metering_mode': get_tag_value('Exif.Photo.MeteringMode'),
            'flash': get_tag_value('Exif.Photo.Flash'),

            # Lens information
            'focal_length': get_tag_value('Exif.Photo.FocalLength'),
            'focal_length_35mm': get_tag_value('Exif.Photo.FocalLengthIn35mmFilm'),
            'lens_make': get_tag_value('Exif.Photo.LensMake'),
            'lens_model': get_tag_value('Exif.Photo.LensModel'),
            'max_aperture': get_tag_value('Exif.Photo.MaxApertureValue'),

            # White balance and color
            'white_balance': get_tag_value('Exif.Photo.WhiteBalance'),
            'white_balance_int': get_tag_value('Exif.Photo.WhiteBalance'),
            'color_space': get_tag_value('Exif.Photo.ColorSpace'),
            'scene_type': get_tag_value('Exif.Photo.SceneType'),
            'scene_capture_type': get_tag_value('Exif.Photo.SceneCaptureType'),
            'saturation': get_tag_value('Exif.Photo.Saturation'),
            'sharpness': get_tag_value('Exif.Photo.Sharpness'),
            'contrast': get_tag_value('Exif.Photo.Contrast'),

            # Advanced exposure info
            'exposure_program': get_tag_value('Exif.Photo.ExposureProgram'),
            'aperture_value': get_tag_value('Exif.Photo.ApertureValue'),
            'shutter_speed_value': get_tag_value('Exif.Photo.ShutterSpeedValue'),
            'subject_distance': get_tag_value('Exif.Photo.SubjectDistance'),
            'digital_zoom_ratio': get_tag_value('Exif.Photo.DigitalZoomRatio'),

            # Addon fields
            # Size
            'width': get_numeric_value('Exif.Photo.PixelXDimension', 0),
            'height': get_numeric_value('Exif.Photo.PixelYDimension', 0),

            # Negative/positive film
            'is_negative': False,  # bool для логики
            'film_type': 'positive',  # строка для UI
            "WB":    get_WB(raw_file_path),

        # Processing info
            'source_file_path': str(raw_file_path),  # full name with path
            'source_file_name': raw_file_path.name,  # file name only (nj rich the file if moved)
            'output_files': {},  # result files
            'modes_processed': [],  # processing modes
        }

        return metadata

    except ImportError:
        print(f"Error: {tr('python-exiv2 library not installed. Install with: pip install python-exiv2')}")
        return {}
    except Exception as e:
        print(f"Error reading extended metadata: {e}")
        return {}

def detect_negative_fast_numpy(rgb_array: np.ndarray) -> int:
    """
    Fast heuristic for detecting negative on large numpy array.
    Optimized for 50MP linear RGB uint16 data.

    Parameters:
        rgb_array: numpy array shape (height, width, 3), dtype uint16

    Returns:
        True  — likely negative
        False — likely positive
    """

    if rgb_array.size == 0:
        return GENERIC_ERROR

    height, width = rgb_array.shape[:2]

    # Smart decimation: take every Nth pixel for ~512px width
    step = max(1, width // 512)
    small = rgb_array[::step, ::step]

    # Vectorized luminance conversion (coefficients for linear RGB)
    # Use @ for fast matrix multiplication
    luma = small @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)

    # Fast histogram with fixed 16-bit range
    vmax = luma.max()
    if vmax == 0:  # Protection against black image
        return False

    hist, _ = np.histogram(luma, bins=256, range=(0, vmax))

    # Shadows and highlights: lower/upper 25% of histogram
    shadows = hist[:64].sum()
    highlights = hist[-64:].sum()

    # Negative = more shadows than highlights (with 1.5 threshold)
    is_negative = shadows > highlights * 1.5
    return NEGATIVE_FILM if is_negative else POSITIVE_FILM

def format_shutter_speed_for_filename(shutter_speed):
    """Convert shutter speed to short filename format"""

    if shutter_speed >= 1:
        return f"{int(shutter_speed)}s"
    else:
        # For fractions, just use denominator
        denominator = round(1 / shutter_speed)
        return str(denominator)

def convert_raw_batch(
        input_files: Union[str, List[str]],
        output_dir: str = "",
        modes: Union[str, List[str]] = "ICC",
        demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD,
) -> Tuple[int, Dict[str, Dict[str, any]]]:
    """
    Batch conversion of RAW files with wildcard and multiple mode support.

    Args:
        input_files: File list or wildcard pattern ("*.cr3", "_V*2.cr2")
        output_dir: Output directory (empty = next to source files)
        modes: Conversion mode(s) ["icc", "lut", "cineon", "bkr" (simplified processing)] or list of modes
        demosaic_algorithm: Demosaic algorithm

    Returns:
        Tuple[int, Dict[str, Dict[str, any]]]:
            - First element: GENERIC_OK or GENERIC_ERROR on error
            - Second element: dictionary {filename: metadata_dict}

        Return dictionary structure:
        {
            "IMG_001.CR3": {
                # === BASIC FILE INFO ===
                "source_file_path": "/full/path/to/IMG_001.CR3",    # str: full path to source file (duplicate)
                "source_file_name": "IMG_001.CR3",                  # str: filename only (duplicate)

                # === CAMERA INFO ===
                "camera_make": "Canon",                             # str: camera manufacturer
                "camera_model": "EOS R5",                           # str: camera model
                "datetime": "2024:03:15 14:30:45",                  # str: photo timestamp

                # === EXPOSURE SETTINGS ===
                "exposure_time": "1/125",                           # str: shutter speed as fraction
                "exposure_time_float": 0.008,                       # float: shutter speed as decimal
                "f_number": "5.6",                                  # str: aperture as fraction
                "f_number_float": 5.6,                              # float: aperture as decimal
                "iso": "800",                                       # str: ISO sensitivity
                "exposure_compensation": "0",                       # str: exposure compensation
                "exposure_mode": "1",                               # str: exposure mode
                "metering_mode": "2",                               # str: metering mode
                "flash": "16",                                      # str: flash mode

                # === LENS INFO ===
                "focal_length": "85.0",                             # str: focal length in mm
                "focal_length_35mm": "85",                          # str: 35mm equivalent focal length
                "lens_make": "Canon",                               # str: lens manufacturer
                "lens_model": "RF 85mm f/1.2L USM",               # str: lens model
                "max_aperture": "1.2",                              # str: maximum aperture

                # === WHITE BALANCE & COLOR ===
                "white_balance": "Auto",                            # str: white balance setting
                "white_balance_int": "0",                           # str: white balance as integer
                "color_space": "1",                                 # str: color space
                "scene_type": "1",                                  # str: scene type
                "scene_capture_type": "0",                          # str: scene capture type
                "saturation": "0",                                  # str: saturation setting
                "sharpness": "0",                                   # str: sharpness setting
                "contrast": "0",                                    # str: contrast setting

                # === ADVANCED EXPOSURE ===
                "exposure_program": "3",                            # str: exposure program mode
                "aperture_value": "5.6",                            # str: aperture value
                "shutter_speed_value": "7.0",                       # str: shutter speed value
                "subject_distance": "2.5",                          # str: subject distance in meters
                "digital_zoom_ratio": "1.0",                        # str: digital zoom ratio

                # === PROCESSING RESULTS (added after conversion) ===
                "width": 8192,                                      # int: processed image width in pixels
                "height": 5464,                                     # int: processed image height in pixels
                "is_negative": "Positive",                          # str: "Negative" or "Positive" film type detection
                "film_type": False,                                 # bool: True for negative, False for positive
                "modes_processed": ["icc", "lut"],                  # List[str]: processing modes applied

                # === OUTPUT FILES ===
                "output_files": {},                                 # Dict: result files (currently empty)
            },
            "IMG_002.CR3": {
                # ... same structure for next file
            }
        }

        Error case:
            Returns: (GENERIC_ERROR, {})

        Success case:
            Returns: (processed_count, metadata_dict)
            where processed_count = number of files × number of modes
    """

    ret = {}
    # Process input files
    try:
        if isinstance(input_files, str):
            if '*' in input_files or '?' in input_files:
                file_list = glob.glob(input_files)
            else:
                file_list = [input_files]
        else:
            file_list = input_files

        file_paths = [Path(f) for f in file_list]

        if not file_paths:
            print(tr("ERROR: No files found for processing"))
            return GENERIC_ERROR, {}

    except Exception as e:
        print(tr("ERROR: Could not process file list: {}").format(e))
        return GENERIC_ERROR, {}

    # Process modes
    if isinstance(modes, str):
        modes_list = [modes]
    else:
        modes_list = modes

    # Determine base output directory
    base_output_path = Path(output_dir) if output_dir else None

    # Create base output directory once
    if base_output_path:
        try:
            base_output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(tr("ERROR: Cannot create output directory: {}").format(e))
            return GENERIC_ERROR, {}

    # Log conversion start
    total_files = len(file_paths) * len(modes_list)
    print(tr("Converting {} files...").format(total_files))
    print(tr("Modes: {}").format(', '.join(modes_list)))

    processed_count = 0
    result_files = {mode: [] for mode in modes_list}
    created_files = []  # Track ALL created files for cleanup
    try:
        for file_index, input_file in enumerate(file_paths, 1):
            if not input_file.exists():
                print(tr("ERROR: File not found: {}").format(input_file))
                # File not found = critical error, cleanup and exit
                cleanup_failed_files(created_files, result_files)
                return GENERIC_ERROR, {}

            print(tr("{}: {}").format(file_index, input_file))

            # Get metadata once per file
            metadata = get_extended_metadata(input_file)
            metadata['modes_processed'] = modes_list
            metadata["output_files"] = {}
            files_dict = metadata["output_files"]
            #wb_temp = get_precise_white_balance(image)

            for mode in modes_list:
                try:
                    # Determine output directory for this file
                    current_output_dir = base_output_path if base_output_path else input_file.parent

                    # Form output filename
                    wb_temp = metadata.get('WB', 0)
                    f_number = metadata.get('f_number_float', 0)
                    exp_time = format_shutter_speed_for_filename(metadata.get('exposure_time_float', 0))
                    camera_model = sanitize_filename(metadata.get('camera_model', 'unknown'))

                    base_name = f"{input_file.stem}_{mode}_{wb_temp}_F{f_number}_{exp_time}_{camera_model}"
                    output_filename = f"{base_name}.tif"
                    output_file = current_output_dir / output_filename

                    # Convert file
                    print(tr("{} {}").format(mode, output_filename))

                    data = convert_raw(
                        str(input_file),
                        str(output_file),
                        mode=mode,
                        demosaic_algorithm=demosaic_algorithm
                    )

                    # Track created file immediately after successful creation
                    created_files.append(output_file)
                    files_dict[mode] = str(output_file)
                    result_files[mode].append(str(output_file))
                    processed_count += 1

                    # Update metadata with conversion results
                    metadata['width'] = data[1][0]
                    metadata['height'] = data[1][1]
                    is_negative = data[0] == NEGATIVE_FILM
                    metadata['is_negative'] = "Negative" if is_negative else "Positive"
                    metadata['film_type'] = is_negative

                except Exception as e:
                    print(tr("ERROR: mode failure {} [{}]: {}").format(
                        input_file.name, mode, e))
                    # ANY error = cleanup ALL and exit
                    cleanup_failed_files(created_files, result_files)
                    return GENERIC_ERROR, {}

            # Store metadata after processing all modes for this file
            ret[metadata['source_file_name']] = metadata


    except KeyboardInterrupt:
        print(tr("ERROR: User interruption"))
        # User interrupted = cleanup ALL and exit
        cleanup_failed_files(created_files, result_files)
        return GENERIC_ERROR, {}
    except Exception as e:
        print(tr("ERROR: Critical conversion error: {}").format(e))
        # Critical error = cleanup ALL and exit
        cleanup_failed_files(created_files, result_files)
        return GENERIC_ERROR, {}

    # SUCCESS: all files processed
    print(tr("Processed files: {}").format(processed_count))
    return GENERIC_OK, ret

def cleanup_failed_files(created_files: List[Path], result_files: Dict[str, List[str]]):
    """
    Clean up files created in current session on error.
    Doesn't touch already existing files.
    """
    for file_path in created_files:
        try:
            if file_path.exists():
                file_path.unlink()
                print(tr("Deleted temporary file: {}").format(file_path.name))
        except Exception as e:
            print(tr("Could not delete temporary file {}: {}").format(file_path.name, e))

def convert_raw(
        input_path: str,
        output_path: str,
        mode: str = "icc",
        demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD,
        check_for_negative = False
) -> tuple[int, tuple[int, int]]:
    """
    Convert single RAW file.

    Args:
        input_path: Path to source RAW file
        output_path: Path to output file
        mode: Conversion mode ("icc", "lut", "cineon", "brk")
        demosaic_algorithm: Demosaic algorithm
    """

    with rawpy.imread(input_path) as raw:

        if mode == "brk":
            # Special mode for bracket analysis: fast processing with linear gamma
            rgb = raw.postprocess(
                gamma=(1, 1),  # linear gamma mandatory for analysis
                no_auto_bright=True,
                output_bps=16,
                output_color=rawpy.ColorSpace.raw,
                use_camera_wb=False,
                use_auto_wb=False,
                demosaic_algorithm=rawpy.DemosaicAlgorithm.LINEAR,  # LINEAR - fastest
                bright=1.0,
                four_color_rgb=False,
                median_filter_passes=0,
                fbdd_noise_reduction=rawpy.FBDDNoiseReductionMode.Off  # OFF
            )

        elif mode == "ICC":
            # For ICC profile: maximum "raw" output
            rgb = raw.postprocess(
                gamma=(1.0, 1.0),  # linear gamma
                no_auto_bright=True,  # no auto-brightness
                output_bps=16,
                output_color=rawpy.ColorSpace.raw,
                use_camera_wb=False,
                use_auto_wb=False,
                demosaic_algorithm=demosaic_algorithm,
                bright=1.0,
                four_color_rgb=False,
                dcb_iterations=0,
                dcb_enhance=False,
                fbdd_noise_reduction=rawpy.FBDDNoiseReductionMode.Off,  # OFF
                median_filter_passes=0
            )

        elif mode == "DCP":
            rgb = raw.postprocess(
                gamma=(1.0, 1.0),  # linear gamma
                no_auto_bright=True,  # no auto-brightness
                output_bps=16,
                output_color=rawpy.ColorSpace.raw,
                use_camera_wb=False,
                use_auto_wb=False,
                demosaic_algorithm=demosaic_algorithm,
                bright=1.0,
                four_color_rgb=False,
                dcb_iterations=0,
                dcb_enhance=False,
                fbdd_noise_reduction=rawpy.FBDDNoiseReductionMode.Off,  # OFF
                median_filter_passes=0,

                # maximal ArgyllCMS compatibility:
                user_wb=[1.0, 1.0, 1.0, 1.0],  # No channal multiplexors
                user_black=None,  # Black Level Auto
                user_sat=None,  # Автоматический уровень насыщения
                noise_thr=None,  # No noize reduction
                chromatic_aberration=(1.0, 1.0),  # No abirations corrections
                bad_pixels_path=None  # Без коррекции битых пикселей
            )

        elif mode == "LUT":
            # For LUT: basic processing
            #rgb = raw.postprocess(
            #    gamma=(2.2, 4.5),  # standard sRGB gamma
            #    no_auto_bright=False,
            #    output_bps=16,
            #    output_color=rawpy.ColorSpace.sRGB,
            #    use_camera_wb=True,
            #    demosaic_algorithm=demosaic_algorithm
            #)
            # Luminar Neo oriented
            rgb = raw.postprocess(
                gamma=(2.2, 2.2),  #  dcraw
                no_auto_bright=False,  # dcraw  auto-brightness
                output_bps=16,  # (dcraw usually 8-bit but Luminar claims 16)
                output_color=rawpy.ColorSpace.sRGB,
                use_camera_wb=True,
                demosaic_algorithm=demosaic_algorithm
            )

        elif mode == "CLG":
            # DXO Style
            rgb = raw.postprocess(
                gamma=(1.0, 1.0),  # Линейная гамма!
                no_auto_bright=True,
                output_bps=16,
                output_color=rawpy.ColorSpace.ProPhoto,  # Широкий gamut
                use_camera_wb=False,  # Нейтральный WB
                demosaic_algorithm=demosaic_algorithm
            )


        elif mode == "Cineon":
            # For LUT under Cineon: log-gamma + linear range
            rgb = raw.postprocess(
                # gamma=(0.6, 0),  # approximate Cineon gamma
                gamma=(1.0, 0),  # Linear gamma для scene-referred
                no_auto_bright=True,
                output_bps=16,
                # output_color=rawpy.ColorSpace.Adobe,
                output_color=rawpy.ColorSpace.ProPhoto,  # Wider gamut
                use_camera_wb=False,
                demosaic_algorithm=demosaic_algorithm
            )

        else:
            print(tr("Unknown mode: {}. Available: 'icc', 'lut', 'cineon', 'bracket'").format(mode))
            return GENERIC_ERROR

        ret_code = POSITIVE_FILM

        if check_for_negative:
            ret_code = detect_negative_fast_numpy(rgb)

        iio.imwrite(output_path, rgb)

        h, w = rgb.shape[:2]
        return (ret_code, (w, h))

def check_cr3_support(file):
    """Проверить поддержку CR3"""
    try:
        # Попытаться открыть CR3 файл
        with rawpy.imread(file) as raw:
            print(f"LibRaw версия: {rawpy.libraw_version}")
            print(f"Размер изображения: {raw.sizes.width}x{raw.sizes.height}")
            print(f"Цветовая модель: {raw.color_desc}")
            return True
    except FileNotFoundError:
        print("Файл CR3 не найден для тестирования")
        return None
    except Exception as e:
        print(f"CR3 не поддерживается: {e}")
        return False


# Usage examples:
if __name__ == "__main__":
    # Example 1: Normal conversion
    try:
        name = "D:/Photo/ColorCh/_R5_2975.CR3"
        check_cr3_support(name)
        count, files = convert_raw_batch(
            input_files=name,
            output_dir="D:/Photo/ColorCh/",
            modes=["brk","lut","icc","cineon"]
        )
        if count == GENERIC_ERROR:
            print(tr("Conversion interrupted due to error"))
        else:
            print(tr("Successfully processed: {} files").format(count))
    except Exception as e:
        print(tr("ERROR: {}").format(e))
        traceback.print_exc()
        print("OMG")


    #count, files = convert_raw_batch(
    #    input_files=["IMG_001.CR3", "IMG_002.CR3", "IMG_003.CR3"],
    #    output_dir="bracket_analysis",
    #    modes="icc"
    #)
    #
    #if count != GENERIC_ERROR:
    #    print(tr("Bracket analysis: processed {} files").format(count))
    #    for mode, file_list in files.items():
    #        print(tr("  Mode {}: {} files").format(mode, len(file_list)))
    #        for tiff_file in file_list:
    #            print(f"    {tiff_file}")
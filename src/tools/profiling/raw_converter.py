import rawpy
import exifread
from fractions import Fraction
import imageio.v3 as iio
import numpy as np
from pathlib import Path
from typing import List, Union, Optional, Dict, Tuple
import glob
from const import GENERIC_ERROR, NEGATIVE_FILM, POSITIVE_FILM

# Qt translation support
def get_translator():
    """Get Qt translator function"""
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            return lambda text, context="RawConverter": app.translate(context, text)
    except ImportError:
        pass
    return lambda text, context="RawConverter": text

# Global translation function
tr = get_translator()


def sanitize_filename(text):
    """Очищаем имя файла от проблемных символов"""
    if not text:
        return "unknown"

    # Заменяем проблемные символы на читабельные
    replacements = {
        '.': '_',  # точка → подчеркивание
        '/': '-',  # слэш → дефис  
        '\\': '-',  # бэкслэш → дефис
        ' ': '_',  # пробел → подчеркивание
        ':': '-',  # двоеточие → дефис
        '*': 'x',  # звездочка → x
        '?': '',  # вопрос → удаляем
        '"': '',  # кавычки → удаляем
        '<': '',  # скобки → удаляем
        '>': '',
        '|': '-',  # труба → дефис
    }

    result = str(text)
    for old, new in replacements.items():
        result = result.replace(old, new)

    return result


def get_extended_metadata(raw_file_path: Path) -> Dict[str, Union[str, float, int, None]]:
    """
    Extract comprehensive metadata from RAW file using exifread.

    Args:
        raw_file_path: Path to RAW file

    Returns:
        Dictionary with extended metadata fields
    """
    try:
        with open(raw_file_path, 'rb') as f:
            tags = exifread.process_file(f, details=True)

            # Helper function to safely extract tag value
            def get_tag_value(tag_name: str, default=None):
                tag = tags.get(tag_name)
                if tag:
                    return str(tag)
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

            # Extract comprehensive metadata
            metadata = {
                # Basic camera info
                'file_path': str(raw_file_path),  # full name with path
                'file_name': raw_file_path.name,  # file name only (nj rich the file if moved)
                'camera_make': get_tag_value('Image Make'),
                'camera_model': get_tag_value('Image Model'),
                'datetime': get_tag_value('EXIF DateTimeOriginal') or get_tag_value('Image DateTime'),

                # Exposure settings
                'exposure_time': get_tag_value('EXIF ExposureTime'),
                'exposure_time_float': fraction_to_float(get_tag_value('EXIF ExposureTime')),
                'f_number': get_tag_value('EXIF FNumber'),
                'f_number_float': fraction_to_float(get_tag_value('EXIF FNumber')),
                'iso': get_tag_value('EXIF ISOSpeedRatings'),
                'exposure_compensation': get_tag_value('EXIF ExposureBiasValue'),
                'exposure_mode': get_tag_value('EXIF ExposureMode'),
                'metering_mode': get_tag_value('EXIF MeteringMode'),
                'flash': get_tag_value('EXIF Flash'),

                # Lens information
                'focal_length': get_tag_value('EXIF FocalLength'),
                'focal_length_35mm': get_tag_value('EXIF FocalLengthIn35mmFilm'),
                'lens_make': get_tag_value('EXIF LensMake'),
                'lens_model': get_tag_value('EXIF LensModel'),
                'max_aperture': get_tag_value('EXIF MaxApertureValue'),

                # White balance and color
                'white_balance': get_tag_value('EXIF WhiteBalance'),
                'white_balance_int': get_tag_value('EXIF WhiteBalance'),
                'color_space': get_tag_value('EXIF ColorSpace'),
                'scene_type': get_tag_value('EXIF SceneType'),
                'scene_capture_type': get_tag_value('EXIF SceneCaptureType'),
                'saturation': get_tag_value('EXIF Saturation'),
                'sharpness': get_tag_value('EXIF Sharpness'),
                'contrast': get_tag_value('EXIF Contrast'),

                # Advanced exposure info
                'exposure_program': get_tag_value('EXIF ExposureProgram'),
                'aperture_value': get_tag_value('EXIF ApertureValue'),
                'shutter_speed_value': get_tag_value('EXIF ShutterSpeedValue'),
                'subject_distance': get_tag_value('EXIF SubjectDistance'),
                'digital_zoom_ratio': get_tag_value('EXIF DigitalZoomRatio'),

                # Addon fields
                # Size
                'width': 0,
                'height': 0,

                # Nagative/positive film
                'is_negative': False,  # bool для логики
                'film_type': 'positive',  # строка для UI

                # Processing info
                'source_file_path': str(raw_file_path),  # full name with path
                'source_file_name': raw_file_path.name,  # file name only (nj rich the file if moved)
                'output_files': {},  # result files
                'modes_processed': [],  # processing modes
            }

            return metadata

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


def convert_raw_batch(
        input_files: Union[str, List[str]],
        output_dir: str = "",
        modes: Union[str, List[str]] = "icc",
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
        Tuple[int, Dict[str, List[str]]]: (number of processed files or GENERIC_ERROR on error,
                                         dictionary {mode: [tiff_file_paths]})
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

            for mode in modes_list:
                try:
                    # Determine output directory for this file
                    current_output_dir = base_output_path if base_output_path else input_file.parent

                    # Form output filename
                    wb_temp = sanitize_filename(metadata.get('white_balance', 'auto'))
                    f_number = metadata.get('f_number_float', 0)
                    exp_time = metadata.get('exposure_time_float', 0)
                    camera_model = sanitize_filename(metadata.get('camera_model', 'unknown'))

                    base_name = f"{input_file.stem}_{mode}_{wb_temp}_{f_number}-{exp_time}_{camera_model}"
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
    return processed_count, ret

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
                demosaic_algorithm=0,  # LINEAR - fastest
                bright=1.0,
                four_color_rgb=False,
                median_filter_passes=0,
                fbdd_noise_reduction=0  # OFF
            )

        elif mode == "icc":
            # For ICC profile: maximum "raw" output
            rgb = raw.postprocess(
                gamma=(1, 1),  # linear gamma
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
                fbdd_noise_reduction=0,  # OFF
                median_filter_passes=0
            )

        elif mode == "lut":
            # For LUT: basic processing
            rgb = raw.postprocess(
                gamma=(2.2, 4.5),  # standard sRGB gamma
                no_auto_bright=False,
                output_bps=16,
                output_color=rawpy.ColorSpace.sRGB,
                use_camera_wb=True,
                demosaic_algorithm=demosaic_algorithm
            )

        elif mode == "cineon":
            # For LUT under Cineon: log-gamma + linear range
            rgb = raw.postprocess(
                gamma=(0.6, 0),  # approximate Cineon gamma
                no_auto_bright=True,
                output_bps=16,
                output_color=rawpy.ColorSpace.Adobe,
                use_camera_wb=True,
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


# Usage examples:
if __name__ == "__main__":
    # Example 1: Normal conversion
    count, files = convert_raw_batch(
        input_files="*.CR3",
        output_dir="converted",
        modes=["icc", "lut"]
    )
    if count == GENERIC_ERROR:
        print(tr("Conversion interrupted due to error"))
    else:
        print(tr("Successfully processed: {} files").format(count))

    count, files = convert_raw_batch(
        input_files=["IMG_001.CR3", "IMG_002.CR3", "IMG_003.CR3"],
        output_dir="bracket_analysis",
        modes="icc"
    )

    if count != GENERIC_ERROR:
        print(tr("Bracket analysis: processed {} files").format(count))
        for mode, file_list in files.items():
            print(tr("  Mode {}: {} files").format(mode, len(file_list)))
            for tiff_file in file_list:
                print(f"    {tiff_file}")

from pathlib import Path
from typing import Dict, Union
import traceback
import tifffile


def tr(text: str) -> str:
    """Translation function placeholder for Qt6 internationalization"""
    return text

def get_tiff_scanner_metadata(tiff_file_path: Path) -> Dict[str, Union[str, float, int, bool, None]]:
    """
    Extract comprehensive metadata from TIFF file for scanner profiling using tifffile.

    Collects all necessary data for creating ICC scanner profile:
    - Scanner identification (Make, Model, Software)
    - Technical parameters (resolution, bit depth, compression)
    - Colour characteristics (color space, gamma, ICC profile)
    - Validation data for profile quality

    Args:
        tiff_file_path: Path to TIFF file

    Returns:
        Dictionary with scanner metadata fields optimised for ICC profile creation
    """
    try:

        # Helper function to safely extract tag value
        def get_tag_value(tags_dict, tag_name: str, default=None):
            """Safe tag value extraction"""
            try:
                return tags_dict.get(tag_name, default)
            except:
                return default

        # Helper function to convert fraction to float
        def fraction_to_float(value) -> float:
            """Convert fraction to float"""
            if value is None:
                return 0.0
            try:
                if isinstance(value, (tuple, list)) and len(value) == 2:
                    return float(value[0]) / float(value[1]) if value[1] != 0 else 0.0
                elif isinstance(value, (int, float)):
                    return float(value)
                return 0.0
            except:
                return 0.0

        # Helper function for compression analysis
        def analyze_compression(compression_value):
            """Compression type analysis"""
            compression_map = {
                1: 'None',
                2: 'CCITT Group 3',
                3: 'CCITT Group 4',
                5: 'LZW',
                7: 'JPEG',
                8: 'Adobe Deflate',
                32773: 'PackBits'
            }

            compression_name = compression_map.get(compression_value, f'Unknown({compression_value})')
            is_lossless = compression_value in [1, 5, 8, 32773]  # Lossless compression

            return compression_name, is_lossless

        # Helper function for linear/non-linear data detection
        def detect_gamma_processing(tags, color_space, bit_depth):
            """Detection of applied gamma correction"""

            gamma_sources = []

            # 1. From TIFF tags TransferFunction or Gamma
            if 'TransferFunction' in tags:
                gamma_sources.append(('transfer_function', 2.2))  # Usually indicates gamma

            # 2. From colour space ColorSpace tag
            colorspace_tag = tags.get('ColorSpace', 0)
            if colorspace_tag == 1:  # sRGB
                gamma_sources.append(('srgb_space', 2.2))

            # 3. Heuristic based on bit depth
            if bit_depth == 8:
                gamma_sources.append(('8bit_heuristic', 2.2))  # Usually gamma corrected
            elif bit_depth == 16:
                gamma_sources.append(('16bit_heuristic', 1.0))  # More often linear

            return gamma_sources

        # Read TIFF with complete metadata
        with tifffile.TiffFile(tiff_file_path) as tif:

            # Get first page (main image)
            page = tif.pages[0]

            # Extract tags
            tags = page.tags

            # Basic image parameters
            width = page.imagewidth
            height = page.imagelength
            bit_depth = page.bitspersample
            samples_per_pixel = page.samplesperpixel

            # If bit_depth is a list, take maximum value
            if isinstance(bit_depth, (tuple, list)):
                bit_depth = max(bit_depth)

            # Compression analysis
            compression_value = page.compression.value if hasattr(page.compression, 'value') else page.compression
            compression_name, is_lossless = analyze_compression(compression_value)

            # Resolution
            x_resolution = fraction_to_float(getattr(page, 'xresolution', None))
            y_resolution = fraction_to_float(getattr(page, 'yresolution', None))
            resolution_unit = getattr(page, 'resolutionunit', 2)  # 2=inches, 3=cm

            # Photometric interpretation
            photometric = page.photometric.value if hasattr(page.photometric, 'value') else page.photometric
            color_space = 'unknown'
            if photometric == 2:
                color_space = 'RGB'
            elif photometric == 5:
                color_space = 'CMYK'
            elif photometric == 1:
                color_space = 'Grayscale'
            elif photometric == 0:
                color_space = 'WhiteIsZero'

            # Search for ICC profile
            icc_profile_present = False
            icc_profile_size = 0
            try:
                if 'ICC Profile' in tags:
                    icc_profile_present = True
                    icc_profile_size = len(tags['ICC Profile'].value)
                elif hasattr(page, 'colormap') and page.colormap is not None:
                    # Colour map present
                    pass
            except:
                pass

            # Gamma processing detection
            gamma_info = detect_gamma_processing(tags, color_space, bit_depth)

            # Create warnings list
            warnings = []

            # Data validation for profiling
            if compression_name != 'None':
                warnings.append(tr(f"COMPRESSION: {compression_name} - possible accuracy loss"))

            if bit_depth < 16:
                warnings.append(tr(f"BIT DEPTH: {bit_depth}bit - 16bit recommended for accuracy"))

            if icc_profile_present:
                warnings.append(tr("ICC PROFILE: Embedded profile detected - may affect data"))

            if any(source[1] != 1.0 for source in gamma_info if source[1]):
                warnings.append(tr("GAMMA: Possible gamma correction detected - data not linear"))

            # Data quality assessment for profiling
            is_suitable_for_profiling = (
                    bit_depth >= 16 and
                    compression_name == 'None' and
                    not icc_profile_present and
                    color_space == 'RGB'
            )

            # Data quality score (0-100)
            quality_score = 100
            if bit_depth < 16:
                quality_score -= 30
            if compression_name != 'None':
                quality_score -= 20
            if icc_profile_present:
                quality_score -= 15
            if any(source[1] != 1.0 for source in gamma_info if source[1]):
                quality_score -= 25
            quality_score = max(0, quality_score)

            # Recommendation
            if is_suitable_for_profiling:
                recommendation = tr("Excellent data for profiling")
            elif not warnings:
                recommendation = tr("Acceptable data for profiling")
            elif len(warnings) <= 2:
                recommendation = tr("Data requires correction before profiling")
            else:
                recommendation = tr("Data not suitable for accurate profiling - rescanning recommended")

            # Assemble final metadata dictionary
            metadata = {
                # === SCANNER IDENTIFICATION ===
                'scanner_make': get_tag_value(tags, 'Make'),
                'scanner_model': get_tag_value(tags, 'Model'),
                'software': get_tag_value(tags, 'Software'),
                'datetime': get_tag_value(tags, 'DateTime'),

                # === TECHNICAL PARAMETERS ===
                'width': width,
                'height': height,
                'bit_depth': bit_depth,
                'samples_per_pixel': samples_per_pixel,
                'photometric_interpretation': photometric,

                # === RESOLUTION ===
                'x_resolution': x_resolution,
                'y_resolution': y_resolution,
                'resolution_unit': 'inches' if resolution_unit == 2 else 'cm' if resolution_unit == 3 else 'unknown',
                'dpi_x': x_resolution if resolution_unit == 2 else x_resolution * 2.54 if resolution_unit == 3 else 0,
                'dpi_y': y_resolution if resolution_unit == 2 else y_resolution * 2.54 if resolution_unit == 3 else 0,

                # === COMPRESSION ===
                'compression': compression_name,
                'compression_code': compression_value,
                'is_lossless': is_lossless,

                # === COLOUR CHARACTERISTICS ===
                'color_space': color_space,
                'icc_profile_present': icc_profile_present,
                'icc_profile_size': icc_profile_size,

                # === GAMMA ANALYSIS ===
                'gamma_sources': gamma_info,
                'likely_gamma': gamma_info[0][1] if gamma_info else 1.0,
                'gamma_confidence': 'high' if len(gamma_info) > 1 else 'medium' if gamma_info else 'low',

                # === DATA QUALITY ===
                'is_linear': all(source[1] == 1.0 for source in gamma_info if source[1]),
                'is_suitable_for_profiling': is_suitable_for_profiling,
                'data_warnings': warnings,
                'quality_score': quality_score,

                # === FILE INFORMATION ===
                'source_file_path': str(tiff_file_path),
                'source_file_name': tiff_file_path.name,
                'file_size_mb': tiff_file_path.stat().st_size / (1024 * 1024),

                # === ADDITIONAL TIFF TAGS ===
                'orientation': get_tag_value(tags, 'Orientation'),
                'planar_configuration': get_tag_value(tags, 'PlanarConfiguration'),
                'artist': get_tag_value(tags, 'Artist'),
                'copyright': get_tag_value(tags, 'Copyright'),
                'document_name': get_tag_value(tags, 'DocumentName'),
                'image_description': get_tag_value(tags, 'ImageDescription'),

                # === PROFILING ===
                'needs_gamma_correction': not all(source[1] == 1.0 for source in gamma_info if source[1]),
                'recommended_action': recommendation,
            }

            return metadata

    except ImportError as e:
        print(tr(f"Error: tifffile library not available: {e}"))
        print(tr("Install with: pip install tifffile"))
        return {}
    except Exception as e:
        print(tr(f"Error reading TIFF metadata from {tiff_file_path}: {e}"))
        return {}


def debug_tiff_tags(filename):
    """
    Debug function to examine all TIFF tags in detail
    """
    import tifffile

    test_file_path = Path(filename)

    try:
        with tifffile.TiffFile(test_file_path) as tif:
            page = tif.pages[0]
            tags = page.tags

            print("=== ALL TIFF TAGS ===")
            for tag_name, tag in tags.items():
                try:
                    value = tag.value if hasattr(tag, 'value') else str(tag)
                    # Truncate very long values
                    if isinstance(value, (str, bytes)) and len(str(value)) > 100:
                        display_value = str(value)[:100] + "..."
                    else:
                        display_value = value
                    print(f"{tag_name} ({tag.code}): {display_value}")
                except Exception as e:
                    print(f"{tag_name} ({tag.code}): <ERROR: {e}>")

            print("\n=== SPECIFIC SCANNER-RELATED TAGS ===")
            scanner_tags = [
                'Make', 'Model', 'Software', 'Artist', 'Copyright',
                'ImageDescription', 'DocumentName', 'HostComputer',
                'TargetPrinter', 'PageName'
            ]

            for tag_name in scanner_tags:
                if tag_name in tags:
                    try:
                        value = tags[tag_name].value
                        print(f"{tag_name}: {value}")
                    except:
                        print(f"{tag_name}: <extraction error>")
                else:
                    print(f"{tag_name}: <not present>")

    except Exception as e:
        print(f"Error reading TIFF: {e}")



def _test_tiff_metadata_reader():
    """
    Test function to read and display metadata from a specific TIFF file.

    Tests the get_tiff_scanner_metadata function with a sample file and
    prints all extracted metadata as raw dictionary content.
    """
    test_file_path = Path(
        r"D:\0GitHub\flab-DIY-stack\src\tools\profiling\demo_project\ColorSmall\bak\IMG_20250731_0003.tif")

    print(tr("Testing TIFF metadata reader..."))
    print(tr(f"File: {test_file_path}"))
    print("-" * 80)

    # Check if file exists
    if not test_file_path.exists():
        print(tr(f"ERROR: File not found: {test_file_path}"))
        return

    # Read metadata
    try:
        metadata = get_tiff_scanner_metadata(test_file_path)

        if not metadata:
            print(tr("ERROR: No metadata extracted"))
            return

        # Print raw dictionary content
        import pprint

        print(tr("=== RAW METADATA DICTIONARY ==="))
        pprint.pprint(metadata, width=120, depth=None)

        print("-" * 80)
        print(tr("Test completed successfully!"))

        debug_tiff_tags(test_file_path)

    except Exception as e:
        print(tr(f"ERROR during metadata extraction: {e}"))
        print(tr(f"Traceback: {traceback.format_exc()}"))
        return None




# Run test if this file is executed directly
if __name__ == "__main__":
    _test_tiff_metadata_reader()
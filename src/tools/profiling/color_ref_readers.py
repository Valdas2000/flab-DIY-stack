import traceback
import locale
from datetime import datetime
from ti3_calcs import chromatic_adaptation_brdf, illuminants, normalize_patch_data
import numpy as np
from colour import Lab_to_XYZ, XYZ_to_xy, xy_to_CCT

from pyparsing import results

from const import GENERIC_OK, GENERIC_ERROR
from typing import Dict, Optional, Any
import time

def tr(text):
    """
    Translation stub function for AT5 internationalisation.
    Replace this with your actual translation implementation.
    """
    return text


xy_to_CCT_Hernandez1999 = xy_to_CCT


def detect_illuminant_from_patches(patches):

    illuminants = {
        'D65': [95.047, 100.000, 108.883],
        'D50': [96.422, 100.000, 82.521],
        'C': [98.074, 100.000, 118.232],
        'A': [109.850, 100.000, 35.585],
        'E': [100.000, 100.000, 100.000]
    }

    # Найти белый патч
    white_patch = None
    for patch in patches:
        lab = patch['lab_target']
        if lab[0] > 90 and abs(lab[1]) < 5 and abs(lab[2]) < 5:
            white_patch = lab
            break

    if not white_patch:
        return None

    best_illuminant = None
    min_error = float('inf')

    for ill_name, ill_xyz in illuminants.items():
        # ИДЕЯ: если белый патч снят при этом освещении,
        # то LAB→XYZ с этим illuminant даст координаты близкие к (100,100,100)

        xyz = Lab_to_XYZ(white_patch, ill_xyz)

        # Для белого патча ожидаем XYZ близкие к illuminant
        # Нормализуем относительно Y=100
        xyz_norm = [xyz[0] / xyz[1] * 100, 100, xyz[2] / xyz[1] * 100]

        # Ошибка от идеального белого при данном освещении
        error = ((xyz_norm[0] - ill_xyz[0]) ** 2 +
                 (xyz_norm[1] - ill_xyz[1]) ** 2 +
                 (xyz_norm[2] - ill_xyz[2]) ** 2) ** 0.5

        if error < min_error:
            min_error = error
            best_illuminant = ill_xyz

    print(f"\nЛучший illuminant с ошибкой {min_error:.2f}")
    return best_illuminant

def add_xyz_targets(patches, illuminant_xy):
    """
    Преобразует LAB в XYZ и добавляет в исходные данные.
    Мутирует массив patches - добавляет ключ 'xyz_target'.

    Args:
        patches: список словарей с ключом 'lab_target'
        illuminant_xy: координаты источника освещения [x, y]
    """
    for patch in patches:
        lab = np.array(patch['lab_target'])
        xyz = Lab_to_XYZ(lab, illuminant_xy)
        patch['xyz_target'] = xyz.tolist()


def write_txt2ti3_patches(patches, field_to_output, input_cgats_filename, output_filename):
    """Write patches to txt2ti3 format maintaining original file sequence"""
    # check input_cgats_filename extension to ti2
    use_sample_id_as_number = False
    if input_cgats_filename.split('.')[-1] == 'ti2':
        use_sample_id_as_number = True

    patch_sequence, xyz, patch_loc = _get_patch_names(input_cgats_filename)
    with_zero, without_zero = _create_patch_name_variants(patch_sequence)
    the_list = with_zero

    is_ok = True
    for val in the_list:
        if val not in patches.keys():
            is_ok = False
            break
    if not is_ok:
        is_ok = True
        the_list = without_zero
        for val in the_list:
            if val not in patches.keys():
                is_ok = False
                break
        if not is_ok:
            print("ERROR: Key schemas of measurements and reference are not compatible")
            return GENERIC_ERROR

    rgb_array = []
    stdev=[]
    for patch_name in the_list:
        rgb_array.append(patches[patch_name][field_to_output])
        stdev.append(patches[patch_name]['std_rgb'])

    xyz_d50 = xyz

    target_white = np.array([95.106486, 100.000000, 108.844025])


    rgb_100, stdev_100 = normalize_patch_data(rgb_array, stdev, xyz_d50, 100,  target_white)
    outp = []
    for i, patch_name in enumerate(the_list):
        #sample_id = patch_loc[i] if use_sample_id_as_number else patch_sequence[i]
        #sample_id = patch_sequence[i]
        outp.append({
            'SAMPLE_ID': patch_loc[i],   # A1 A2 A3 or 1 2 3
            'SAMPLE_LOC': patch_sequence[i],
            'XYZ': xyz_d50[i],
            'RGB': rgb_100[i],
            'STDEV': stdev_100[i]
        })
    #_export_patches_for_txt2ti3(outp, output_filename, is_rgb=True)
    #_export_patches_for_txt2ti3(outp, 'xyz.cie', is_rgb=False)
    create_camera_ti3_d50(outp, output_filename)

    return

# XYZ значения должны быть в D50!
def create_camera_ti3_d50(patch_data, output_filename):
    try:
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'English_United States.1252')  # Windows
        except locale.Error:
            locale.setlocale(locale.LC_TIME, 'C')  # Fallback

    current_time = datetime.now().strftime("%a %b %d %H:%M:%S %Y")

    with (open(output_filename, 'w') as f):
        header = f"""CTI3
DESCRIPTOR "Argyll Calibration Target chart information 3"
ORIGINATOR "PatchReader flab-DIY-stack"
CREATED "{current_time}"
DEVICE_CLASS "INPUT"
COLOR_REP "XYZ_RGB"

NUMBER_OF_FIELDS 11
BEGIN_DATA_FORMAT
SAMPLE_ID SAMPLE_LOC XYZ_X XYZ_Y XYZ_Z RGB_R RGB_G RGB_B STDEV_R STDEV_G STDEV_B 
END_DATA_FORMAT
"""
        f.write(header)
        f.write(f'\nNUMBER_OF_SETS {len(patch_data)}\n')
        f.write('BEGIN_DATA\n')

        # Patch data
        for patch in patch_data:
            p_color = patch['RGB']
            x_color = patch['XYZ']
            stdev = patch['STDEV']

            f.write(
                    f"{patch['SAMPLE_ID']} "
                    f'{patch['SAMPLE_LOC']} '
                    f"{x_color[0]:.5f} "
                    f"{x_color[1]:.5f} "
                    f"{x_color[2]:.5f} "
                    f"{p_color[0]:.5f} "
                    f"{p_color[1]:.5f} "
                    f"{p_color[2]:.5f} "
                    f"{stdev[0]:.5f} "
                    f"{stdev[1]:.5f} "
                    f"{stdev[2]:.5f} "
                    f"\n"
                    )

        f.write('END_DATA\n')



def _create_patch_name_variants(patch_names):
    """
    Создает два варианта списка имен патчей: с ведущим нулем и без него

    Args:
        patch_names: список имен патчей (например: ['A1', 'B2', 'C3'])

    Returns:
        tuple: (with_zero, without_zero)
               with_zero: ['A01', 'B02', 'C03']
               without_zero: ['A1', 'B2', 'C3']
    """
    with_zero = []
    without_zero = []

    for name in patch_names:
        letter = name[0]
        number = int(name[1:])

        with_zero.append(f"{letter}{number:02d}")
        without_zero.append(f"{letter}{number}")

    return with_zero, without_zero

def _export_patches_for_txt2ti3( patch_data, output_filename, is_rgb=True):
    """Export RGB patches to txt2ti3 compatible format"""


    # Запись в файл
    with open(output_filename, 'w') as f:
        # CGATS header

        f.write('CGATS.17\n')
        if is_rgb:
            f.write('COLOR_REP "RGB"\n')
        else:
            f.write('COLOR_REP "XYZ"\n')
        f.write('\n')
        f.write('NUMBER_OF_FIELDS 4\n')
        f.write('BEGIN_DATA_FORMAT\n')
        if is_rgb:
            f.write('SAMPLE_ID RGB_R RGB_G RGB_B\n')
        else:
            f.write('SAMPLE_ID XYZ_X XYZ_Y XYZ_Z\n')
        f.write('END_DATA_FORMAT\n')
        f.write('\n')
        f.write(f'NUMBER_OF_SETS {len(patch_data)}\n')
        f.write('BEGIN_DATA\n')

        # Patch data
        for patch in patch_data:
            if is_rgb:
                p_color = patch['RGB']
            else:
                p_color = patch['XYZ']
            f.write(f"{patch['SAMPLE_ID']} {p_color[0]:.3f} "
                    f"{p_color[1]:.5f} {p_color[2]:.5f}\n")

        f.write('END_DATA\n')

def _get_patch_names(cgats_filename):
    """Extract patch names maintaining file order"""
    result = parse_cgats_file(cgats_filename)
    xyz = None
    if 'xyz_target' in result['patches'][0].keys():
        xyz = [result['xyz_target'] for result in result['patches']]
    elif 'lab_target' in result['patches'][0].keys():
        illuminant_xyz = detect_illuminant_from_patches(result['patches'])
        add_xyz_targets(result['patches'], illuminant_xyz)
        xyz = [result['xyz_target'] for result in result['patches']]

    return [result['patch_id'] for result in result['patches']], xyz, [str(result.get('sample_loc',0)) for result in result['patches']]

def parse_cgats_file(cgats_filename) -> dict[str: any]:
    """
    Universal CGATS file parser with automatic column detection.

    Supports:
    - X-Rite: Sample_NAME, SAMPLE_NAME, Lab_L, Lab_a, Lab_b
    - Argyll: SAMPLE_ID, SAMPLE_LOC, LAB_L, LAB_A, LAB_B
    - Mixed formats with incorrect data ordering
    """
    patches = []

    # Data structure
    data_format = {}
    column_names = []
    in_data_format = False
    in_data = False

    # File type detection
    file_ext = cgats_filename.lower().split('.')[-1]
    file_type = file_ext if file_ext in ['ti2', 'ti3', 'cie'] else 'cgats'

    with open(cgats_filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # Parse data format section
            if line == 'BEGIN_DATA_FORMAT':
                in_data_format = True
                continue

            if line == 'END_DATA_FORMAT':
                in_data_format = False
                for i, col_name in enumerate(column_names):
                    data_format[col_name] = i
                continue

            if in_data_format and line:
                column_names = line.split()
                continue

            # Parse data section
            if line == 'BEGIN_DATA':
                in_data = True
                continue

            if line == 'END_DATA':
                break

            if in_data and line:
                parts = line.split()

                if len(parts) < len(column_names):
                    continue

                # Universal patch ID extraction
                patch_id = None
                sample_loc = None
                path_number = None

                # Search for patch ID using various naming conventions
                for id_variant in ['SAMPLE_ID', 'Sample_NAME', 'SAMPLE_NAME']:
                    if id_variant in data_format:
                        idx = data_format[id_variant]
                        value = parts[idx].strip('"')

                        # Determine if this is an ID or a number
                        if value.isdigit():
                            # This is a number - data might be mixed up
                            sample_loc = value
                        else:
                            # This is a text ID
                            patch_id = value
                        break

                # Search for SAMPLE_LOC if present
                if 'SAMPLE_LOC' in data_format:
                    idx = data_format['SAMPLE_LOC']
                    loc_value = parts[idx].strip('"')

                    if loc_value.isdigit():
                        sample_loc = loc_value
                    else:
                        # SAMPLE_LOC contains text - this is the actual ID
                        if not patch_id:  # If ID hasn't been found yet
                            patch_id = loc_value

                # Skip if ID still not found
                if not patch_id:
                    continue

                # Skip technical records
                if patch_id in ['0', '00']:
                    continue

                # Create patch data
                patch_data = {'patch_id': patch_id}

                if sample_loc:
                    patch_data['sample_loc'] = sample_loc

                # RGB values (standard naming)
                if all(col in data_format for col in ['RGB_R', 'RGB_G', 'RGB_B']):
                    patch_data['rgb_reference'] = [
                        float(parts[data_format['RGB_R']]),
                        float(parts[data_format['RGB_G']]),
                        float(parts[data_format['RGB_B']])
                    ]

                # XYZ values (standard naming)
                if all(col in data_format for col in ['XYZ_X', 'XYZ_Y', 'XYZ_Z']):
                    patch_data['xyz_target'] = [
                        float(parts[data_format['XYZ_X']]),
                        float(parts[data_format['XYZ_Y']]),
                        float(parts[data_format['XYZ_Z']])
                    ]

                # LAB values - universal search
                lab_variants = [
                    ['LAB_L', 'LAB_A', 'LAB_B'],  # Argyll
                    ['Lab_L', 'Lab_a', 'Lab_b'],  # X-Rite variant 1
                    ['Lab_L', 'Lab_A', 'Lab_B']  # X-Rite variant 2
                ]

                for lab_cols in lab_variants:
                    if all(col in data_format for col in lab_cols):
                        try:
                            # Handle commas as decimal separators
                            lab_values = []
                            for col in lab_cols:
                                val_str = parts[data_format[col]].replace(',', '.')
                                lab_values.append(float(val_str))

                            patch_data['lab_target'] = lab_values
                            break
                        except ValueError:
                            continue

                patches.append(patch_data)

    return {
        'patches': patches,
        'format': column_names,
        'file_type': file_type,
        'total_columns': len(column_names),
        'detected_format': _detect_format_type(column_names)
    }


def _detect_format_type(column_names):
    """Detect format type by column names"""
    cols_str = ' '.join(column_names).upper()

    if 'SAMPLE_NAME' in cols_str:
        return 'X-Rite'
    elif 'SAMPLE_ID' in cols_str and 'SAMPLE_LOC' in cols_str:
        return 'Argyll'
    elif 'LAB_' in cols_str:
        return 'Standard CGATS'
    else:
        return 'Unknown'


def analyse_file_format(cgats_filename):
    """
    Analyse file format with diagnostic information
    """
    print(tr(f"Analysing format: {cgats_filename}"))
    print("=" * 60)

    result = parse_cgats_file(cgats_filename)
    patches = result['patches']

    print(tr(f"Detected format: {result['detected_format']}"))
    print(tr(f"Columns: {' | '.join(result['format'])}"))
    print(tr(f"Successfully parsed patches: {len(patches)}"))

    if patches:
        print(tr("\nFirst 3 patches:"))
        for i, patch in enumerate(patches[:3]):
            output = tr(f"  {i + 1}. ID: '{patch['patch_id']}'")
            if 'sample_loc' in patch:
                output += tr(f" (position: {patch['sample_loc']})")
            if 'lab_measured' in patch:
                lab = patch['lab_measured']
                output += tr(f" LAB: [{lab[0]:.2f}, {lab[1]:.2f}, {lab[2]:.2f}]")
            print(output)

    print("=" * 60)
    return result


def get_patch_names_universal(cgats_filename):
    """
    Universal patch name extraction for any format

    Works with:
    - X-Rite: Sample_NAME -> ['A1', 'A2', 'A3', ...]
    - Argyll: SAMPLE_ID -> ['H6', 'M10', 'A01', ...]
    - Mixed: correctly identifies ID vs number
    """
    result = parse_cgats_file(cgats_filename)
    patches = result['patches']

    # Extract names - identical for all formats
    patch_names = [patch['patch_id'] for patch in patches]

    print(tr(f"Format: {result['detected_format']}"))
    print(tr(f"Patches found: {len(patch_names)}"))
    print(tr(f"First 10: {patch_names[:10]}"))

    return patch_names

import platform
from typing import List, Tuple, Optional, Callable
from background_process import BackgroundProcessManager
import tempfile
import os
from PySide6.QtWidgets import QApplication


def save_to_cgats_cie_file(data_list: list[dict], metadata: dict, filename: str) -> None:
    """
    Creates CGATS.17 CIE file for camera profiling from spectrophotometer data.

    Args:
        data_list: List of dictionaries containing patch data with:
                  - lab_reference_m: tuple of (L, A, B) values
                  - patch_id: patch identifier
        metadata: Dictionary with metadata for CGATS header
        filename: Output .cie file name
    """

    # Validate input data
    if not data_list:
        raise ValueError("Data list cannot be empty")

    # Validate LAB data from xicclu
    for i, item in enumerate(data_list):
        if 'lab_reference_m' not in item or 'patch_id' not in item:
            raise ValueError(f"Missing required fields in record {i}")

        lab = item['lab_reference_m']
        if not isinstance(lab, (tuple, list)) or len(lab) != 3:
            raise ValueError(f"Invalid LAB data format in record {i}: {lab}")

        L, A, B = lab
        if not all(isinstance(val, (int, float)) for val in lab):
            raise ValueError(f"LAB values must be numbers in record {i}: {lab}")

        if not (0 <= L <= 100):
            raise ValueError(f"L value outside range 0-100 in record {i}: L={L}")

    # Create CGATS file
    with open(filename, 'w', encoding='utf-8') as f:
        # CGATS header
        f.write("CGATS.17\n")

        # Write metadata
        for key, value in metadata.items():
            f.write(f'{key} "{value}"\n')

        f.write("\n")

        # Data format section
        f.write("NUMBER_OF_FIELDS 4\n")
        f.write("BEGIN_DATA_FORMAT\n")
        f.write("SAMPLE_ID LAB_L LAB_A LAB_B\n")
        f.write("END_DATA_FORMAT\n")
        f.write("\n")

        # Number of records
        f.write(f"NUMBER_OF_SETS {len(data_list)}\n")
        f.write("BEGIN_DATA\n")

        # Write patch data (preserve original order!)
        for item in data_list:
            patch_id = item['patch_id']
            L, A, B = item['lab_reference_m']

            # Format LAB values with 5 decimal places
            f.write(f"{patch_id} {L:.5f} {A:.5f} {B:.5f}\n")

        f.write("END_DATA\n")


def run_xicclu_with_background(
        data: List[Dict[str,Any]],
        profile_path: str,
        input_file: str,
):
    """Запуск xicclu через BackgroundProcessManager."""

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    results = []
    manager = BackgroundProcessManager(app)
    manager.use_loading_dialog = False

    # Формируем команду в зависимости от ОС

    cmd = ['xicclu', '-v0', '-ir', '-pl', '-s255', profile_path]

    def parse_xicclu_output(return_code: int, stdout: str, stderr: str):
        """Парсинг вывода xicclu в список кортежей."""
        if return_code == 0:
            for line in stdout.strip().split('\n'):
                line = line.strip()
                if line:
                    try:
                        parts = line.split()
                        if len(parts) >= 3:
                            results.append((float(parts[0]), float(parts[1]), float(parts[2])))
                    except ValueError:
                        continue

    def on_error(error: str):
        print(f"Ошибка выполнения: {error}")

    with open(input_file, 'r', encoding='utf-8') as f:
        manager.stdin_handle = f
        manager.execute_command(
            cmd=cmd,
            message="Выполнение xicclu...",
            timeout=300,
            on_success= parse_xicclu_output,
            on_error=on_error
        )

        while manager.is_running():
            QApplication.processEvents()  # Обновляем UI
            time.sleep(0.15)  # 50ms пауза

        for idx, result in enumerate(results):
            data[idx]['lab_reference_m'] = result

def update_lab_data(ti3_data: List[Any], path_to_paper_profile:str) -> None:
    try:
        temp_fd, temp_filename = tempfile.mkstemp(suffix='.txt', prefix='lab_data_')
        with os.fdopen(temp_fd, 'w') as f:
            for item in ti3_data:
                r, g, b = item['rgb_reference'][0], item['rgb_reference'][1], item['rgb_reference'][2]
                f.write(f"{r} {g} {b}\n")

        run_xicclu_with_background(
            ti3_data,
            profile_path=path_to_paper_profile,
            input_file=temp_filename,
        )

        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    except Exception as e:
        print(f"Error: int labB: {e}")
        traceback.print_exc()

def make_lab_data(ti3_data: List[Any], input_ti3_file:str, cht_data) -> None:
    try:
        result = analyse_file_format(input_ti3_file)

        for i, item in enumerate(ti3_data):
            cht_record = cht_data[item['patch_id']]
            item['lab_reference_m'] =  cht_record['lab_reference']
            item['xyz_reference_m'] = cht_record['xyz_reference']

    except Exception as e:
        print(f"Error: int labB: {e}")
        traceback.print_exc()

# Testing all file formats
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                 QComboBox, QTextEdit, QPushButton, QFileDialog,
                                 QMessageBox, QApplication, QCheckBox)

    app = QApplication(sys.argv)


    test_files = [
        "D:/0GitHub/flab-DIY-stack/src/tools/profiling/demo_project/tst_ref.ti3",  # Sample_NAME, Lab_L, Lab_a, Lab_b
    ]
    for filename in test_files:
        try:
            profile_path = "D:/0GitHub/flab-DIY-stack/src/tools/profiling/demo_project/FOMEI_Baryta_MONO_290_PIXMA_G540_PPPL_HQ_RB4.icm"
            input_file = "D:/0GitHub/flab-DIY-stack/src/tools/profiling/demo_project/rgb_ref.txt"

            result = analyse_file_format(filename)
            update_lab_data(result['patches'], profile_path, input_file)

            print(result)
        except FileNotFoundError:
            print(tr(f"File {filename} not found"))
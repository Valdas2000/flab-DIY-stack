
import struct
import json
import datetime
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import ConvexHull

from patch_calcs import expected_artifact_quality  # Твоя система!

from colour.difference import delta_E_CIE2000
import colour

def compare_camera_to_standard(camera_wb_dict, best_illuminant):
    """
    Сравнивает WB камеры со стандартным источником

    Args:
        camera_wb_dict: словарь с данными камеры
        best_illuminant: ID стандартного источника из библиотеки

    Returns:
        dict: исходный словарь + best_illuminant + camera_relevance
    """

    # Получаем температуру стандартного источника
    illuminant_xy = colour.CCS_ILLUMINANTS['CIE 1931 2 Degree Standard Observer'][best_illuminant]
    standard_temp = colour.temperature.xy_to_CCT_Hernandez1999(illuminant_xy)

    # Температура камеры
    camera_temp = camera_wb_dict['temperature']

    # Вычисляем релевантность (обратная к разности температур)
    temp_diff = abs(camera_temp - standard_temp)

    # Нормализуем релевантность в диапазон 0-100%
    # Если разница меньше 200K - высокая релевантность
    # Если больше 2000K - низкая релевантность
    if temp_diff <= 200:
        relevance = 100
    elif temp_diff >= 2000:
        relevance = 0
    else:
        # Линейная интерполяция между 200K и 2000K
        relevance = 100 - (temp_diff - 200) * 100 / (2000 - 200)

    # Добавляем новые поля
    result = camera_wb_dict.copy()
    result['best_illuminant'] = best_illuminant
    result['camera_relevance'] = round(relevance, 1)

    # Официальные DNG коды источников освещения (Adobe DNG Specification)
    ILLUMINANT_TO_DNG = {
        # Стандартные источники CIE
        'A': 17,  # Incandescent / Tungsten (2856K)
        'B': 18,  # Direct sunlight at noon (4874K)
        'C': 19,  # Average / North sky daylight (6774K)
        'D50': 23,  # ISO studio tungsten (5003K)
        'D55': 20,  # Daylight D55 (5503K)
        'D65': 21,  # Daylight D65 (6504K) - стандарт sRGB
        'D75': 22,  # North sky daylight (7504K)

        # Флуоресцентные источники
        'F1': 24,  # Daylight fluorescent (6430K)
        'F2': 25,  # Cool white fluorescent (4230K)
        'F3': 26,  # White fluorescent (3450K)
        'F4': 27,  # Warm white fluorescent (2940K)
        'F5': 28,  # Daylight fluorescent (6350K)
        'F6': 29,  # Lite white fluorescent (4150K)
        'F7': 30,  # D65 simulator, daylight simulator (6500K)
        'F8': 31,  # D50 simulator, Sylvania F40 Design 50 (5000K)
        'F9': 32,  # Cool white deluxe fluorescent (4150K)
        'F10': 33,  # Philips TL85, Ultralume 50 (5000K)
        'F11': 34,  # Philips TL84, Ultralume 40 (4000K)
        'F12': 35,  # Philips TL83, Ultralume 30 (3000K)

        # Специальные источники
        'ISO_STUDIO_TUNGSTEN': 24,  # Альтернативное название для D50

        # Вспышки и студийное освещение
        'FLASH': 4,  # Flash
        'FINE_WEATHER': 9,  # Fine weather
        'CLOUDY_WEATHER': 10,  # Cloudy weather
        'SHADE': 11,  # Shade
        'DAYLIGHT_FLUORESCENT': 12,  # Daylight fluorescent (D 5700 – 7100K)
        'DAY_WHITE_FLUORESCENT': 13,  # Day white fluorescent (N 4600 – 5400K)
        'COOL_WHITE_FLUORESCENT': 14,  # Cool white fluorescent (W 3900 – 4500K)
        'WHITE_FLUORESCENT': 15,  # White fluorescent (WW 3200 – 3700K)
        'STANDARD_LIGHT_A': 17,  # Standard light A
        'STANDARD_LIGHT_B': 18,  # Standard light B
        'STANDARD_LIGHT_C': 19,  # Standard light C

        # Добавляем общепринятые альтернативные названия
        'DAYLIGHT': 21,  # Часто используется как синоним D65
        'TUNGSTEN': 17,  # Синоним источника A
        'INCANDESCENT': 17,  # Синоним источника A
        'SUNLIGHT': 18,  # Синоним источника B
        'SKYLIGHT': 19,  # Синоним источника C
    }

    return ILLUMINANT_TO_DNG[best_illuminant]


def find_best_illuminant(patches_data):
    """
    Брутфорс поиск лучшего источника освещения
    Args:
        patches_data: список словарей с 'rgb' и 'xyz_reference'
    Returns:
        str: ID лучшего источника (библиотечный)
    """

    # Все доступные источники из библиотеки colour
    illuminants = colour.CCS_ILLUMINANTS['CIE 1931 2 Degree Standard Observer'].keys()

    best_illuminant = None
    min_error = float('inf')

    for illuminant_name in illuminants:
        total_error = 0

        try:
            for patch in patches_data:
                rgb = np.array(patch['rgb'])
                if rgb.max() > 1.0:
                    rgb = rgb / 255.0

                xyz_reference = np.array(patch['xyz_reference'])

                xyz_calculated = colour.RGB_to_XYZ(
                    rgb,
                    colourspace='sRGB',
                    illuminant=colour.CCS_ILLUMINANTS['CIE 1931 2 Degree Standard Observer'][illuminant_name]
                )

                lab_ref = colour.XYZ_to_Lab(xyz_reference)
                lab_calc = colour.XYZ_to_Lab(xyz_calculated)

                total_error += delta_E_CIE2000(lab_ref, lab_calc)

            avg_error = total_error / len(patches_data)

            if avg_error < min_error:
                min_error = avg_error
                best_illuminant = illuminant_name

        except:
            continue

    return best_illuminant

def calculate_forward_matrix(color_matrix, rgb_array, xyz_array):
    """
    Вычисляет ForwardMatrix1 для DCP профиля
    Не просто инверсия ColorMatrix!
    """

    # 1. Преобразуем XYZ в цветовое пространство вывода (sRGB)
    xyz_to_srgb = np.array([
        [3.2406, -1.5372, -0.4986],
        [-0.9689, 1.8758, 0.0415],
        [0.0557, -0.2040, 1.0570]
    ])

    # 2. Целевые RGB значения в sRGB
    srgb_target = xyz_array @ xyz_to_srgb.T

    # 3. Оптимизируем ForwardMatrix для минимизации ошибки
    def forward_objective(forward_matrix_flat):
        forward_matrix = forward_matrix_flat.reshape(3, 3)

        # Camera RGB → XYZ → sRGB для отображения
        xyz_predicted = rgb_array @ color_matrix.T  # RAW RGB → XYZ
        srgb_predicted = xyz_predicted @ forward_matrix.T  # XYZ → sRGB (для показа)

        return (srgb_predicted - srgb_target).flatten()


    # Начальная матрица - комбинация ColorMatrix + XYZ→sRGB
    initial_forward = xyz_to_srgb @ color_matrix

    from scipy.optimize import least_squares
    result = least_squares(forward_objective, initial_forward.flatten())

    forward_matrix = result.x.reshape(3, 3)
    return forward_matrix


def calculate_reduction_matrices(color_matrix, forward_matrix):
    """
    ReductionMatrix - для работы с различными цветовыми пространствами
    """
    # ReductionMatrix преобразует ColorMatrix к стандартному освещению
    # Обычно это единичная матрица для одного источника света
    reduction_matrix1 = np.eye(3)
    reduction_matrix2 = np.eye(3)

    return reduction_matrix1, reduction_matrix2


def build_dcp_profile(patches_data, output_filename):

    print(f"Обрабатываем {len(patches_data)} патчей...")

    # Извлекаем данные
    rgb_values = []
    xyz_values = []

    for patch in patches_data:
        rgb = np.array(patch['RGB'])
        xyz = np.array(patch['XYZ'])

        # Нормализуем RGB к [0,1]
        rgb_norm = rgb / 255.0 if rgb.max() > 1.0 else rgb
        rgb_values.append(rgb_norm)
        xyz_values.append(xyz)

    rgb_array = np.array(rgb_values)
    xyz_array = np.array(xyz_values)

    # Строим матрицу преобразования RGB→XYZ
    def build_color_matrix(rgb, xyz):
        def objective(matrix_flat):
            matrix = matrix_flat.reshape(3, 3)
            xyz_pred = rgb @ matrix.T
            return (xyz_pred - xyz).flatten()

        initial_matrix = np.eye(3).flatten()
        result = least_squares(objective, initial_matrix)
        return result.x.reshape(3, 3)

    # Строим основную матрицу
    color_matrix = build_color_matrix(rgb_array, xyz_array)

    # После расчета color_matrix
    print("Вычисляем ForwardMatrix...")
    forward_matrix1 = calculate_forward_matrix(color_matrix, rgb_array, xyz_array)
    forward_matrix2 = forward_matrix1  # Пока одинаковые для одного освещения

    print("Вычисляем ReductionMatrix...")
    reduction_matrix1, reduction_matrix2 = calculate_reduction_matrices(
        color_matrix, forward_matrix1
    )

    # Подготавливаем данные для твоей системы оценки
    patch_data_for_analysis = []
    xyz_predicted = rgb_array @ color_matrix.T

    for i, patch in enumerate(patches_data):
        # Форматируем под твою систему
        analysis_patch = {
            'mean_rgb': rgb_values[i] * 255,  # Возвращаем к 0-255
            'SAMPLE_ID': patch['SAMPLE_ID'],
            'original_xyz': xyz_values[i],
            'predicted_xyz': xyz_predicted[i]
        }
        patch_data_for_analysis.append(analysis_patch)

    # ИСПОЛЬЗУЕМ ТВОЮ СИСТЕМУ ОЦЕНКИ! 🎯
    status, quality_result = expected_artifact_quality(
        patch_data_for_analysis,
        is_negative=False,  # Для обычной камеры
        artifact_type="DCP"
    )

    if status == 0:  # GENERIC_OK
        print("\n" + "=" * 50)
        print("АНАЛИЗ КАЧЕСТВА ПРОФИЛЯ (твоя система):")
        print("=" * 50)
        print(quality_result['m_analysis'])
        print("\n" + quality_result['q_results'])
        print("=" * 50)

        # Достаем детальные оценки
        quality_data = quality_result['data']
        overall_score = quality_data['score']
        grade = quality_data['grade']
        expected_delta_e = quality_data['delta_e_expected']

    else:
        print("❌ Ошибка в анализе качества")
        overall_score = 0.5  # Fallback
        grade = "UNKNOWN"
        expected_delta_e = "Unknown"

    print(f"\nМатрица преобразования RGB→XYZ:")
    print(color_matrix)

    best_il = find_best_illuminant(patches_data)

    # Создаем DCP с оценкой качества
    dcp_data = {
        # === ОБЯЗАТЕЛЬНЫЕ ТЕГИ ===
        'color_matrix_1': color_matrix,  # ColorMatrix1 (ОБЯЗАТЕЛЬНО)
        'illuminant_1': best_il,  # CalibrationIlluminant1 (D65)
        'unique_camera_model': 'Generic Camera',  # UniqueCameraModel (ОБЯЗАТЕЛЬНО)

        # === МАТРИЦЫ ДЛЯ ИСТОЧНИКА 1 ===
        'forward_matrix_1': forward_matrix1,  # ForwardMatrix1
        'reduction_matrix_1': reduction_matrix1,  # ReductionMatrix1
        'camera_calibration_1': np.eye(3),  # CameraCalibration1

        # === МАТРИЦЫ ДЛЯ ИСТОЧНИКА 2 (пока None) ===
        'color_matrix_2': None,  # ColorMatrix2 (для второго освещения)
        'illuminant_2': None,  # CalibrationIlluminant2 (17 = StdA)
        'forward_matrix_2': None,  # ForwardMatrix2
        'reduction_matrix_2': None,  # ReductionMatrix2
        'camera_calibration_2': None,  # CameraCalibration2

        # === МЕТАДАННЫЕ ПРОФИЛЯ ===
        'profile_name': 'AI Generated DCP',  # ProfileName
        'profile_copyright': 'AI Assistant',  # ProfileCopyright
        'profile_embed_policy': 3,  # ProfileEmbedPolicy (разрешить копирование)
        'profile_version': '1.0.0',  # Версия профиля (кастомное поле)

        # === ТАБЛИЦЫ ПОИСКА (пока None) ===
        'hue_sat_deltas_1': None,  # HueSatDeltas1 (HSL коррекция) **ID 50708** [[5]](https://exiftool.org/TagNames/DNG.html).
        'hue_sat_deltas_2': None,  # HueSatDeltas2
        'look_table': None,  # LookTable (творческий look)

        # === ИНФОРМАЦИЯ О КАЧЕСТВЕ ===
        'patches_count': len(patches_data),
        'quality_score': overall_score,
        'quality_grade': grade,
        'expected_accuracy': expected_delta_e,
        'analysis_details': quality_result if status == 0 else None,

        # === ТЕХНИЧЕСКАЯ ИНФОРМАЦИЯ ===
        'creation_date': None,  # Дата создания (заполним в save_dcp)
        'software_version': 'PatchReader flab-DIY-stack ',  # Версия софта
    }

    # Сохраняем как DCP
    save_dcp_profile(dcp_data, output_filename)

    return dcp_data


def save_dcp_profile(dcp_data, filename):
    """Сохраняет DCP с правильными типами данных для каждого тега"""

    # Определяем какие теги записывать
    def should_write_tag(key, value):
        if value is None:
            return False
        if key.endswith('_2') and not has_second_illuminant(dcp_data):
            return False  # Не записываем теги для второго источника если его нет
        return True

    def has_second_illuminant(dcp_data):
        """Проверяем есть ли данные для второго источника света"""
        return (dcp_data.get('illuminant_2') is not None and
                dcp_data.get('color_matrix_2') is not None)

    # Маппинг: поле → (тег_id, тип_данных, функция_записи)
    DCP_TAG_MAP = {
        'color_matrix_1': (50714, 10, write_matrix_srational),
        'color_matrix_2': (50715, 10, write_matrix_srational),
        'forward_matrix_1': (50716, 10, write_matrix_srational),
        'forward_matrix_2': (50726, 10, write_matrix_srational),
        'reduction_matrix_1': (50719, 10, write_matrix_srational),
        'reduction_matrix_2': (50720, 10, write_matrix_srational),
        'camera_calibration_1': (50723, 10, write_matrix_srational),
        'camera_calibration_2': (50724, 10, write_matrix_srational),

        'illuminant_1': (50717, 3, write_short),
        'illuminant_2': (50718, 3, write_short),
        'profile_embed_policy': (50941, 4, write_long),

        'profile_name': (50936, 2, write_ascii_string),
        'profile_copyright': (50942, 2, write_ascii_string),
        'unique_camera_model': (50727, 2, write_ascii_string), #
        'profile_version': (50725, 2, write_ascii_string),  # ✅ ДОБАВЛЕНО!
        # Правильный HueSatDeltas1
        'hue_sat_deltas_1': (50708, 5, write_matrix_srational),  # ✅ ИСПРАВЛЕНО!

    }

    # Собираем теги для записи
    tags_to_write = []
    for key, value in dcp_data.items():
        if key in DCP_TAG_MAP and should_write_tag(key, value):
            tag_id, data_type, write_func = DCP_TAG_MAP[key]
            tags_to_write.append({
                'tag_id': tag_id,
                'data_type': data_type,
                'value': value,
                'write_func': write_func
            })

    write_dcp_binary(filename + '.dcp', tags_to_write)


# === ФУНКЦИИ ЗАПИСИ ДЛЯ КАЖДОГО ТИПА ===

def write_matrix_srational(f, matrix):
    """Записывает 3x3 матрицу как 9 SRATIONAL значений"""
    for value in matrix.flatten():
        # Конвертируем float в рациональное число
        numerator = int(value * 1000000)
        denominator = 1000000
        f.write(struct.pack('<l', numerator))  # signed int32
        f.write(struct.pack('<l', denominator))  # signed int32


def write_short(f, value):
    """Записывает SHORT (2 байта)"""
    f.write(struct.pack('<H', int(value)))


def write_long(f, value):
    """Записывает LONG (4 байта)"""
    f.write(struct.pack('<L', int(value)))


def write_ascii_string(f, text):
    """Записывает ASCII строку с null-terminator"""
    text_bytes = text.encode('ascii') + b'\0'
    f.write(text_bytes)
    # Дополняем до четного количества байт
    if len(text_bytes) % 2 == 1:
        f.write(b'\0')


def write_dcp_binary(filename, tags_to_write):
    """Записывает бинарный DCP файл с правильным форматированием"""

    with open(filename, 'wb') as f:
        # TIFF заголовок
        f.write(b'II')  # Little endian
        f.write(struct.pack('<H', 42))  # TIFF magic
        f.write(struct.pack('<L', 8))  # Offset to IFD

        # Вычисляем размеры и смещения
        ifd_size = 2 + len(tags_to_write) * 12 + 4  # header + tags + next_offset
        data_offset = 8 + ifd_size

        # IFD заголовок
        f.write(struct.pack('<H', len(tags_to_write)))

        # === ЗАПИСЫВАЕМ ДИРЕКТОРИИ ТЕГОВ ===
        current_data_offset = data_offset

        for tag in tags_to_write:
            f.write(struct.pack('<H', tag['tag_id']))  # Tag ID
            f.write(struct.pack('<H', tag['data_type']))  # Data type

            # Count зависит от типа данных
            if tag['data_type'] == 10:  # SRATIONAL matrix
                count = 9  # 3x3 matrix
                f.write(struct.pack('<L', count))
                f.write(struct.pack('<L', current_data_offset))
                current_data_offset += count * 8  # 9 * (4+4 bytes)

            elif tag['data_type'] == 2:  # ASCII string
                text_len = len(tag['value'].encode('ascii')) + 1  # +null terminator
                f.write(struct.pack('<L', text_len))
                if text_len <= 4:
                    # Короткая строка помещается прямо в директорию
                    f.write(tag['value'].encode('ascii').ljust(4, b'\0'))
                else:
                    f.write(struct.pack('<L', current_data_offset))
                    current_data_offset += (text_len + 1) // 2 * 2  # Выравнивание

            else:  # SHORT, LONG
                f.write(struct.pack('<L', 1))  # Count = 1
                if tag['data_type'] == 3:  # SHORT
                    f.write(struct.pack('<H', int(tag['value'])))
                    f.write(struct.pack('<H', 0))  # Padding
                else:  # LONG
                    f.write(struct.pack('<L', int(tag['value'])))

        # Next IFD offset (0 = последняя)
        f.write(struct.pack('<L', 0))

        # === ЗАПИСЫВАЕМ ДАННЫЕ ТЕГОВ ===
        for tag in tags_to_write:
            if tag['data_type'] == 10:  # Матрицы
                tag['write_func'](f, tag['value'])
            elif tag['data_type'] == 2 and len(tag['value']) > 3:  # Длинные строки
                tag['write_func'](f, tag['value'])

    print(f"📁 DCP файл записан: {filename}")


def save_dcp_as_json(dcp_data, filename):
    """JSON только для отладки и анализа!"""

    matrix = dcp_data['color_matrix_1'].tolist()

    profile_data = {
        'profile_type': 'DCP_DEBUG',  # Не настоящий DCP!
        'color_matrix_1': matrix,
        'illuminant_1': dcp_data['illuminant_1'],
        'quality_assessment': {
            'grade': dcp_data['quality_grade'],
            'expected_accuracy': dcp_data['expected_accuracy']
        },
        'adobe_dng_format': {
            'ColorMatrix1': ' '.join([f'{x:.6f}' for x in np.array(matrix).flatten()])
        }
    }

    with open(filename + '_debug.json', 'w') as f:
        json.dump(profile_data, f, indent=2)

    print(f"🔧 DEBUG версия сохранена как {filename}_debug.json")
    print(f"📝 Для Adobe DNG вставь матрицу:")
    print(f"ColorMatrix1: {profile_data['adobe_dng_format']['ColorMatrix1']}")


def test_dcp_creation():
    """Тестирует создание DCP профиля"""

    # Тестовые данные патчей
    test_patches = [
        {'RGB': [255, 0, 0], 'XYZ': [0.4124, 0.2126, 0.0193], 'SAMPLE_ID': 'RED'},
        {'RGB': [0, 255, 0], 'XYZ': [0.3576, 0.7152, 0.1192], 'SAMPLE_ID': 'GREEN'},
        {'RGB': [0, 0, 255], 'XYZ': [0.1805, 0.0722, 0.9505], 'SAMPLE_ID': 'BLUE'},
        {'RGB': [128, 128, 128], 'XYZ': [0.2034, 0.2140, 0.2330], 'SAMPLE_ID': 'GRAY'},
    ]

    print("🧪 Тестируем создание DCP...")

    try:
        dcp_data = build_dcp_profile(test_patches, "test_profile")
        print("✅ DCP профиль создан успешно!")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


# Для тестирования
if __name__ == "__main__":
    test_dcp_creation()
    # color checker
    # colprof -v -D "Scanner Profile" -C "Your Profile Description" -q m -S Adobe-RGB -wp colorchecker.ti3
    # 220 patches
    # colprof -v -D "Scanner Profile" -C "Description" -q m -S Adobe-RGB -wp target.ti3
    # colprof -v -D "Scanner 220 Profile" -C "High quality LUT profile" -q h -S Adobe-RGB -wp target.ti3

    # Scanner Profile
    # colprof -v -qh (-M) -S Adobe-RGB -wp -A bradford input.ti3
    # Scanner Profile 600+ drift stable   **Matrix + High Quality**
    # colprof -v -qh (-M) -S Adobe-RGB -wp -A bradford input.ti3
    # Scanner Profile 600+ color precise  **LUT + High Quality**
    # colprof -v -qh -S Adobe-RGB -wp -A bradford input.ti3

    # Scanner Profile с полными CAM матрицами
    # colprof -v -qh -S Adobe-RGB -wp -A bradford input.ti3

    # BW Reverce
    # ЧБ Scanner Reverse Profile для Capture One
    # colprof -v -q h -a m -Z b -u input.ti3
    # Matrix + ограничение диапазона
    # colprof -v -q h -a m -Z b -u -R input.ti3



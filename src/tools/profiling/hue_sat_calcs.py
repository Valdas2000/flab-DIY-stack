import numpy as np
from typing import Dict, List, Tuple, Union, Optional, Any

# Constants
GENERIC_ERROR = -1
GENERIC_OK = 0

def select_table_configuration(is_color: bool, is_negative: bool, patches_count: int) :
    """
    Выбирает конфигурацию таблицы согласно ВАШИМ требованиям.

    Args:
        is_color: True для цветных изображений
        is_negative: True для негативной пленки
        patches_count: Количество доступных патчей

    Returns:
        Словарь с параметрами таблицы
    """
    # ЧБ + позитив = ЗАПРЕЩЕНО
    if not is_color and not is_negative:
        raise ValueError("ЗАПРЕЩЕННЫЙ КЕЙС: ЧБ позитив невозможен")

    ret = {}
    # ЧБ + негатив = всегда bw_reversal
    if not is_color and is_negative:
        return {
            'dim_x': 8, 'dim_y': 4, 'dim_z': 12,
            'total_patches': 8 * 4 * 12,  # 384
            'drift_buffer': 200,
            'description': 'BW universal reversal with drift defence +-300K',
            'algorithm_params': {
                # interpolation options for BW reversal process
                'scenario': 'bw_reversal',
                'k_neighbors': 6,      # Меньше соседей (проще задача)
                'shepard_power': 1.5,  # Менее агрессивные веса
                'rbf_function': 'cubic',
                'rbf_smoothing': 0.05, # Меньше регуляризация
                'outlier_filtering': False,
            },
            'quality_thresholds': {
                # quality metrics for Hybrid
                'boundary_clipping_threshold': 0.2,  # Строже для ЧБ
                'instability_threshold': 10.0,
                'extreme_values_threshold': 0.3
            },
            'correction_limits': {
                'hue': (-15.0, 15.0),  # для bw_reversal
                'sat': (-0.5, 0.0),  # для bw_reversal
                'val': (-0.4, 0.4)  # для bw_reversal
            }

        }

    # Цветные изображения - ранжирование по количеству патчей
    if patches_count < 100:
        # Малая таблица
        ret = {
            'table_type': 'small colors set',
            'dim_x': 8, 'dim_y': 4, 'dim_z': 4,
            'total_patches': 8 * 4 * 4,  # 128
            'drift_buffer': 200 if is_negative else 0,
            'description': f'Small Color Set 100- {"reversal +-300K" if is_negative else "positive"})'
        }
    elif patches_count <= 300:
        # Стандартная ColorChecker
        ret = {
            'table_type': 'colorchecker',
            'dim_x': 12, 'dim_y': 6, 'dim_z': 6,
            'total_patches': 12 * 6 * 6,  # 432
            'drift_buffer': 200 if is_negative else 0,
            'description': f'Medium Color Set 100-300 ,  {"reversal +-300K" if is_negative else "positive"})'
        }
    else:
        # Большая таблица для реверса/высокой точности
        ret = {
            'table_type': 'color_reversal',
            'dim_x': 24, 'dim_y': 8, 'dim_z': 6,
            'total_patches': 24 * 8 * 6,  # 1152
            'drift_buffer': 200 if is_negative else 0,
            'description': f'Big Color Set 300+,  {"reversal +-300K" if is_negative else "positive"})'
        }

    ret1 = {}
    if is_negative:
        ret1 = {'algorithm_params': {
                'scenario': 'color_reversal',
                'k_neighbors': 8,
                'shepard_power': 2,
                'rbf_function': 'thin_plate',
                'rbf_smoothing': 0.1,
                'outlier_filtering': True
            },
           'quality_thresholds': {  # quality metrics for Hybrid
                'boundary_clipping_threshold': 0.3,
                'instability_threshold': 15.0,
                'extreme_values_threshold': 0.4
            },
            'correction_limits': {
                'hue': (-30.0, 30.0),  # Полные цветовые коррекции
                'sat': (-0.3, 0.3),  # Насыщенность в обе стороны
                'val': (-0.2, 0.2)  # Умеренные яркостные коррекции
            }
        }

    else:
        ret1= {
            'algorithm_params': {
                'scenario': 'emulation',
                'k_neighbors': 12,     # Больше соседей (сложная задача)
                'shepard_power': 2.5,  # Более локализованная интерполяция
                'rbf_function': 'multiquadric',
                'rbf_smoothing': 0.2,  # Больше регуляризация
                'outlier_filtering': True,
            },
            'quality_thresholds': {
                # quality metrics for Hybrid
                'boundary_clipping_threshold': 0.5,  # Либеральнее для эмуляции
                'instability_threshold': 20.0,
                'extreme_values_threshold': 0.6
            },
            'correction_limits': {
                'hue': (-45.0, 45.0),  # Максимальные цветовые сдвиги
                'sat': (-0.4, 0.6),  # Сильное повышение насыщенности
                'val': (-0.3, 0.3)  # Расширенные яркостные коррекции
            }
        }

    ret.update(ret1)
    return ret

def create_empty_hue_sat_table(config: Dict[str, Union[int, str]]) -> Dict[str, Any]:
    """
    Создает пустую структуру данных для HSV таблицы на основе конфигурации.

    Args:
        config: Словарь конфигурации от select_table_configuration()

    Returns:
        Словарь с пустыми структурами для заполнения данными
    """
    dim_x, dim_y, dim_z = config['dim_x'], config['dim_y'], config['dim_z']

    # Создаем пустые numpy массивы для каждой компоненты HSV
    # Инициализируем NaN для четкого разделения заполненных/пустых ячеек
    empty_table = np.full((dim_x, dim_y, dim_z), np.nan, dtype=np.float32)

    return {
        # Основные таблицы дельт (3 компонента HSV)
        'hue_deltas': empty_table.copy(),  # Δ Hue
        'sat_deltas': empty_table.copy(),  # Δ Saturation
        'val_deltas': empty_table.copy(),  # Δ Value/Lightness

        # Метаданные структуры
        'dimensions': {
            'hue_divisions': dim_x,  # Разбиений по оттенку
            'sat_divisions': dim_y,  # Разбиений по насыщенности
            'val_divisions': dim_z  # Разбиений по яркости
        },

        # Индексы координат HSV для каждой ячейки
        'coordinate_map': {
            'hue_coords': np.linspace(0.0, 360.0, dim_x, endpoint=False),  # 0-360°
            'sat_coords': np.linspace(0.0, 1.0, dim_y),  # 0-1
            'val_coords': np.linspace(0.0, 1.0, dim_z)  # 0-1
        },

        # Маска заполненных ячеек (изначально все False)
        'filled_mask': np.zeros((dim_x, dim_y, dim_z), dtype=bool),

        # Метаданные конфигурации
        'config_info': {
            'table_type': config['table_type'],
            'description': config['description'],
            'total_cells': dim_x * dim_y * dim_z,
            'drift_buffer': config.get('drift_buffer', 0)
        },
        'algorithm_params': config['algorithm_params'],
        'quality_thresholds': config['quality_thresholds'],
        'correction_limits': config['correction_limits']
    }


def populate_hue_sat_table(empty_table: Dict[str, Any], measured_patches: List[Dict]) -> Dict[str, Any]:
    """
    Заполняет HSV таблицу для DCP профиля.

    DCP логика: измеренные RGB камеры → эталонные XYZ → дельты коррекции
    НЕ зависит от целевого устройства вывода!

    Args:
        empty_table: Результат create_empty_hue_sat_table()
        measured_patches: [{'RGB': [r,g,b], 'XYZ': [x,y,z]}, ...]
            где RGB = RAW→RGB конвертация камеры
            где XYZ = колориметрически измеренные эталоны
    """
    import colorsys

    # Извлекаем координатные сетки
    hue_coords = empty_table['coordinate_map']['hue_coords']
    sat_coords = empty_table['coordinate_map']['sat_coords']
    val_coords = empty_table['coordinate_map']['val_coords']

    # Работаем с существующими массивами
    hue_deltas = empty_table['hue_deltas']
    sat_deltas = empty_table['sat_deltas']
    val_deltas = empty_table['val_deltas']
    filled_mask = empty_table['filled_mask']

    mapped_patches = 0

    for patch in measured_patches:
        # 🎯 1. RGB КАМЕРЫ (что получилось после матрицы камеры)
        camera_rgb = np.array(patch['RGB'])

        # 🎯 2. ЭТАЛОННЫЕ XYZ (колориметрически измеренные)
        reference_xyz = np.array(patch['XYZ'])

        # 🎯 3. Camera RGB → HSV (для индексации в таблице)
        camera_rgb_norm = camera_rgb / 255.0 if np.max(camera_rgb) > 1.0 else camera_rgb
        camera_rgb_norm = np.clip(camera_rgb_norm, 0, 1)  # Безопасность

        camera_hsv_raw = colorsys.rgb_to_hsv(camera_rgb_norm[0], camera_rgb_norm[1], camera_rgb_norm[2])
        camera_hsv = np.array([
            camera_hsv_raw[0] * 360.0,  # H: 0-360°
            camera_hsv_raw[1],  # S: 0-1
            camera_hsv_raw[2]  # V: 0-1
        ])

        # 🎯 4. Reference XYZ → "правильный" RGB
        # Для DCP используем СТАНДАРТНОЕ рабочее пространство (обычно ProPhoto/sRGB)
        reference_rgb = xyz_to_camera_rgb(reference_xyz)
        reference_rgb_norm = reference_rgb / 255.0 if np.max(reference_rgb) > 1.0 else reference_rgb
        reference_rgb_norm = np.clip(reference_rgb_norm, 0, 1)

        # 🎯 5. Reference RGB → HSV (целевые значения)
        reference_hsv_raw = colorsys.rgb_to_hsv(reference_rgb_norm[0], reference_rgb_norm[1], reference_rgb_norm[2])
        reference_hsv = np.array([
            reference_hsv_raw[0] * 360.0,
            reference_hsv_raw[1],
            reference_hsv_raw[2]
        ])

        # 🎯 6. Индексация по HSV КАМЕРЫ (не эталона!)
        h_idx = np.argmin(np.abs(hue_coords - camera_hsv[0]))
        s_idx = np.argmin(np.abs(sat_coords - camera_hsv[1]))
        v_idx = np.argmin(np.abs(val_coords - camera_hsv[2]))

        # 🎯 7. Дельты коррекции = (эталон - камера)
        delta_h = reference_hsv[0] - camera_hsv[0]
        delta_s = reference_hsv[1] - camera_hsv[1]
        delta_v = reference_hsv[2] - camera_hsv[2]

        # Обработка циклического Hue
        if delta_h > 180:
            delta_h -= 360
        elif delta_h < -180:
            delta_h += 360

        # 🎯 8. Записываем коррекцию в таблицу
        if not filled_mask[h_idx, s_idx, v_idx]:
            hue_deltas[h_idx, s_idx, v_idx] = delta_h
            sat_deltas[h_idx, s_idx, v_idx] = delta_s
            val_deltas[h_idx, s_idx, v_idx] = delta_v
            filled_mask[h_idx, s_idx, v_idx] = True
            mapped_patches += 1

    # Обновляем статистику
    empty_table['config_info']['filled_cells'] = np.sum(filled_mask)
    empty_table['config_info']['fill_ratio'] = (
            empty_table['config_info']['filled_cells'] /
            empty_table['config_info']['total_cells']
    )
    empty_table['config_info']['mapped_patches'] = mapped_patches
    empty_table['config_info']['total_input_patches'] = len(measured_patches)

    return empty_table


def xyz_to_camera_rgb(xyz):
    """
    XYZ → RGB для DCP профиля.
    Используем стандартное рабочее пространство DCP (обычно близкое к ProPhoto).
    """
    # DCP обычно использует широкое цветовое пространство
    # Матрица ProPhoto RGB (D50 illuminant, что часто используется в DCP)
    M = np.array([
        [1.3460, -0.2556, -0.0511],
        [-0.5446, 1.5082, 0.0205],
        [0.0000, 0.0000, 1.2123]
    ])

    # Нормализация XYZ (Y=100 для белой точки)
    xyz_norm = xyz / 100.0 if np.max(xyz) > 1.0 else xyz

    # Применяем матрицу
    rgb_linear = M @ xyz_norm

    # Гамма коррекция (обычно простая 2.2 для DCP)
    rgb_gamma = np.power(np.abs(rgb_linear), 1 / 2.2) * np.sign(rgb_linear)

    # Возвращаем в диапазоне 0-255 (но без жесткого clipping)
    return rgb_gamma * 255


def interpolate_color_correction_sheppard(populated_table: Dict[str, Any]) -> Dict[str, Any]:
    """
    Универсальная интерполяция с использованием Shepard + конфигурационные параметры.

    Особенности:
    - Shepard interpolation (IDW) как основной метод
    - Использует параметры из конфигурации таблицы
    - Универсальные ограничения для всех сценариев
    - Векторизованные операции

    Args:
        populated_table: Результат populate_hue_sat_table() с заполненными измерениями

    Returns:
        Полностью заполненная HSV таблица с интерполированными значениями
    """
    from scipy.spatial import KDTree

    # Извлекаем структуры данных
    hue_deltas = populated_table['hue_deltas']
    sat_deltas = populated_table['sat_deltas']
    val_deltas = populated_table['val_deltas']
    filled_mask = populated_table['filled_mask']

    coordinate_map = populated_table['coordinate_map']
    hue_coords = coordinate_map['hue_coords']
    sat_coords = coordinate_map['sat_coords']
    val_coords = coordinate_map['val_coords']

    # НОВОЕ: Извлекаем параметры из конфигурации
    algorithm_params = populated_table['algorithm_params']
    correction_limits = populated_table['correction_limits']
    scenario = algorithm_params['scenario']

    # Получаем размеры сетки
    n_hue, n_sat, n_val = hue_deltas.shape

    print(f"🎯 Shepard Interpolation [{scenario.upper()}]:")
    print(f"   Grid: {n_hue}×{n_sat}×{n_val} = {n_hue * n_sat * n_val} cells")
    print(f"   Filled: {np.sum(filled_mask)} ({np.sum(filled_mask) / (n_hue * n_sat * n_val) * 100:.1f}%)")

    # Проверяем достаточность данных
    if np.sum(filled_mask) < 4:
        print("❌ Insufficient data for interpolation (need ≥4 points)")
        return populated_table

    # 1. Собираем известные точки и коррекции (векторизованно)
    filled_indices = np.where(filled_mask)
    n_known = len(filled_indices[0])

    # HSV координаты известных точек
    known_hsv = np.column_stack([
        hue_coords[filled_indices[0]],
        sat_coords[filled_indices[1]],
        val_coords[filled_indices[2]]
    ])

    # HSV коррекции
    known_corrections = np.column_stack([
        hue_deltas[filled_mask],
        sat_deltas[filled_mask],
        val_deltas[filled_mask]
    ])

    print(f"   Known points: {n_known}")

    # 2. Создаем KDTree для быстрого поиска соседей
    spatial_index = KDTree(known_hsv)

    # 3. Находим все пустые ячейки для интерполяции
    empty_mask = ~filled_mask
    empty_indices = np.where(empty_mask)
    n_empty = len(empty_indices[0])

    if n_empty == 0:
        print("✅ All cells already filled")
        return populated_table

    # HSV координаты пустых точек
    target_hsv = np.column_stack([
        hue_coords[empty_indices[0]],
        sat_coords[empty_indices[1]],
        val_coords[empty_indices[2]]
    ])

    print(f"   Target points: {n_empty}")

    # 4. НОВОЕ: Параметры интерполяции из конфигурации
    k_neighbors = min(algorithm_params['k_neighbors'], n_known)  # Не больше чем есть точек
    shepard_power = algorithm_params['shepard_power']

    print(f"   Using {k_neighbors} neighbors, Shepard power={shepard_power}")

    # 5. Векторизованный поиск k ближайших соседей
    distances, neighbor_indices = spatial_index.query(target_hsv, k=k_neighbors)

    # Обработка случая одного соседа (distances может быть 1D)
    if k_neighbors == 1:
        distances = distances.reshape(-1, 1)
        neighbor_indices = neighbor_indices.reshape(-1, 1)

    # 6. Векторизованный расчет весов Shepard
    # Избегаем деления на ноль для совпадающих точек
    epsilon = 1e-12
    safe_distances = np.maximum(distances, epsilon)

    # Веса Shepard: w_i = 1 / d_i^p
    shepard_weights = 1.0 / (safe_distances ** shepard_power)

    # Нормализация весов (сумма = 1 для каждой точки)
    weight_sums = np.sum(shepard_weights, axis=1, keepdims=True)
    normalized_weights = shepard_weights / weight_sums

    # 7. Векторизованная интерполяция для каждой компоненты
    interpolated_corrections = np.zeros((n_empty, 3))

    for comp in range(3):  # H, S, V компоненты
        # Берем значения соседей для текущей компоненты
        neighbor_values = known_corrections[neighbor_indices, comp]  # shape: (n_empty, k_neighbors)

        # Взвешенная сумма
        interpolated_corrections[:, comp] = np.sum(
            normalized_weights * neighbor_values, axis=1
        )

    print("✅ Shepard interpolation completed")

    # 8. НОВОЕ: Применяем ограничения из конфигурации
    hue_limits = correction_limits['hue']
    sat_limits = correction_limits['sat']
    val_limits = correction_limits['val']

    interpolated_corrections[:, 0] = np.clip(interpolated_corrections[:, 0], hue_limits[0], hue_limits[1])
    interpolated_corrections[:, 1] = np.clip(interpolated_corrections[:, 1], sat_limits[0], sat_limits[1])
    interpolated_corrections[:, 2] = np.clip(interpolated_corrections[:, 2], val_limits[0], val_limits[1])

    # 9. Заполняем результирующие массивы
    result_hue_deltas = hue_deltas.copy()
    result_sat_deltas = sat_deltas.copy()
    result_val_deltas = val_deltas.copy()

    # Векторизованная запись результатов
    result_hue_deltas[empty_mask] = interpolated_corrections[:, 0]
    result_sat_deltas[empty_mask] = interpolated_corrections[:, 1]
    result_val_deltas[empty_mask] = interpolated_corrections[:, 2]

    # 10. Создаем результирующую таблицу
    result_table = populated_table.copy()
    result_table['hue_deltas'] = result_hue_deltas
    result_table['sat_deltas'] = result_sat_deltas
    result_table['val_deltas'] = result_val_deltas
    result_table['filled_mask'] = np.ones_like(filled_mask, dtype=bool)  # Все заполнено

    # 11. Обновляем метаданные
    result_table['config_info']['interpolation_method'] = f'shepard_{scenario}'
    result_table['config_info']['filled_cells'] = n_hue * n_sat * n_val
    result_table['config_info']['fill_ratio'] = 1.0
    result_table['config_info']['interpolated_cells'] = n_empty
    result_table['config_info']['k_neighbors'] = k_neighbors
    result_table['config_info']['shepard_power'] = shepard_power

    # НОВОЕ: Записываем примененные ограничения
    result_table['config_info']['applied_limits'] = {
        'hue_delta_range': hue_limits,
        'sat_delta_range': sat_limits,
        'val_delta_range': val_limits
    }

    print(f"✅ {scenario.capitalize()} Shepard interpolation completed:")
    print(f"   Interpolated: {n_empty} new cells")
    print(f"   Method: Shepard IDW (k={k_neighbors}, p={shepard_power})")
    print(f"   Applied limits: Hue {hue_limits}, Sat {sat_limits}, Val {val_limits}")

    return result_table


def interpolate_color_correction_rbf(populated_table: Dict[str, Any],
                                     fallback_for_shepard: bool = False) -> Dict[str, Any]:
    """
    Универсальная RBF интерполяция с конфигурационными параметрами.

    Используется как:
    1. Standalone метод для высокоточной интерполяции
    2. Fallback когда Shepard показывает плохое качество

    Особенности:
    - Использует RBF параметры из конфигурации
    - Универсальные ограничения для всех сценариев
    - Регуляризация для численной стабильности
    - Векторизованные операции

    Args:
        populated_table: Результат populate_hue_sat_table() с заполненными измерениями
        fallback_for_shepard: True если используется как fallback после Shepard

    Returns:
        Полностью заполненная HSV таблица с RBF интерполированными значениями
    """
    from scipy.interpolate import Rbf
    import warnings

    # Извлекаем структуры данных
    hue_deltas = populated_table['hue_deltas']
    sat_deltas = populated_table['sat_deltas']
    val_deltas = populated_table['val_deltas']
    filled_mask = populated_table['filled_mask']

    coordinate_map = populated_table['coordinate_map']
    hue_coords = coordinate_map['hue_coords']
    sat_coords = coordinate_map['sat_coords']
    val_coords = coordinate_map['val_coords']

    # НОВОЕ: Извлекаем параметры из конфигурации
    algorithm_params = populated_table['algorithm_params']
    correction_limits = populated_table['correction_limits']
    scenario = algorithm_params['scenario']

    # Получаем размеры сетки
    n_hue, n_sat, n_val = hue_deltas.shape

    method_name = "RBF Fallback" if fallback_for_shepard else "RBF Primary"
    print(f"🧮 {method_name} [{scenario.upper()}]:")
    print(f"   Grid: {n_hue}×{n_sat}×{n_val} = {n_hue * n_sat * n_val} cells")
    print(f"   Filled: {np.sum(filled_mask)} ({np.sum(filled_mask) / (n_hue * n_sat * n_val) * 100:.1f}%)")

    # Проверяем достаточность данных для RBF
    min_points_required = 6  # RBF нужно больше точек чем Shepard
    if np.sum(filled_mask) < min_points_required:
        print(f"❌ Insufficient data for RBF interpolation (need ≥{min_points_required} points)")
        return populated_table

    # 1. Собираем известные точки и коррекции (векторизованно)
    filled_indices = np.where(filled_mask)
    n_known = len(filled_indices[0])

    # HSV координаты известных точек
    known_hsv = np.column_stack([
        hue_coords[filled_indices[0]],
        sat_coords[filled_indices[1]],
        val_coords[filled_indices[2]]
    ])

    # HSV коррекции
    known_corrections = np.column_stack([
        hue_deltas[filled_mask],
        sat_deltas[filled_mask],
        val_deltas[filled_mask]
    ])

    print(f"   Known points: {n_known}")

    # 2. Находим все пустые ячейки для интерполяции
    empty_mask = ~filled_mask
    empty_indices = np.where(empty_mask)
    n_empty = len(empty_indices[0])

    if n_empty == 0:
        print("✅ All cells already filled")
        return populated_table

    # HSV координаты пустых точек
    target_hsv = np.column_stack([
        hue_coords[empty_indices[0]],
        sat_coords[empty_indices[1]],
        val_coords[empty_indices[2]]
    ])

    print(f"   Target points: {n_empty}")

    # 3. НОВОЕ: Параметры RBF из конфигурации
    rbf_function = algorithm_params['rbf_function']
    smoothing = algorithm_params['rbf_smoothing']

    print(f"   RBF function: {rbf_function}, smoothing: {smoothing}")

    # 4. Создаем RBF интерполяторы для каждой компоненты
    interpolated_corrections = np.zeros((n_empty, 3))

    # Подавляем предупреждения RBF о плохой обусловленности
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)

        try:
            for comp in range(3):  # H, S, V компоненты
                component_name = ['Hue', 'Saturation', 'Value'][comp]
                print(f"   Processing {component_name}...")

                # Создаем RBF интерполятор для текущей компоненты
                rbf_interpolator = Rbf(
                    known_hsv[:, 0],  # H координаты
                    known_hsv[:, 1],  # S координаты
                    known_hsv[:, 2],  # V координаты
                    known_corrections[:, comp],  # Значения коррекций
                    function=rbf_function,
                    smooth=smoothing
                )

                # Векторизованная интерполяция для всех целевых точек
                interpolated_values = rbf_interpolator(
                    target_hsv[:, 0],  # H целевых точек
                    target_hsv[:, 1],  # S целевых точек
                    target_hsv[:, 2]  # V целевых точек
                )

                interpolated_corrections[:, comp] = interpolated_values

        except Exception as e:
            print(f"❌ RBF interpolation failed: {e}")

            # Fallback к простому среднему
            print("   Using average fallback...")
            mean_corrections = np.mean(known_corrections, axis=0)
            interpolated_corrections = np.tile(mean_corrections, (n_empty, 1))

    print("✅ RBF interpolation completed")

    # 5. НОВОЕ: Применяем ограничения из конфигурации
    hue_limits = correction_limits['hue']
    sat_limits = correction_limits['sat']
    val_limits = correction_limits['val']

    interpolated_corrections[:, 0] = np.clip(interpolated_corrections[:, 0], hue_limits[0], hue_limits[1])
    interpolated_corrections[:, 1] = np.clip(interpolated_corrections[:, 1], sat_limits[0], sat_limits[1])
    interpolated_corrections[:, 2] = np.clip(interpolated_corrections[:, 2], val_limits[0], val_limits[1])

    # 6. НОВОЕ: Дополнительная фильтрация выбросов (если включена)
    if algorithm_params.get('outlier_filtering', False):
        for comp in range(3):
            values = interpolated_corrections[:, comp]

            # Используем межквартильный размах для обнаружения выбросов
            q75, q25 = np.percentile(values, [75, 25])
            iqr = q75 - q25
            outlier_threshold = 2.0  # Консервативный порог

            lower_bound = q25 - outlier_threshold * iqr
            upper_bound = q75 + outlier_threshold * iqr

            # Заменяем выбросы медианным значением
            median_value = np.median(values)
            outlier_mask = (values < lower_bound) | (values > upper_bound)

            if np.any(outlier_mask):
                interpolated_corrections[outlier_mask, comp] = median_value
                n_outliers = np.sum(outlier_mask)
                component_name = ['Hue', 'Saturation', 'Value'][comp]
                print(f"   Filtered {n_outliers} {component_name} outliers")

    # 7. Заполняем результирующие массивы
    result_hue_deltas = hue_deltas.copy()
    result_sat_deltas = sat_deltas.copy()
    result_val_deltas = val_deltas.copy()

    # Векторизованная запись результатов
    result_hue_deltas[empty_mask] = interpolated_corrections[:, 0]
    result_sat_deltas[empty_mask] = interpolated_corrections[:, 1]
    result_val_deltas[empty_mask] = interpolated_corrections[:, 2]

    # 8. Создаем результирующую таблицу
    result_table = populated_table.copy()
    result_table['hue_deltas'] = result_hue_deltas
    result_table['sat_deltas'] = result_sat_deltas
    result_table['val_deltas'] = result_val_deltas
    result_table['filled_mask'] = np.ones_like(filled_mask, dtype=bool)  # Все заполнено

    # 9. Обновляем метаданные
    method_key = f'rbf_fallback_{scenario}' if fallback_for_shepard else f'rbf_{scenario}'
    result_table['config_info']['interpolation_method'] = method_key
    result_table['config_info']['filled_cells'] = n_hue * n_sat * n_val
    result_table['config_info']['fill_ratio'] = 1.0
    result_table['config_info']['interpolated_cells'] = n_empty
    result_table['config_info']['rbf_function'] = rbf_function
    result_table['config_info']['rbf_smoothing'] = smoothing

    # НОВОЕ: Записываем примененные ограничения
    result_table['config_info']['applied_limits'] = {
        'hue_delta_range': hue_limits,
        'sat_delta_range': sat_limits,
        'val_delta_range': val_limits
    }

    result_table['config_info']['outlier_filtering'] = algorithm_params.get('outlier_filtering', False)

    print(f"✅ {scenario.capitalize()} RBF interpolation completed:")
    print(f"   Interpolated: {n_empty} new cells")
    print(f"   Method: {rbf_function} RBF (smoothing={smoothing})")
    print(f"   Applied limits: Hue {hue_limits}, Sat {sat_limits}, Val {val_limits}")
    print(f"   Outlier filtering: {algorithm_params.get('outlier_filtering', False)}")

    return result_table


def interpolate_color_correction_hybrid(populated_table: Dict[str, Any]) -> Dict[str, Any]:
    """
    Гибридный Shepard + RBF интерполятор с конфигурационными параметрами.

    Алгоритм:
    1. Пытается Shepard интерполяцию
    2. Оценивает качество результата используя пороги из конфигурации
    3. Если качество плохое - переключается на RBF

    Args:
        populated_table: Результат populate_hue_sat_table()

    Returns:
        Результат лучшего из методов
    """
    # НОВОЕ: Извлекаем параметры из конфигурации
    algorithm_params = populated_table['algorithm_params']
    quality_thresholds = populated_table['quality_thresholds']
    scenario = algorithm_params['scenario']

    print(f"🔄 Hybrid Shepard+RBF [{scenario.upper()}]:")

    # 1. Пробуем Shepard интерполяцию
    print("   Step 1: Trying Shepard interpolation...")
    shepard_result = interpolate_color_correction_sheppard(populated_table)

    # 2. Проверяем качество Shepard результата
    filled_mask = populated_table['filled_mask']
    empty_mask = ~filled_mask
    n_empty = np.sum(empty_mask)

    if n_empty == 0:
        print("   All cells already filled - using Shepard result")
        return shepard_result

    # Простая метрика качества: проверяем распределение значений
    shepard_hue_values = shepard_result['hue_deltas'][empty_mask]
    shepard_sat_values = shepard_result['sat_deltas'][empty_mask]
    shepard_val_values = shepard_result['val_deltas'][empty_mask]

    # НОВОЕ: Используем пороги из конфигурации
    boundary_threshold = quality_thresholds['boundary_clipping_threshold']
    instability_threshold = quality_thresholds['instability_threshold']
    extreme_threshold = quality_thresholds['extreme_values_threshold']

    # Флаги проблем с качеством
    quality_issues = []

    # Проверка 1: Слишком много значений на границах (признак клиппинга)
    correction_limits = populated_table['correction_limits']
    hue_limits = correction_limits['hue']

    # Проверяем близость к границам (90% от лимита)
    hue_near_boundary = np.mean(np.abs(shepard_hue_values) > abs(hue_limits[1]) * 0.9)
    if hue_near_boundary > boundary_threshold:
        quality_issues.append(f"Hue clipping: {hue_near_boundary * 100:.1f}%")

    # Проверка 2: Слишком большой разброс (нестабильность)
    hue_std = np.std(shepard_hue_values)
    if hue_std > instability_threshold:
        quality_issues.append(f"Hue instability: σ={hue_std:.1f}°")

    # Проверка 3: Много экстремальных значений
    # Используем более универсальную проверку для разных сценариев
    hue_extreme = np.abs(shepard_hue_values) > abs(hue_limits[1]) * 0.7
    sat_extreme = np.abs(shepard_sat_values) > max(abs(correction_limits['sat'][0]),
                                                   abs(correction_limits['sat'][1])) * 0.7
    val_extreme = np.abs(shepard_val_values) > max(abs(correction_limits['val'][0]),
                                                   abs(correction_limits['val'][1])) * 0.7

    extreme_values_ratio = np.mean(hue_extreme | sat_extreme | val_extreme)
    if extreme_values_ratio > extreme_threshold:
        quality_issues.append(f"Extreme values: {extreme_values_ratio * 100:.1f}%")

    # 3. Решение о методе
    if len(quality_issues) == 0:
        print("   Step 2: Shepard quality OK - using Shepard result")
        shepard_result['config_info']['quality_check'] = "passed"
        return shepard_result
    else:
        print(f"   Step 2: Shepard quality issues detected:")
        for issue in quality_issues:
            print(f"            - {issue}")
        print("   Step 3: Switching to RBF fallback...")

        # Используем RBF как fallback
        rbf_result = interpolate_color_correction_rbf(populated_table, fallback_for_shepard=True)
        rbf_result['config_info']['quality_check'] = f"shepard_failed: {'; '.join(quality_issues)}"
        rbf_result['config_info']['hybrid_decision'] = "rbf_chosen"

        return rbf_result


def generate_hue_sat_deltas_data(interpolated_table: Dict[str, Any]) -> np.ndarray:
    """
    Генерирует данные для записи в DCP тег HueSatDeltas1 (ID 50708).

    Формат Adobe DCP: массив float32 значений в порядке:
    [hue0_sat0_val0_delta_h, hue0_sat0_val0_delta_s, hue0_sat0_val0_delta_v,
     hue0_sat0_val1_delta_h, hue0_sat0_val1_delta_s, hue0_sat0_val1_delta_v, ...]

    Args:
        interpolated_table: Результат interpolate_color_correction_*() с заполненными данными

    Returns:
        np.ndarray: Плоский массив float32 для записи в DCP
    """

    # Извлекаем интерполированные дельты
    hue_deltas = interpolated_table['hue_deltas']
    sat_deltas = interpolated_table['sat_deltas']
    val_deltas = interpolated_table['val_deltas']

    # Получаем размеры сетки
    dim_x, dim_y, dim_z = hue_deltas.shape

    print(f"📊 Generating HueSatDeltas1 data:")
    print(f"   Grid dimensions: {dim_x}H × {dim_y}S × {dim_z}V")
    print(f"   Total cells: {dim_x * dim_y * dim_z}")

    # Создаем плоский массив в Adobe DCP порядке
    # Adobe порядок: для каждой HSV ячейки [delta_h, delta_s, delta_v]
    total_values = dim_x * dim_y * dim_z * 3  # 3 значения на ячейку
    dcp_data = np.zeros(total_values, dtype=np.float32)

    # Заполняем в правильном порядке (H внешний, V внутренний)
    index = 0
    for h in range(dim_x):  # Hue (внешний цикл)
        for s in range(dim_y):  # Saturation
            for v in range(dim_z):  # Value (внутренний цикл)
                # Записываем тройку [delta_h, delta_s, delta_v]
                dcp_data[index] = hue_deltas[h, s, v]  # Delta Hue
                dcp_data[index + 1] = sat_deltas[h, s, v]  # Delta Saturation
                dcp_data[index + 2] = val_deltas[h, s, v]  # Delta Value
                index += 3

    # Проверяем диапазоны (Adobe DCP спецификация)
    hue_range = (np.min(dcp_data[0::3]), np.max(dcp_data[0::3]))
    sat_range = (np.min(dcp_data[1::3]), np.max(dcp_data[1::3]))
    val_range = (np.min(dcp_data[2::3]), np.max(dcp_data[2::3]))

    print(f"   Hue deltas range: [{hue_range[0]:.2f}, {hue_range[1]:.2f}]")
    print(f"   Sat deltas range: [{sat_range[0]:.3f}, {sat_range[1]:.3f}]")
    print(f"   Val deltas range: [{val_range[0]:.3f}, {val_range[1]:.3f}]")

    # Получаем информацию о сценарии для логов
    scenario = interpolated_table['algorithm_params']['scenario']
    config_info = interpolated_table.get('config_info', {})
    interpolation_method = config_info.get('interpolation_method', 'unknown')

    print(f"   Scenario: {scenario}")
    print(f"   Method: {interpolation_method}")
    print(f"   Data size: {len(dcp_data)} values ({len(dcp_data) * 4} bytes)")

    # Проверяем на NaN и Inf
    invalid_count = np.sum(~np.isfinite(dcp_data))
    if invalid_count > 0:
        print(f"⚠️  Warning: {invalid_count} invalid values (NaN/Inf) found - replacing with 0.0")
        dcp_data[~np.isfinite(dcp_data)] = 0.0

    print("✅ HueSatDeltas1 data generated successfully")

    return dcp_data



# Исправленный main с интеграцией HSL таблиц
if __name__ == "__main__":
    # Тестовые данные патчей
    test_patches = [
        {'SAMPLE_ID': "A01", 'RGB': [13.14600, 12.61100, 11.97300], 'XYZ': [11.773, 10.213, 4.9219]},
        {'SAMPLE_ID': "A02", 'RGB': [49.23000, 48.11800, 46.60800], 'XYZ': [40.174, 36.201, 20.217]},
        {'SAMPLE_ID': "A03", 'RGB': [29.93600, 33.49200, 36.75300], 'XYZ': [17.675, 19.409, 26.983]},
        {'SAMPLE_ID': "A04", 'RGB': [16.18700, 16.10500, 15.79200], 'XYZ': [11.121, 13.530, 5.5615]},
        {'SAMPLE_ID': "A05", 'RGB': [37.11300, 40.82200, 44.24100], 'XYZ': [25.551, 24.404, 34.847]},
        {'SAMPLE_ID': "A06", 'RGB': [55.87600, 60.32000, 63.95600], 'XYZ': [31.744, 43.164, 35.249]},
        {'SAMPLE_ID': "B01", 'RGB': [38.36500, 33.18200, 27.80300], 'XYZ': [40.056, 30.947, 4.8180]},
        {'SAMPLE_ID': "B02", 'RGB': [23.29900, 28.08500, 32.73500], 'XYZ': [12.544, 11.700, 28.648]},
        {'SAMPLE_ID': "B03", 'RGB': [28.29200, 25.49000, 22.66000], 'XYZ': [30.675, 20.352, 10.837]},
        {'SAMPLE_ID': "B04", 'RGB': [12.13300, 13.14800, 14.11400], 'XYZ': [8.3961, 6.5047, 10.849]},
        {'SAMPLE_ID': "B05", 'RGB': [50.17500, 47.95100, 44.94500], 'XYZ': [36.036, 44.991, 8.9494]},
        {'SAMPLE_ID': "B06", 'RGB': [50.21800, 44.50400, 38.35600], 'XYZ': [50.203, 44.570, 6.2773]},
        {'SAMPLE_ID': "C01", 'RGB': [14.62200, 18.32500, 21.96600], 'XYZ': [7.4590, 6.0952, 23.518]},
        {'SAMPLE_ID': "C02", 'RGB': [28.59500, 29.13500, 29.15000], 'XYZ': [15.439, 23.986, 7.7482]},
        {'SAMPLE_ID': "C03", 'RGB': [20.01200, 17.08800, 14.18100], 'XYZ': [22.850, 13.022, 4.1188]},
        {'SAMPLE_ID': "C04", 'RGB': [70.29800, 63.37900, 55.64300], 'XYZ': [59.637, 60.332, 7.3520]},
        {'SAMPLE_ID': "C05", 'RGB': [34.13700, 33.98400, 33.80200], 'XYZ': [30.450, 20.015, 22.947]},
        {'SAMPLE_ID': "C06", 'RGB': [31.93000, 37.25800, 42.17200], 'XYZ': [13.591, 19.466, 30.479]},
        {'SAMPLE_ID': "D01", 'RGB': [128.9290, 133.0470, 135.8290], 'XYZ': [86.776, 90.361, 70.642]},
        {'SAMPLE_ID': "D02", 'RGB': [87.82600, 91.24800, 93.76600], 'XYZ': [56.865, 59.038, 48.218]},
        {'SAMPLE_ID': "D03", 'RGB': [56.62100, 58.95000, 60.69400], 'XYZ': [34.763, 36.036, 29.378]},
        {'SAMPLE_ID': "D04", 'RGB': [29.61600, 30.76700, 31.61300], 'XYZ': [18.884, 19.603, 16.309]},
        {'SAMPLE_ID': "D05", 'RGB': [14.99100, 15.62700, 16.10700], 'XYZ': [8.4332, 8.7464, 7.1022]},
        {'SAMPLE_ID': "D06", 'RGB': [5.802000, 6.080000, 6.296000], 'XYZ': [3.0110, 3.0971, 2.5475]}
    ]

    print("🧪 ТЕСТ 1: Цветной позитив с малым количеством патчей")
    config = select_table_configuration(is_color=True, is_negative=False, patches_count=150)
    empty_table = create_empty_hue_sat_table(config)
    populated_table = populate_hue_sat_table(empty_table, test_patches)
    rez = interpolate_color_correction_hybrid(populated_table)
    dcp_data = generate_hue_sat_deltas_data(rez)

    print(rez)
    # 2. РАЗНАЯ интерполяция пустых ячеек по сценариям
    #if scenario == "reverse":
    #    final_table = interpolate_reverse_case(populated_table)
    #elif scenario == "bw_reverse":  # ← ПОТЕРЯННЫЙ СЦЕНАРИЙ!
    #    final_table = interpolate_bw_reverse(populated_table)
    #elif scenario == "color_correction":
    #    final_table = interpolate_color_correction(populated_table)


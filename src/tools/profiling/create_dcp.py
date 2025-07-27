#, `median_rgb`
# Получаем температуру из вашей функции
temperature = get_WB(image_path)
illuminant_code = temp_to_illuminant(temperature)

# WB коррекция патчей
wb_multipliers = rawpy.imread(image_path).camera_whitebalance
wb_corrected_rgb = apply_wb_to_patches(rgb_patches, wb_multipliers)

# Вычисляем матрицу
color_matrix = calculate_color_matrix(wb_corrected_rgb, xyz_reference)

# DCP с правильным иллюминантом
tags = {
    50721: color_matrix.flatten(),
    50778: illuminant_code,  # правильный источник света!
    50964: np.linalg.inv(color_matrix).flatten()
}



def calculate_color_matrix(rgb_patches, xyz_reference):
    """
    rgb_patches: [[R1,G1,B1], [R2,G2,B2], ...] - ваши извлеченные RGB
    xyz_reference: [[X1,Y1,Z1], [X2,Y2,Z2], ...] - эталонные XYZ
    """

    # Нормализация RGB (если еще не сделана)
    rgb = np.array(rgb_patches, dtype=np.float64)
    rgb = rgb / 65535.0  # для 16-bit данных

    xyz = np.array(xyz_reference, dtype=np.float64)

    # Матрица RGB → XYZ методом наименьших квадратов
    color_matrix, residuals, rank, s = np.linalg.lstsq(rgb, xyz, rcond=None)

    return color_matrix.T  # транспонируем для DCP формата

def apply_wb_to_patches(rgb_patches, wb_multipliers):
    """
    rgb_patches: ваши извлеченные RGB значения
    wb_multipliers: [r_mul, g_mul, b_mul] из camera_whitebalance
    """
    wb_corrected = []
    r_mul, g_mul, b_mul = wb_multipliers

    for r, g, b in rgb_patches:
        r_corrected = r * r_mul
        g_corrected = g * g_mul
        b_corrected = b * b_mul
        wb_corrected.append([r_corrected, g_corrected, b_corrected])

    return np.array(wb_corrected)


def create_dcp_for_unknown_light(color_matrix):
    # Не важно какой был свет при съемке!
    # CalibrationIlluminant1 = 21 (D65) - стандартное значение
    # Матрица сама компенсирует искажения

    tags = {
        50721: color_matrix.flatten(),  # ColorMatrix1
        50778: 21,  # D65 - условное значение
        50964: np.linalg.inv(color_matrix).flatten()  # ForwardMatrix1
    }

def temp_to_illuminant(temperature):
    """Преобразование температуры в DNG illuminant код"""
    if 2800 <= temperature <= 3200:
        return 17  # Standard Illuminant A (tungsten)
    elif 4800 <= temperature <= 5200:
        return 23  # D50
    elif 6400 <= temperature <= 6600:
        return 21  # D65
    elif 5400 <= temperature <= 5600:
        return 20  # D55
    else:
        return 21  # D65 по умолчанию


✅ Используем только доступные данные:

    .ti3 от цифровой камеры: digital_3000K.ti3 и digital_5000K.ti3

    .ti3 от плёнки: film_3000K.ti3 и film_5000K.ti3

🔧 Шаг за шагом: создание адаптивного DCP
🔹 Шаг 1. Интерполяция .ti3 под 3200K и 2800K

# Пример: 3200K между 3000K и 5000K -> вес = (3200−3000)/(5000−3000) = 0.1
python interp_ti3.py film_3000K.ti3 film_5000K.ti3 0.1 film_3200K.ti3
python interp_ti3.py film_3000K.ti3 film_5000K.ti3 -0.1 film_2800K.ti3

Скрипт interp_ti3.py создаёт интерполированные .ti3 по температуре.
🔹 Шаг 2. Создание DCP с помощью dcptool

dcptool make \
  --negative \
  --input film_3000K.ti3 \
  --input film_2800K.ti3 \
  --input film_3200K.ti3 \
  --output DCP_Neg_3000K_wide.dcp \
  --name "BW Negative Wide 3000K" \
  --temperature 2800 3000 3200

    --negative — обращение негатива в позитив.

    Температуры задаются в возрастающем порядке.

    .ti3 должны соответствовать этим температурам.
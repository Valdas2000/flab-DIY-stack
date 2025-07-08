# project.pro

# Указываем все .ui файлы
FORMS = main_window.ui \
        settings_dialog.ui \
        about_dialog.ui \
        export_dialog.ui \
        login_dialog.ui

# Указываем .py файлы (если есть tr() в коде)
SOURCES = *.py

# Целевые языки
TRANSLATIONS = translations/app_ru.ts \
               translations/app_en.ts \
               translations/app_de.ts

# Кодировка (важно!)
CODECFORTR = UTF-8

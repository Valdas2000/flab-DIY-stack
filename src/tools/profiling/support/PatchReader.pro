# project.pro

# .ui files here
FORMS = main_window.ui 
#        settings_dialog.ui \
#        about_dialog.ui \
#        export_dialog.ui \
#        login_dialog.ui

# .py files (tr() is a must in the code)
SOURCES = *.py

# Целевые языки
TRANSLATIONS = translations/app_ru.ts \
               translations/app_en.ts \
               translations/app_pl.ts

# Encoding (essential!)
CODECFORTR = UTF-8

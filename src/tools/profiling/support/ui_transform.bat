pyside6-uic patch_reader.ui -o ../patch_reader_ui.py
pyside6-uic create_project_dlg.ui -o ../create_project_dlg_ui.py
pyside6-uic show_graphics_board.ui -o ../show_graphics_ui.py

rem pylupdate5 patch_reader.ui -ts ../translations/PatchReader_en.ts
rem pylupdate5 find_proper_breketing.py -ts translations/translations.ts

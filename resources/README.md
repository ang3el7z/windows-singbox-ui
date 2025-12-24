# Qt Resource System (QRC) для ресурсов

## Обзор

Ресурсы приложения (иконка и шрифт) зашиты в код через Qt Resource System (QRC), а не копируются как отдельные файлы. Это гарантирует, что ресурсы всегда доступны внутри приложения, независимо от структуры файлов.

## Что вшивается

1. **`app.ico`** - Иконка приложения (собственная, не из qtawesome)
   - Находится в `resources/icons/app.ico`
   - Используется для отображения иконки в окне, трее и т.д.
   - Это обычный файл иконки Windows (.ico)

2. **`materialdesignicons5-webfont-5.9.55.ttf`** - Шрифт Material Design Icons
   - Находится в `resources/fonts/`
   - Это ШРИФТ с символами-иконками (не отдельные файлы иконок)
   - Используется для программной отрисовки иконок через `icon_helper.py`
   - Шрифт был скопирован из qtawesome, но мы используем только шрифт, не саму библиотеку

## Структура

```
resources/
 ├── app.qrc          # Описание ресурсов Qt
 ├── icons/
 │   └── app.ico      # Иконка приложения
 └── fonts/
     └── materialdesignicons5-webfont-5.9.55.ttf  # Шрифт для иконок
```

## Компиляция QRC

QRC файл компилируется в Python модуль `scripts/resources_rc.py`.

### Автоматическая компиляция

При сборке через PyInstaller (`.spec` файл) QRC автоматически компилируется, если `scripts/resources_rc.py` отсутствует.

### Ручная компиляция

Если нужно скомпилировать вручную:

```bash
# Windows
py -m PyQt5.pyrcc_main resources/app.qrc -o scripts/resources_rc.py

# Или через скрипт
py scripts/build_qrc.py
```

## Использование

### Иконка приложения

Иконка загружается через `IconManager`:

```python
from utils.icon_manager import get_icon, set_application_icon, set_window_icon

# Получить иконку
icon = get_icon()

# Установить для приложения
set_application_icon(app)

# Установить для окна
set_window_icon(window)
```

Внутри `IconManager` используется путь Qt Resource:
```python
QIcon(":/icons/app.ico")
```

### Иконки из шрифта

Иконки из встроенного шрифта загружаются через `icon_helper`:

```python
from utils.icon_helper import icon

# Создать QIcon
icon_obj = icon("mdi.plus").icon()

# Создать QPixmap
pixmap = icon("mdi.delete").pixmap(24, 24)
```

**Важно:** Это НЕ отдельные файлы иконок! Это символы из шрифта Material Design Icons:
- Шрифт содержит тысячи символов-иконок
- Мы используем только нужные нам иконки через Unicode коды
- Коды символов определены в `utils/icon_helper.py` в словаре `MDI_ICONS`
- Иконки отрисовываются программно из символов шрифта

## Важно

1. **`scripts/resources_rc.py` должен быть скомпилирован** перед запуском приложения
2. **Иконка и шрифты НЕ добавляются в `datas`** в `.spec` файле - они зашиты через QRC
3. **`scripts.resources_rc` добавлен в `hiddenimports`** в `.spec` для PyInstaller
4. **Иконка для exe-файла** (`icon=` в EXE) остается отдельной - это иконка самого exe в проводнике
5. **Шрифт Material Design Icons** должен быть скопирован в `resources/fonts/` перед компиляцией QRC (см. `resources/fonts/README.md`)

## Преимущества

✅ Иконка и шрифты всегда доступны внутри приложения  
✅ Не зависит от структуры файлов после распаковки  
✅ Один источник истины для ресурсов  
✅ Правильная работа с AppUserModelID в Windows  
✅ Нет зависимости от внешних библиотек (qtawesome)  
✅ Production-ready решение


# Code

Эта папка предназначена для вычислительной части проекта.

- `src/` — основной код
- `notebooks/` — черновые эксперименты и визуализация

Здесь будет код для:
- вычисления точек Лагранжа;
- интегрирования траекторий;
- построения графиков и анимаций.

## Быстрый запуск

Пример для системы Солнце - Земля и точки `L1`:

```bash
python3 code/src/run_simulation.py --point L1 --dx 1e-4 --t-max 6 --dt 0.002
```

Пример для устойчивой точки `L4`:

```bash
python3 code/src/run_simulation.py --point L4 --dx 1e-3 --vy 0.02 --t-max 20 --dt 0.002
```

Готовый набор более понятных демонстрационных картинок:

```bash
python3 code/src/make_showcase.py
```

Скрипт сохраняет:
- `results/sun_earth_lagrange_points_coordinates.json` — координаты всех `L1-L5`
- `results/figures/*.png` — статическую траекторию
- `results/figures/*_3d.png` — 3D-вид сцены
- `results/figures/*.svg` — векторные версии рисунков без потери качества при увеличении
- `results/archive/html_animations/*.html` — архивные HTML-анимации
- `results/*_summary.json` — параметры конкретного запуска

## Живая анимация через pygame

После установки `pygame` можно открыть отдельное окно с живой анимацией:

```bash
python3 code/src/pygame_viewer.py --point L1 --dx 1e-4 --t-max 8
```

Пример для устойчивой точки `L4`:

```bash
python3 code/src/pygame_viewer.py --point L4 --dx 1e-3 --vy 0.02 --t-max 20
```

Пример в `3D`-режиме с ненулевым отклонением по `z`:

```bash
python3 code/src/pygame_viewer.py --mode 3d --point L4 --dx 1e-4 --dz 5e-4 --vy -0.0002 --vz 0.0002 --t-max 30
```

Пример в `3D`-режиме для неустойчивой точки:

```bash
python3 code/src/pygame_viewer.py --mode 3d --point L1 --dx 1e-4 --dz 3e-4 --t-max 16
```

Управление в окне:
- `Пробел` — пауза
- `R` — начать заново
- `Стрелка вверх` — ускорить
- `Стрелка вниз` — замедлить
- `Tab` — переключить локальный вид `2D/3D`
- `A / D` — повернуть 3D-сцену
- `W / S` — изменить наклон 3D-камеры
- `Esc` — выход

На экране:
- слева — общая схема Солнце - Земля и все `L1-L5`
- справа — крупный вид около выбранной точки
- справа в легенде — расшифровка цветов, текущее время и расстояние до `Ln`

## Понятные имена файлов

- `sun_earth_lagrange_points_map.*` — карта системы Солнце - Земля и всех точек `L1-L5`
- `sun_earth_l1_unstable_2d.*` — 2D-график для неустойчивой точки `L1`
- `sun_earth_l1_unstable_3d.*` — 3D-график для неустойчивой точки `L1`
- `archive/html_animations/sun_earth_l1_unstable_animation.html` — архивная HTML-анимация для `L1`
- `sun_earth_l1_unstable_summary.json` — параметры запуска для `L1`
- `sun_earth_l4_stable_2d.*` — 2D-график для устойчивой точки `L4`
- `sun_earth_l4_stable_3d.*` — 3D-график для устойчивой точки `L4`
- `archive/html_animations/sun_earth_l4_stable_animation.html` — архивная HTML-анимация для `L4`
- `sun_earth_l4_stable_summary.json` — параметры запуска для `L4`

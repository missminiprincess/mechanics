# Code

Основной код проекта теперь живёт в `src/mechanics/`.

Папка `code/` оставлена как слой совместимости:

- `code/src/run_simulation.py` — старый entrypoint, теперь проксирует в новый CLI
- `code/src/make_showcase.py` — старый showcase entrypoint, теперь проксирует в новый CLI
- `code/src/cr3bp.py` — тонкий compatibility module поверх новой пакетной структуры
- `code/src/pygame_viewer.py` — deprecated stub; вместо него используется `plotly` HTML dashboard

Новая основная структура:

- `src/mechanics/core/` — математика и численный пайплайн
- `src/mechanics/viz/` — статическая и интерактивная визуализация
- `src/mechanics/io/` — экспорт JSON и файловых артефактов
- `src/mechanics/cli/` — команды `simulate` и `showcase`

## Быстрый запуск

Новый CLI:

```bash
PYTHONPATH=src python3 -m mechanics.cli.main simulate --point L1 --dx 1e-4 --t-max 6 --dt 0.002
```

Готовый набор основных фигур:

```bash
PYTHONPATH=src python3 -m mechanics.cli.main showcase
```

Что сохраняется:

- `results/runs/*.json` — summary конкретного запуска
- `results/figures/*_2d.png` — статическая 2D-траектория
- `results/figures/*_3d.png` — статическая 3D-сцена
- `results/figures/*.svg` — векторные версии рисунков
- `results/html/*.html` — интерактивные `plotly` dashboards

## Совместимость со старыми командами

Старые команды всё ещё работают как thin wrappers:

```bash
python3 code/src/run_simulation.py --point L1 --dx 1e-4 --t-max 6 --dt 0.002
python3 code/src/make_showcase.py
```

`pygame`-viewer выведен из основного пути. Вместо него используется интерактивный HTML в `results/html/`.

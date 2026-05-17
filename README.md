# Проект: точки Лагранжа

Проект посвящён точкам Лагранжа в ограниченной круговой задаче трёх тел.
Он состоит из двух частей:

- теоретическая часть в `TeX`
- вычислительная часть с моделированием и визуализацией траекторий

## Структура проекта

```text
mechanics/
├─ README.md
├─ pyproject.toml
├─ .gitignore
├─ docs/
│  ├─ tex/
│  └─ sources/
├─ src/
│  └─ mechanics/
│     ├─ core/
│     ├─ viz/
│     ├─ io/
│     └─ cli/
├─ code/
│  └─ src/
├─ results/
│  ├─ figures/
│  ├─ html/
│  └─ runs/
├─ data/
├─ notebooks/
└─ scripts/
```

## Что где лежит

- `src/mechanics/core/` — математическая модель, точки Лагранжа, динамика и интегрирование
- `src/mechanics/viz/` — статическая `matplotlib`-графика и интерактивные `plotly` dashboards
- `src/mechanics/io/` — экспорт JSON и организация выходных файлов
- `src/mechanics/cli/` — команды `simulate` и `showcase`
- `docs/tex/` — исходники отчёта
- `results/figures/` — статические `png/svg`
- `results/html/` — интерактивные `html`
- `results/runs/` — summary по каждому запуску
- `code/src/` — compatibility wrappers для старых путей запуска

## Быстрый запуск

Один запуск:

```bash
PYTHONPATH=src python3 -m mechanics.cli.main simulate --point L1 --dx 1e-4 --t-max 6 --dt 0.002
```

Набор базовых демонстраций:

```bash
PYTHONPATH=src python3 -m mechanics.cli.main showcase
```

Что создаётся:

- `results/runs/*.json`
- `results/figures/*_2d.png`
- `results/figures/*_3d.png`
- `results/figures/*.svg`
- `results/html/*.html`

## Совместимость

Старые скрипты `code/src/run_simulation.py` и `code/src/make_showcase.py` оставлены как тонкие wrappers.
Старый `pygame` viewer выведен из основного пути; вместо него используется `plotly` dashboard.

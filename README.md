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
├─ mechanics/
│  ├─ core/
│  ├─ viz/
│  ├─ io/
│  └─ cli/
├─ results/
│  ├─ figures/
│  ├─ html/
│  └─ runs/
```

## Что где лежит

- `mechanics/core/` — математическая модель, точки Лагранжа, динамика и интегрирование
- `mechanics/viz/` — статическая `matplotlib`-графика и интерактивные `plotly` dashboards
- `mechanics/io/` — экспорт JSON и организация выходных файлов
- `mechanics/cli/` — команды `simulate` и `showcase`
- `docs/tex/` — исходники отчёта
- `results/figures/` — статические `png/svg`
- `results/html/` — интерактивные `html`
- `results/runs/` — summary по каждому запуску

## Быстрый запуск

Требуется Python 3.13 или новее.

Подготовка окружения:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pre-commit install
```

Один запуск:

```bash
python -m mechanics.cli.main simulate --point L1 --dx 1e-4 --t-max 6 --dt 0.002
```

Набор базовых демонстраций:

```bash
python -m mechanics.cli.main showcase
```

Что создаётся:

- `results/runs/*.json`
- `results/runs/*_trajectory.csv`
- `results/figures/*_2d.png`
- `results/figures/*_3d.png`
- `results/figures/*.svg`
- `results/html/*.html`

Для `showcase` дополнительно создаётся интерактивное сравнение:

- `results/html/sun_earth_showcase_comparison.html`

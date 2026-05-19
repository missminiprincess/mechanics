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
- `mechanics/cli/` — команды `simulate` и `showcase`, включая выбор системы через `--system`
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
python -m mechanics.cli.main simulate --system sun-earth --point L1 --dx 1e-4 --t-max 6 --dt 0.002
```

Набор базовых демонстраций:

```bash
python -m mechanics.cli.main showcase --system sun-earth
```

Поддерживаемые системы:

- `sun-earth` — Солнце-Земля
- `earth-moon` — Земля-Луна
- `sun-jupiter` — Солнце-Юпитер

Что создаётся:

- `results/runs/*.json`
- `results/runs/*_trajectory.csv`
- `results/figures/*_2d.png`
- `results/figures/*_3d.png`
- `results/figures/*.svg`
- `results/html/*.html`

Для `showcase` создаётся единый интерактивный dashboard:

- `results/html/sun_earth_showcase.html`

В dashboard входят вкладки для базовых запусков `L1` и `L4`, сравнение устойчивости,
одинаковое начальное возмущение, серия амплитуд `dx` и сравнение шага интегрирования `dt`.
JSON summary и CSV-траектории дополнительно содержат физические масштабы в километрах/сутках,
порог ухода, время ухода, рост отклонения и контроль интеграла Якоби.

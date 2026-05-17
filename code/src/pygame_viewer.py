"""Interactive pygame viewer for CR3BP trajectories near Lagrange points.

This script opens a live window with two large panels:
- a global Sun-Earth map with all five Lagrange points
- a local zoom around the selected point with the animated trajectory

Controls:
- Space: pause / resume
- R: restart animation
- Up / Down: faster / slower playback
- Esc or close window: exit
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pygame

from cr3bp import (
    SimulationConfig,
    initial_state_from_point,
    integrate_rk4,
    lagrange_points,
    sun_earth_system,
)


BACKGROUND = (5, 7, 13)
PANEL_BG = (7, 11, 20)
PANEL_BORDER = (60, 72, 92)
GRID = (36, 48, 67)
TEXT = (232, 238, 255)
MUTED = (160, 175, 205)
SUN = (255, 176, 0)
EARTH = (78, 161, 255)
TARGET = (255, 91, 91)
START = (35, 209, 96)
END = (255, 123, 0)
TRACK = (84, 201, 255)
TRACK_FADE = (255, 95, 95)
OTHER_POINT = (120, 132, 158)


@dataclass(frozen=True)
class ViewerConfig:
    mode: str
    point_name: str
    dx: float
    dy: float
    dz: float
    vx: float
    vy: float
    vz: float
    t_max: float
    dt: float
    frame_stride: int
    width: int
    height: int
    fps: int
    auto_quit_seconds: float | None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Open a live pygame animation for motion near a chosen Sun-Earth Lagrange point."
    )
    parser.add_argument("--mode", default="2d", choices=["2d", "3d"], help="Local panel mode")
    parser.add_argument("--point", default="L1", choices=["L1", "L2", "L3", "L4", "L5"])
    parser.add_argument("--dx", type=float, default=1e-4, help="Initial x offset from the selected point")
    parser.add_argument("--dy", type=float, default=0.0, help="Initial y offset from the selected point")
    parser.add_argument("--dz", type=float, default=0.0, help="Initial z offset from the selected point")
    parser.add_argument("--vx", type=float, default=0.0, help="Initial velocity along x")
    parser.add_argument("--vy", type=float, default=0.0, help="Initial velocity along y")
    parser.add_argument("--vz", type=float, default=0.0, help="Initial velocity along z")
    parser.add_argument("--t-max", type=float, default=20.0, help="Final normalized integration time")
    parser.add_argument("--dt", type=float, default=0.002, help="Time step for RK4")
    parser.add_argument("--frame-stride", type=int, default=6, help="Use every N-th integrated point for display")
    parser.add_argument("--width", type=int, default=1920, help="Window width in pixels")
    parser.add_argument("--height", type=int, default=1080, help="Window height in pixels")
    parser.add_argument("--fps", type=int, default=60, help="Target frames per second")
    parser.add_argument(
        "--auto-quit-seconds",
        type=float,
        default=None,
        help="Close automatically after the given wall-clock time. Useful for headless checks.",
    )
    return parser


def map_point(point: tuple[float, float], bounds: tuple[float, float, float, float], rect: pygame.Rect) -> tuple[int, int]:
    x, y = point
    x_min, x_max, y_min, y_max = bounds
    sx = rect.left + (x - x_min) / (x_max - x_min) * rect.width
    sy = rect.bottom - (y - y_min) / (y_max - y_min) * rect.height
    return int(round(sx)), int(round(sy))


def padded_bounds(x_min: float, x_max: float, y_min: float, y_max: float, pad_ratio: float = 0.1) -> tuple[float, float, float, float]:
    dx = max(x_max - x_min, 1e-8)
    dy = max(y_max - y_min, 1e-8)
    pad_x = dx * pad_ratio
    pad_y = dy * pad_ratio
    return x_min - pad_x, x_max + pad_x, y_min - pad_y, y_max + pad_y


def map_local_3d_point(
    point_xyz: tuple[float, float, float],
    radius: float,
    rect: pygame.Rect,
    azimuth_deg: float,
    elevation_deg: float,
) -> tuple[int, int]:
    azimuth = np.deg2rad(azimuth_deg)
    elevation = np.deg2rad(elevation_deg)
    x, y, z = point_xyz

    cos_a = float(np.cos(azimuth))
    sin_a = float(np.sin(azimuth))
    cos_e = float(np.cos(elevation))
    sin_e = float(np.sin(elevation))

    # Rotate around the z axis, then around the x axis.
    x1 = cos_a * x - sin_a * y
    y1 = sin_a * x + cos_a * y
    z1 = z

    x2 = x1
    y2 = cos_e * y1 - sin_e * z1
    z2 = sin_e * y1 + cos_e * z1

    # Orthographic projection with z shown vertically.
    sx = rect.centerx + (x2 / radius) * (rect.width * 0.42)
    sy = rect.centery - (z2 / radius) * (rect.height * 0.42)
    # A small depth bias makes front-facing points slightly lower and easier to read.
    sy -= (y2 / radius) * 24.0
    return int(round(sx)), int(round(sy))


def draw_panel_frame(surface: pygame.Surface, rect: pygame.Rect, title: str, title_font, text_font) -> None:
    pygame.draw.rect(surface, PANEL_BG, rect, border_radius=18)
    pygame.draw.rect(surface, PANEL_BORDER, rect, width=2, border_radius=18)
    title_surface = title_font.render(title, True, TEXT)
    surface.blit(title_surface, (rect.left + 18, rect.top + 14))
    hint = text_font.render("Система координат во вращающейся системе", True, MUTED)
    surface.blit(hint, (rect.left + 18, rect.top + 52))


def draw_grid(surface: pygame.Surface, rect: pygame.Rect, bounds: tuple[float, float, float, float], steps: int = 6) -> None:
    x_min, x_max, y_min, y_max = bounds
    for i in range(1, steps):
        x = x_min + (x_max - x_min) * i / steps
        y = y_min + (y_max - y_min) * i / steps
        p1 = map_point((x, y_min), bounds, rect)
        p2 = map_point((x, y_max), bounds, rect)
        pygame.draw.line(surface, GRID, p1, p2, 1)
        p3 = map_point((x_min, y), bounds, rect)
        p4 = map_point((x_max, y), bounds, rect)
        pygame.draw.line(surface, GRID, p3, p4, 1)


def draw_polyline(surface: pygame.Surface, points_xy: np.ndarray, bounds: tuple[float, float, float, float], rect: pygame.Rect) -> None:
    if len(points_xy) < 2:
        return
    screen_points = [map_point((float(x), float(y)), bounds, rect) for x, y in points_xy]
    for index in range(1, len(screen_points)):
        color_mix = index / max(len(screen_points) - 1, 1)
        color = (
            int(TRACK[0] * (1.0 - color_mix) + TRACK_FADE[0] * color_mix),
            int(TRACK[1] * (1.0 - color_mix) + TRACK_FADE[1] * color_mix),
            int(TRACK[2] * (1.0 - color_mix) + TRACK_FADE[2] * color_mix),
        )
        pygame.draw.line(surface, color, screen_points[index - 1], screen_points[index], 3)


def draw_marker(
    surface: pygame.Surface,
    world_xy: tuple[float, float],
    bounds: tuple[float, float, float, float],
    rect: pygame.Rect,
    color: tuple[int, int, int],
    radius: int,
    label: str,
    font,
    label_offset: tuple[int, int] = (10, -16),
) -> None:
    px, py = map_point(world_xy, bounds, rect)
    pygame.draw.circle(surface, color, (px, py), radius)
    pygame.draw.circle(surface, (10, 10, 10), (px, py), radius, width=2)
    label_surface = font.render(label, True, color)
    surface.blit(label_surface, (px + label_offset[0], py + label_offset[1]))


def draw_legend(
    surface: pygame.Surface,
    rect: pygame.Rect,
    config: ViewerConfig,
    rel_distance: float,
    current_time: float,
    speed_multiplier: int,
    view_mode: str,
    font,
    small_font,
) -> None:
    legend_x = rect.left + 18
    y = rect.top + 20

    title = font.render("Обозначения", True, TEXT)
    surface.blit(title, (legend_x, y))
    y += 40

    items = [
        (SUN, "Солнце"),
        (EARTH, "Земля"),
        (TARGET, f"Выбранная точка {config.point_name}"),
        (START, "Начальная точка"),
        (END, "Текущее положение тела"),
        (TRACK, "Траектория движения"),
    ]
    for color, label in items:
        pygame.draw.circle(surface, color, (legend_x + 10, y + 10), 8)
        text_surface = small_font.render(label, True, TEXT)
        surface.blit(text_surface, (legend_x + 28, y))
        y += 34

    y += 16
    lines = [
        f"Режим локального окна: {view_mode.upper()}",
        f"t = {current_time:.3f}",
        f"Расстояние до {config.point_name}: {rel_distance:.6f}",
        f"Смещение: dx={config.dx:g}, dy={config.dy:g}, dz={config.dz:g}",
        f"Скорость: vx={config.vx:g}, vy={config.vy:g}, vz={config.vz:g}",
        f"Интегрирование: t_max={config.t_max:g}, dt={config.dt:g}",
        f"Скорость анимации: x{speed_multiplier}",
    ]
    for line in lines:
        text_surface = small_font.render(line, True, MUTED)
        surface.blit(text_surface, (legend_x, y))
        y += 28

    y += 12
    controls = [
        "Пробел - пауза",
        "R - перезапуск",
        "Стрелка вверх - быстрее",
        "Стрелка вниз - медленнее",
        "Tab - 2D / 3D",
        "A / D - поворот 3D по горизонтали",
        "W / S - наклон 3D по вертикали",
        "Esc - выход",
    ]
    for line in controls:
        text_surface = small_font.render(line, True, TEXT)
        surface.blit(text_surface, (legend_x, y))
        y += 26


def main() -> None:
    args = build_parser().parse_args()
    config = ViewerConfig(
        mode=args.mode,
        point_name=args.point,
        dx=args.dx,
        dy=args.dy,
        dz=args.dz,
        vx=args.vx,
        vy=args.vy,
        vz=args.vz,
        t_max=args.t_max,
        dt=args.dt,
        frame_stride=max(1, args.frame_stride),
        width=args.width,
        height=args.height,
        fps=max(10, args.fps),
        auto_quit_seconds=args.auto_quit_seconds,
    )

    system = sun_earth_system()
    points = lagrange_points(system.mu)
    sim_config = SimulationConfig(
        point_name=config.point_name,
        dx=config.dx,
        dy=config.dy,
        dz=config.dz,
        vx=config.vx,
        vy=config.vy,
        vz=config.vz,
        t_max=config.t_max,
        dt=config.dt,
        sample_stride=config.frame_stride,
    )
    initial_state = initial_state_from_point(points[config.point_name], sim_config)
    times, states = integrate_rk4(initial_state, system.mu, config.t_max, config.dt)

    times = times[:: config.frame_stride]
    states = states[:: config.frame_stride]
    target = points[config.point_name]

    # Bounds for the two visual panels.
    global_x = np.concatenate([states[:, 0], np.array([-system.mu, 1.0 - system.mu]), np.array([p[0] for p in points.values()])])
    global_y = np.concatenate([states[:, 1], np.array([0.0, 0.0]), np.array([p[1] for p in points.values()])])
    global_bounds = padded_bounds(float(global_x.min()), float(global_x.max()), float(global_y.min()), float(global_y.max()), 0.14)

    dx_rel = states[:, 0] - target[0]
    dy_rel = states[:, 1] - target[1]
    dz_rel = states[:, 2] - target[2]
    local_radius = max(float(np.max(np.abs(dx_rel))), float(np.max(np.abs(dy_rel))), float(np.max(np.abs(dz_rel))), 0.01) * 1.2
    local_bounds = (-local_radius, local_radius, -local_radius, local_radius)

    pygame.init()
    pygame.display.set_caption(f"Точки Лагранжа: анимация около {config.point_name}")
    screen = pygame.display.set_mode((config.width, config.height))
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("Arial", 28, bold=True)
    font = pygame.font.SysFont("Arial", 24, bold=True)
    text_font = pygame.font.SysFont("Arial", 20)
    small_font = pygame.font.SysFont("Arial", 18)

    margin = 22
    legend_width = 370
    panel_gap = 18
    content_width = config.width - legend_width - margin * 2 - panel_gap
    panel_width = content_width // 2
    panel_height = config.height - margin * 2
    global_rect = pygame.Rect(margin, margin, panel_width, panel_height)
    local_rect = pygame.Rect(margin + panel_width + panel_gap, margin, panel_width, panel_height)
    legend_rect = pygame.Rect(config.width - legend_width - margin, margin, legend_width, panel_height)

    plot_pad_left = 22
    plot_pad_right = 20
    plot_pad_bottom = 28
    plot_pad_top = 88
    global_plot = global_rect.inflate(-(plot_pad_left + plot_pad_right), -(plot_pad_top + plot_pad_bottom))
    global_plot.topleft = (global_rect.left + plot_pad_left, global_rect.top + plot_pad_top)
    local_plot = local_rect.inflate(-(plot_pad_left + plot_pad_right), -(plot_pad_top + plot_pad_bottom))
    local_plot.topleft = (local_rect.left + plot_pad_left, local_rect.top + plot_pad_top)

    frame_index = 0
    speed_multiplier = 1
    paused = False
    elapsed_wall_time = 0.0
    view_mode = config.mode
    azimuth_deg = -55.0
    elevation_deg = 28.0

    running = True
    while running:
        dt_wall = clock.tick(config.fps) / 1000.0
        elapsed_wall_time += dt_wall
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    frame_index = 0
                    paused = False
                elif event.key == pygame.K_UP:
                    speed_multiplier = min(speed_multiplier + 1, 20)
                elif event.key == pygame.K_DOWN:
                    speed_multiplier = max(speed_multiplier - 1, 1)
                elif event.key == pygame.K_TAB:
                    view_mode = "3d" if view_mode == "2d" else "2d"
                elif event.key == pygame.K_a:
                    azimuth_deg -= 8.0
                elif event.key == pygame.K_d:
                    azimuth_deg += 8.0
                elif event.key == pygame.K_w:
                    elevation_deg = min(elevation_deg + 5.0, 85.0)
                elif event.key == pygame.K_s:
                    elevation_deg = max(elevation_deg - 5.0, -85.0)

        if config.auto_quit_seconds is not None and elapsed_wall_time >= config.auto_quit_seconds:
            running = False

        if not paused:
            frame_index = min(frame_index + speed_multiplier, len(states) - 1)

        current = states[frame_index]
        current_rel = (float(current[0] - target[0]), float(current[1] - target[1]))
        current_time = float(times[frame_index])
        rel_distance = float(np.hypot(current_rel[0], current_rel[1]))

        screen.fill(BACKGROUND)
        draw_panel_frame(screen, global_rect, "Общая схема Солнце - Земля", title_font, text_font)
        local_title = (
            f"Крупный вид около {config.point_name} в плоскости"
            if view_mode == "2d"
            else f"Крупный 3D-вид около {config.point_name}"
        )
        draw_panel_frame(screen, local_rect, local_title, title_font, text_font)
        pygame.draw.rect(screen, PANEL_BG, legend_rect, border_radius=18)
        pygame.draw.rect(screen, PANEL_BORDER, legend_rect, width=2, border_radius=18)

        draw_grid(screen, global_plot, global_bounds)
        draw_grid(screen, local_plot, local_bounds)

        global_track = states[: frame_index + 1, :2]
        local_track = np.column_stack([dx_rel[: frame_index + 1], dy_rel[: frame_index + 1]])
        draw_polyline(screen, global_track, global_bounds, global_plot)
        if view_mode == "2d":
            draw_polyline(screen, local_track, local_bounds, local_plot)
        else:
            local_track_xyz = np.column_stack([dx_rel[: frame_index + 1], dy_rel[: frame_index + 1], dz_rel[: frame_index + 1]])
            projected = [
                map_local_3d_point((float(x), float(y), float(z)), local_radius, local_plot, azimuth_deg, elevation_deg)
                for x, y, z in local_track_xyz
            ]
            for index in range(1, len(projected)):
                color_mix = index / max(len(projected) - 1, 1)
                color = (
                    int(TRACK[0] * (1.0 - color_mix) + TRACK_FADE[0] * color_mix),
                    int(TRACK[1] * (1.0 - color_mix) + TRACK_FADE[1] * color_mix),
                    int(TRACK[2] * (1.0 - color_mix) + TRACK_FADE[2] * color_mix),
                )
                pygame.draw.line(screen, color, projected[index - 1], projected[index], 3)

        draw_marker(screen, (-system.mu, 0.0), global_bounds, global_plot, SUN, 12, "Солнце", text_font, (-20, -34))
        draw_marker(screen, (1.0 - system.mu, 0.0), global_bounds, global_plot, EARTH, 10, "Земля", text_font, (10, -30))

        for name, coords in points.items():
            color = TARGET if name == config.point_name else OTHER_POINT
            radius = 9 if name == config.point_name else 6
            label = name
            draw_marker(
                screen,
                (float(coords[0]), float(coords[1])),
                global_bounds,
                global_plot,
                color,
                radius,
                label,
                text_font,
                (8, -26 if name == config.point_name else -18),
            )

        draw_marker(
            screen,
            (float(states[0, 0]), float(states[0, 1])),
            global_bounds,
            global_plot,
            START,
            8,
            "Старт",
            text_font,
            (12, 8),
        )
        draw_marker(
            screen,
            (float(current[0]), float(current[1])),
            global_bounds,
            global_plot,
            END,
            9,
            "Текущее тело",
            text_font,
            (12, -30),
        )

        if view_mode == "2d":
            # Local panel is drawn in coordinates relative to the chosen L point.
            draw_marker(screen, (0.0, 0.0), local_bounds, local_plot, TARGET, 10, config.point_name, text_font, (12, -30))
            draw_marker(screen, (dx_rel[0], dy_rel[0]), local_bounds, local_plot, START, 8, "Старт", text_font, (12, 8))
            draw_marker(screen, current_rel, local_bounds, local_plot, END, 9, "Текущее тело", text_font, (12, -30))

            # Axes crossing through the local Lagrange point.
            x_axis_a = map_point((local_bounds[0], 0.0), local_bounds, local_plot)
            x_axis_b = map_point((local_bounds[1], 0.0), local_bounds, local_plot)
            y_axis_a = map_point((0.0, local_bounds[2]), local_bounds, local_plot)
            y_axis_b = map_point((0.0, local_bounds[3]), local_bounds, local_plot)
            pygame.draw.line(screen, MUTED, x_axis_a, x_axis_b, 1)
            pygame.draw.line(screen, MUTED, y_axis_a, y_axis_b, 1)
        else:
            # 3D axes around the selected Lagrange point.
            axes = [
                ((-local_radius, 0.0, 0.0), (local_radius, 0.0, 0.0), (255, 120, 120), "ось x"),
                ((0.0, -local_radius, 0.0), (0.0, local_radius, 0.0), (120, 255, 170), "ось y"),
                ((0.0, 0.0, -local_radius), (0.0, 0.0, local_radius), (120, 180, 255), "ось z"),
            ]
            for start_axis, end_axis, axis_color, axis_label in axes:
                a = map_local_3d_point(start_axis, local_radius, local_plot, azimuth_deg, elevation_deg)
                b = map_local_3d_point(end_axis, local_radius, local_plot, azimuth_deg, elevation_deg)
                pygame.draw.line(screen, axis_color, a, b, 2)
                label_pos = map_local_3d_point(end_axis, local_radius, local_plot, azimuth_deg, elevation_deg)
                axis_surface = small_font.render(axis_label, True, axis_color)
                screen.blit(axis_surface, (label_pos[0] + 8, label_pos[1] - 14))

            target_pos = map_local_3d_point((0.0, 0.0, 0.0), local_radius, local_plot, azimuth_deg, elevation_deg)
            start_pos = map_local_3d_point((float(dx_rel[0]), float(dy_rel[0]), float(dz_rel[0])), local_radius, local_plot, azimuth_deg, elevation_deg)
            current_pos = map_local_3d_point((float(dx_rel[frame_index]), float(dy_rel[frame_index]), float(dz_rel[frame_index])), local_radius, local_plot, azimuth_deg, elevation_deg)

            pygame.draw.circle(screen, TARGET, target_pos, 10)
            pygame.draw.circle(screen, (10, 10, 10), target_pos, 10, 2)
            pygame.draw.circle(screen, START, start_pos, 8)
            pygame.draw.circle(screen, (10, 10, 10), start_pos, 8, 2)
            pygame.draw.circle(screen, END, current_pos, 9)
            pygame.draw.circle(screen, (10, 10, 10), current_pos, 9, 2)

            screen.blit(text_font.render(config.point_name, True, TARGET), (target_pos[0] + 10, target_pos[1] - 28))
            screen.blit(text_font.render("Старт", True, START), (start_pos[0] + 10, start_pos[1] + 6))
            screen.blit(text_font.render("Текущее тело", True, END), (current_pos[0] + 10, current_pos[1] - 28))
            camera_text = small_font.render(
                f"Камера: az={azimuth_deg:.0f}°, el={elevation_deg:.0f}°",
                True,
                MUTED,
            )
            screen.blit(camera_text, (local_rect.left + 18, local_rect.bottom - 64))

        status_line = (
            "Неустойчивый случай: траектория со временем уходит от точки"
            if config.point_name in {"L1", "L2", "L3"}
            else "Устойчивый случай: движение остаётся в окрестности точки"
        )
        status_surface = text_font.render(status_line, True, TEXT)
        screen.blit(status_surface, (local_rect.left + 18, local_rect.bottom - 38))

        draw_legend(screen, legend_rect, config, rel_distance, current_time, speed_multiplier, view_mode, font, small_font)

        pygame.display.flip()

        if frame_index >= len(states) - 1 and not paused:
            paused = True

    pygame.quit()


if __name__ == "__main__":
    main()

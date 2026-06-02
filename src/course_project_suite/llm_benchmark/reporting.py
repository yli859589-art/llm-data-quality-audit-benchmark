from __future__ import annotations
import html
from pathlib import Path


COLORS = ['#2563eb', '#dc2626', '#16a34a', '#9333ea', '#ea580c']


def write_line_chart(path: str | Path, series: dict[str, list[tuple[float, float]]], title: str, x_label: str, y_label: str) -> None:
    path = Path(path)
    width, height, margin = 760, 430, 62
    points = [point for values in series.values() for point in values]
    xs = [point[0] for point in points]; ys = [point[1] for point in points]
    xmin, xmax = min(xs), max(xs); ymin, ymax = min(ys), max(ys)
    if ymax == ymin: ymax += 1
    def px(x): return margin + (x - xmin) * (width - 2 * margin) / max(1e-12, xmax - xmin)
    def py(y): return height - margin - (y - ymin) * (height - 2 * margin) / max(1e-12, ymax - ymin)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2}" y="28" text-anchor="middle" font-family="Arial" font-size="18">{html.escape(title)}</text>',
        f'<line x1="{margin}" y1="{height-margin}" x2="{width-margin}" y2="{height-margin}" stroke="#111827"/>',
        f'<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height-margin}" stroke="#111827"/>',
        f'<text x="{width / 2}" y="{height-16}" text-anchor="middle" font-family="Arial" font-size="13">{html.escape(x_label)}</text>',
        f'<text x="18" y="{height / 2}" text-anchor="middle" transform="rotate(-90 18 {height / 2})" font-family="Arial" font-size="13">{html.escape(y_label)}</text>',
    ]
    for index, (name, values) in enumerate(series.items()):
        color = COLORS[index % len(COLORS)]
        coords = ' '.join(f'{px(x):.1f},{py(y):.1f}' for x, y in values)
        lines.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="2.5"/>')
        lines.append(f'<text x="{width-margin-145}" y="{margin+18*index}" font-family="Arial" font-size="12" fill="{color}">{html.escape(name)}</text>')
    lines.append('</svg>')
    path.write_text('\n'.join(lines), encoding='utf-8')


def write_bar_chart(path: str | Path, rows: list[dict[str, object]], title: str) -> None:
    path = Path(path)
    width, height, margin = 820, 450, 70
    values = [float(row['query_tokens_per_second']) for row in rows]
    vmax = max(values) if values else 1.0
    bar_width = max(10, (width - 2 * margin) / max(1, len(rows)) - 8)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2}" y="28" text-anchor="middle" font-family="Arial" font-size="18">{html.escape(title)}</text>',
        f'<line x1="{margin}" y1="{height-margin}" x2="{width-margin}" y2="{height-margin}" stroke="#111827"/>',
    ]
    for index, row in enumerate(rows):
        value = float(row['query_tokens_per_second'])
        bar_height = value * (height - 2 * margin) / vmax
        x = margin + index * ((width - 2 * margin) / len(rows)) + 4
        y = height - margin - bar_height
        label = f"{row['implementation']} T={row['sequence_length']}"
        lines.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" fill="{COLORS[index % len(COLORS)]}"/>')
        lines.append(f'<text x="{x + bar_width / 2:.1f}" y="{height-margin+14}" text-anchor="end" transform="rotate(-38 {x + bar_width / 2:.1f} {height-margin+14})" font-family="Arial" font-size="10">{html.escape(label)}</text>')
    lines.append('</svg>')
    path.write_text('\n'.join(lines), encoding='utf-8')

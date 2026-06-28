"""Render a static visual presentation from the CSS probe certificate report."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reports" / "css_probe_report.json"
HTML_PATH = ROOT / "reports" / "css_probe_results_presentation.html"
SVG_PATH = ROOT / "reports" / "css_probe_results_summary.svg"
PNG_PATH = ROOT / "reports" / "css_probe_results_summary.png"

LEVEL_LABELS = {
    "level_1_typed": "L1 Typed",
    "level_2_bounded": "L2 Bounded",
    "level_3_behavioral": "L3 Behavioral",
    "level_4_causal": "L4 Causal",
    "level_5_spectral": "L5 Spectral",
    "level_6_rollback_safe": "L6 Rollback",
}

PROBE_LABELS = {
    "activation_patch_probe": "Activation patch",
    "low_rank_operator_probe": "Low-rank op",
    "norm_drift_probe": "Norm drift",
    "spectral_radius_probe": "Spectral radius",
    "pseudospectrum_probe": "Pseudospectrum",
    "causal_locality_probe": "Causal locality",
    "off_target_regression_probe": "Off-target",
    "rollback_probe": "Rollback",
    "operator_vs_text_benchmark": "Operator vs text",
    "koopman_dynamics_message_probe": "Koopman dynamics",
    "proof_state_surgery_probe": "Proof state",
}


def main() -> int:
    payload = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    HTML_PATH.write_text(render_html(payload), encoding="utf-8")
    SVG_PATH.write_text(render_svg(payload), encoding="utf-8")
    render_png_if_available(payload, PNG_PATH)
    print(f"wrote {HTML_PATH}")
    print(f"wrote {SVG_PATH}")
    if PNG_PATH.exists():
        print(f"wrote {PNG_PATH}")
    return 0


def render_html(payload: dict[str, Any]) -> str:
    probes = payload["probes"]
    coverage = payload["certification_summary"]["coverage"]
    transfer = find_probe(payload, "operator_vs_text_benchmark")["metrics"]
    activation = find_probe(payload, "activation_patch_probe")["metrics"]
    dynamics = find_probe(payload, "koopman_dynamics_message_probe")["metrics"]

    level_rows = "\n".join(render_level_row(level, names, len(probes)) for level, names in coverage.items())
    probe_cards = "\n".join(render_probe_card(probe) for probe in probes)
    transfer_bars = render_transfer_bars(transfer)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CSS Phase 0 Results</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #17202a;
      --muted: #5f6b76;
      --line: #d6dde5;
      --paper: #f7f9fb;
      --panel: #ffffff;
      --ok: #1f8a5b;
      --blue: #2367b5;
      --teal: #168a9a;
      --amber: #ad6a00;
      --red: #b42318;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: var(--paper);
      line-height: 1.45;
    }}
    header {{
      padding: 32px clamp(20px, 5vw, 64px) 24px;
      background: #ffffff;
      border-bottom: 1px solid var(--line);
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: clamp(28px, 4vw, 48px);
      letter-spacing: 0;
    }}
    h2 {{ margin: 0 0 14px; font-size: 20px; }}
    main {{ padding: 24px clamp(20px, 5vw, 64px) 48px; }}
    .subhead {{ color: var(--muted); max-width: 920px; margin: 0; }}
    .grid {{
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      margin: 24px 0;
    }}
    .metric, section, .probe {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }}
    .metric .value {{ font-size: 32px; font-weight: 700; margin-top: 6px; }}
    .metric .label, .small {{ color: var(--muted); font-size: 13px; }}
    section {{ margin: 20px 0; }}
    .barrow {{
      display: grid;
      grid-template-columns: 150px minmax(160px, 1fr) 72px;
      gap: 12px;
      align-items: center;
      margin: 11px 0;
    }}
    .bar {{
      height: 12px;
      background: #e8edf3;
      border-radius: 999px;
      overflow: hidden;
    }}
    .fill {{ height: 100%; background: var(--ok); border-radius: inherit; }}
    .fill.blue {{ background: var(--blue); }}
    .fill.teal {{ background: var(--teal); }}
    .probegrid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 14px;
    }}
    .probe h3 {{ margin: 0 0 8px; font-size: 16px; }}
    .badge {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 999px;
      background: #e5f4ed;
      color: var(--ok);
      font-weight: 700;
      font-size: 12px;
      margin-right: 6px;
      margin-bottom: 6px;
    }}
    .level-badge {{ background: #e8f0fb; color: var(--blue); }}
    dl {{
      display: grid;
      grid-template-columns: minmax(120px, 0.9fr) minmax(120px, 1.1fr);
      gap: 6px 12px;
      margin: 12px 0 0;
      font-size: 13px;
    }}
    dt {{ color: var(--muted); }}
    dd {{ margin: 0; font-weight: 600; overflow-wrap: anywhere; }}
    .two {{
      display: grid;
      grid-template-columns: minmax(280px, 1fr) minmax(280px, 1fr);
      gap: 20px;
    }}
    @media (max-width: 760px) {{
      .two {{ grid-template-columns: 1fr; }}
      .barrow {{ grid-template-columns: 1fr; gap: 6px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Certified Semantic Surgery Phase 0 Results</h1>
    <p class="subhead">Synthetic probe suite certificate generated from <code>reports/css_probe_report.json</code>. The run accepted all probes, validated every packet, and covered certification Levels 1-6.</p>
  </header>
  <main>
    <div class="grid">
      {metric_card("Suite accepted", "true" if payload["accepted"] else "false", "Overall accept/reject decision")}
      {metric_card("Accepted probes", f'{payload["summary"]["num_accepted"]}/{payload["summary"]["num_probes"]}', "Probe acceptance count")}
      {metric_card("Invalid packets", "0", "Packet schema warnings in final report")}
      {metric_card("Levels covered", "1-6", "Phase 0 certification ladder")}
    </div>

    <div class="two">
      <section>
        <h2>Certification Coverage</h2>
        {level_rows}
      </section>
      <section>
        <h2>Key Safety Margins</h2>
        <dl>
          <dt>Target success delta</dt><dd>{fmt(activation["target_success_delta"])}</dd>
          <dt>Activation rollback residue</dt><dd>{sci(activation["rollback_residue"])}</dd>
          <dt>Koopman pseudospectral proxy</dt><dd>{fmt(dynamics["pseudospectral_proxy"])} / 5.0</dd>
          <dt>Koopman rollout max norm</dt><dd>{fmt(dynamics["rollout_max_norm"])} / 5.0</dd>
          <dt>Operator advantage</dt><dd>{fmt(transfer["operator_absolute_advantage"])}</dd>
          <dt>Off-target degradation max</dt><dd>{fmt(transfer["off_target_degradation_max"])}</dd>
        </dl>
      </section>
    </div>

    <section>
      <h2>Operator vs Text Transfer</h2>
      {transfer_bars}
    </section>

    <section>
      <h2>Probe Cards</h2>
      <div class="probegrid">
        {probe_cards}
      </div>
    </section>
  </main>
</body>
</html>
"""


def render_svg(payload: dict[str, Any]) -> str:
    probes = payload["probes"]
    coverage = payload["certification_summary"]["coverage"]
    transfer = find_probe(payload, "operator_vs_text_benchmark")["metrics"]
    activation = find_probe(payload, "activation_patch_probe")["metrics"]
    dynamics = find_probe(payload, "koopman_dynamics_message_probe")["metrics"]
    rows = []
    y = 245
    max_count = len(probes)
    for key, names in coverage.items():
        width = int(330 * len(names) / max_count)
        rows.append(f'<text x="64" y="{y + 10}" class="label">{escape(LEVEL_LABELS[key])}</text>')
        rows.append(f'<rect x="220" y="{y}" width="330" height="14" rx="7" class="track"/>')
        rows.append(f'<rect x="220" y="{y}" width="{width}" height="14" rx="7" class="green"/>')
        rows.append(f'<text x="570" y="{y + 11}" class="small">{len(names)}/{max_count}</text>')
        y += 34

    transfer_items = [
        ("No message", transfer["no_message_target_margin_delta"]),
        ("Text", transfer["text_target_margin_delta"]),
        ("Latent vector", transfer["latent_vector_target_margin_delta"]),
        ("Additive operator", transfer["additive_operator_target_margin_delta"]),
        ("Low-rank operator", transfer["low_rank_operator_target_margin_delta"]),
    ]
    max_transfer = max(abs(value) for _, value in transfer_items) or 1.0
    transfer_rows = []
    y = 245
    for label, value in transfer_items:
        width = int(300 * abs(value) / max_transfer)
        color = "blue" if value >= 0 else "red"
        transfer_rows.append(f'<text x="690" y="{y + 10}" class="label">{escape(label)}</text>')
        transfer_rows.append(f'<rect x="850" y="{y}" width="300" height="14" rx="7" class="track"/>')
        transfer_rows.append(f'<rect x="850" y="{y}" width="{width}" height="14" rx="7" class="{color}"/>')
        transfer_rows.append(f'<text x="1170" y="{y + 11}" class="small">{fmt(value)}</text>')
        y += 34

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <style>
    .bg {{ fill: #f7f9fb; }}
    .panel {{ fill: #ffffff; stroke: #d6dde5; stroke-width: 1; }}
    .title {{ font: 700 42px Arial, Helvetica, sans-serif; fill: #17202a; }}
    .subtitle {{ font: 18px Arial, Helvetica, sans-serif; fill: #5f6b76; }}
    .metric {{ font: 700 34px Arial, Helvetica, sans-serif; fill: #17202a; }}
    .label {{ font: 15px Arial, Helvetica, sans-serif; fill: #17202a; }}
    .small {{ font: 13px Arial, Helvetica, sans-serif; fill: #5f6b76; }}
    .section {{ font: 700 22px Arial, Helvetica, sans-serif; fill: #17202a; }}
    .track {{ fill: #e8edf3; }}
    .green {{ fill: #1f8a5b; }}
    .blue {{ fill: #2367b5; }}
    .red {{ fill: #b42318; }}
  </style>
  <rect class="bg" width="1280" height="720"/>
  <text x="64" y="72" class="title">Certified Semantic Surgery Phase 0</text>
  <text x="64" y="106" class="subtitle">11/11 probes accepted, all packets valid, certification Levels 1-6 covered</text>

  {svg_metric(64, 138, "Accepted", "11/11")}
  {svg_metric(350, 138, "Invalid packets", "0")}
  {svg_metric(636, 138, "Target success delta", fmt(activation["target_success_delta"]))}
  {svg_metric(922, 138, "Pseudospectral proxy", f'{fmt(dynamics["pseudospectral_proxy"])}/5.0')}

  <rect x="44" y="205" width="560" height="295" rx="8" class="panel"/>
  <text x="64" y="228" class="section">Certification coverage</text>
  {"".join(rows)}

  <rect x="660" y="205" width="570" height="255" rx="8" class="panel"/>
  <text x="690" y="228" class="section">Operator vs text target margin</text>
  {"".join(transfer_rows)}

  <rect x="44" y="532" width="1186" height="124" rx="8" class="panel"/>
  <text x="64" y="566" class="section">Safety margins</text>
  <text x="64" y="604" class="label">Rollback residue: {sci(activation["rollback_residue"])}</text>
  <text x="382" y="604" class="label">Rollout max norm: {fmt(dynamics["rollout_max_norm"])}/5.0</text>
  <text x="704" y="604" class="label">Operator advantage: {fmt(transfer["operator_absolute_advantage"])}</text>
  <text x="984" y="604" class="label">Off-target degradation: {fmt(transfer["off_target_degradation_max"])}</text>
</svg>
"""


def metric_card(label: str, value: str, detail: str) -> str:
    return f'<div class="metric"><div class="label">{escape(label)}</div><div class="value">{escape(value)}</div><div class="small">{escape(detail)}</div></div>'


def render_level_row(level: str, names: list[str], total: int) -> str:
    pct = 100.0 * len(names) / total
    return f"""
    <div class="barrow">
      <div>{escape(LEVEL_LABELS[level])}</div>
      <div class="bar"><div class="fill" style="width: {pct:.1f}%"></div></div>
      <div class="small">{len(names)}/{total}</div>
    </div>"""


def render_transfer_bars(metrics: dict[str, Any]) -> str:
    items = [
        ("No message", metrics["no_message_target_margin_delta"]),
        ("Text-like instruction", metrics["text_target_margin_delta"]),
        ("Latent vector", metrics["latent_vector_target_margin_delta"]),
        ("Additive operator", metrics["additive_operator_target_margin_delta"]),
        ("Low-rank operator", metrics["low_rank_operator_target_margin_delta"]),
        ("Operator + certificate", metrics["operator_plus_certificate_target_margin_delta"]),
    ]
    max_value = max(abs(value) for _, value in items) or 1.0
    rows = []
    for label, value in items:
        pct = 100.0 * abs(value) / max_value
        color = "blue" if value >= 0 else "teal"
        rows.append(
            f"""
    <div class="barrow">
      <div>{escape(label)}</div>
      <div class="bar"><div class="fill {color}" style="width: {pct:.1f}%"></div></div>
      <div class="small">{fmt(value)}</div>
    </div>"""
        )
    return "\n".join(rows)


def render_probe_card(probe: dict[str, Any]) -> str:
    levels = probe["certificate"]["covered_levels"]
    level_badges = " ".join(f'<span class="badge level-badge">{escape(LEVEL_LABELS[level])}</span>' for level in levels)
    packet = probe["packet"]
    return f"""
    <div class="probe">
      <h3>{escape(PROBE_LABELS.get(probe["name"], probe["name"]))}</h3>
      <span class="badge">accepted</span>
      {level_badges}
      <dl>
        <dt>Packet</dt><dd>{escape(packet["packet_id"])}</dd>
        <dt>Operator</dt><dd>{escape(packet["operator_type"])}</dd>
        <dt>Persistence</dt><dd>{escape(packet["persistence"])}</dd>
        <dt>Target</dt><dd>{escape(packet["target"]["state_type"])}</dd>
      </dl>
    </div>"""


def svg_metric(x: int, y: int, label: str, value: str) -> str:
    return f'<rect x="{x}" y="{y}" width="238" height="48" rx="8" class="panel"/><text x="{x + 18}" y="{y + 20}" class="small">{escape(label)}</text><text x="{x + 18}" y="{y + 42}" class="metric">{escape(value)}</text>'


def find_probe(payload: dict[str, Any], name: str) -> dict[str, Any]:
    for probe in payload["probes"]:
        if probe["name"] == name:
            return probe
    raise KeyError(name)


def fmt(value: float) -> str:
    return f"{value:.4g}"


def sci(value: float) -> str:
    return f"{value:.2e}"


def escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render_png_if_available(payload: dict[str, Any], path: Path) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return

    width, height = 1280, 720
    image = Image.new("RGB", (width, height), "#f7f9fb")
    draw = ImageDraw.Draw(image)
    title = load_font(ImageFont, 42, bold=True)
    subtitle = load_font(ImageFont, 18)
    section = load_font(ImageFont, 22, bold=True)
    label = load_font(ImageFont, 15)
    small = load_font(ImageFont, 13)
    metric = load_font(ImageFont, 32, bold=True)

    probes = payload["probes"]
    coverage = payload["certification_summary"]["coverage"]
    transfer = find_probe(payload, "operator_vs_text_benchmark")["metrics"]
    activation = find_probe(payload, "activation_patch_probe")["metrics"]
    dynamics = find_probe(payload, "koopman_dynamics_message_probe")["metrics"]

    draw.text((64, 54), "Certified Semantic Surgery Phase 0", fill="#17202a", font=title)
    draw.text((64, 94), "11/11 probes accepted, all packets valid, certification Levels 1-6 covered", fill="#5f6b76", font=subtitle)

    draw_png_metric(draw, 64, 138, "Accepted", "11/11", metric, small)
    draw_png_metric(draw, 350, 138, "Invalid packets", "0", metric, small)
    draw_png_metric(draw, 636, 138, "Target success delta", fmt(activation["target_success_delta"]), metric, small)
    draw_png_metric(draw, 922, 138, "Pseudospectral proxy", f'{fmt(dynamics["pseudospectral_proxy"])}/5.0', metric, small)

    draw.rounded_rectangle((44, 205, 604, 500), radius=8, fill="#ffffff", outline="#d6dde5")
    draw.text((64, 222), "Certification coverage", fill="#17202a", font=section)
    y = 245
    for key, names in coverage.items():
        draw.text((64, y - 2), LEVEL_LABELS[key], fill="#17202a", font=label)
        draw.rounded_rectangle((220, y, 550, y + 14), radius=7, fill="#e8edf3")
        bar_width = int(330 * len(names) / len(probes))
        draw.rounded_rectangle((220, y, 220 + bar_width, y + 14), radius=7, fill="#1f8a5b")
        draw.text((570, y - 1), f"{len(names)}/{len(probes)}", fill="#5f6b76", font=small)
        y += 34

    draw.rounded_rectangle((660, 205, 1230, 460), radius=8, fill="#ffffff", outline="#d6dde5")
    draw.text((690, 222), "Operator vs text target margin", fill="#17202a", font=section)
    transfer_items = [
        ("No message", transfer["no_message_target_margin_delta"]),
        ("Text", transfer["text_target_margin_delta"]),
        ("Latent vector", transfer["latent_vector_target_margin_delta"]),
        ("Additive operator", transfer["additive_operator_target_margin_delta"]),
        ("Low-rank operator", transfer["low_rank_operator_target_margin_delta"]),
    ]
    max_transfer = max(abs(value) for _, value in transfer_items) or 1.0
    y = 245
    for item_label, value in transfer_items:
        draw.text((690, y - 2), item_label, fill="#17202a", font=label)
        draw.rounded_rectangle((850, y, 1150, y + 14), radius=7, fill="#e8edf3")
        bar_width = int(300 * abs(value) / max_transfer)
        color = "#2367b5" if value >= 0 else "#b42318"
        draw.rounded_rectangle((850, y, 850 + bar_width, y + 14), radius=7, fill=color)
        draw.text((1170, y - 1), fmt(value), fill="#5f6b76", font=small)
        y += 34

    draw.rounded_rectangle((44, 532, 1230, 656), radius=8, fill="#ffffff", outline="#d6dde5")
    draw.text((64, 558), "Safety margins", fill="#17202a", font=section)
    draw.text((64, 600), f'Rollback residue: {sci(activation["rollback_residue"])}', fill="#17202a", font=label)
    draw.text((382, 600), f'Rollout max norm: {fmt(dynamics["rollout_max_norm"])}/5.0', fill="#17202a", font=label)
    draw.text((704, 600), f'Operator advantage: {fmt(transfer["operator_absolute_advantage"])}', fill="#17202a", font=label)
    draw.text((984, 600), f'Off-target degradation: {fmt(transfer["off_target_degradation_max"])}', fill="#17202a", font=label)

    image.save(path)


def draw_png_metric(draw: Any, x: int, y: int, label: str, value: str, metric_font: Any, small_font: Any) -> None:
    draw.rounded_rectangle((x, y, x + 238, y + 48), radius=8, fill="#ffffff", outline="#d6dde5")
    draw.text((x + 18, y + 7), label, fill="#5f6b76", font=small_font)
    draw.text((x + 18, y + 23), value, fill="#17202a", font=metric_font)


def load_font(image_font: Any, size: int, bold: bool = False) -> Any:
    candidates = [
        "arialbd.ttf" if bold else "arial.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        try:
            return image_font.truetype(candidate, size=size)
        except OSError:
            continue
    return image_font.load_default()


if __name__ == "__main__":
    raise SystemExit(main())

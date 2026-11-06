"""Generates publication- and wet-lab-ready HTML hit dossiers."""
from datetime import datetime, timezone
import html
from .server import render_svg, compute_properties


def generate_report(episode, state, cfg):
    c_a, c_b = episode['candidates']
    dec = state['decision'] or {'kind': 'in_progress', 'candidate': None, 'probability': 0.0,
                                'explanation': 'Assay reveals in progress.'}
    p_a = compute_properties(c_a.get('smiles', '')) or {}
    p_b = compute_properties(c_b.get('smiles', '')) or {}
    svg_a = render_svg(c_a.get('smiles', ''), width=220, height=120)
    svg_b = render_svg(c_b.get('smiles', ''), width=220, height=120)

    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    doc_id = c_a['activity_records'][0].get('document_chembl_id', 'N/A')
    assay_id = episode['provenance'].get('assay', 'N/A')

    # Status badge styling
    is_nom = dec['kind'] == 'nominate'
    badge_color = '#15803d' if is_nom else '#b45309'
    badge_title = f"NOMINATE CANDIDATE {dec['candidate']}" if is_nom else "ABSTENTION (PRESERVE BUDGET)"

    # Specimen lookup
    samples_by_id = {s['id']: s for s in episode['samples']}

    trail_rows = []
    for step in state['trace']:
        sid = step['sample_id']
        sm = samples_by_id.get(sid, {'name': sid, 'x': [0, 0]})
        diff = abs(sm['x'][0] - sm['x'][1])
        trail_rows.append(f"""
        <tr>
            <td style="text-align:center;font-weight:600;">{step['step']}</td>
            <td><b>{html.escape(sm['name'])}</b><br><span style="font-size:11px;color:#666;">{html.escape(sid)}</span></td>
            <td style="text-align:right;">{sm['x'][0]:.2f}</td>
            <td style="text-align:right;">{sm['x'][1]:.2f}</td>
            <td style="text-align:right;color:#1d5fbf;font-weight:500;">{diff:.2f}</td>
            <td style="text-align:right;font-weight:600;">{step['response']:.3f}</td>
            <td style="text-align:right;">{step['posterior'][0]:.1%} / {step['posterior'][1]:.1%}</td>
        </tr>
        """)

    trail_html = "\n".join(trail_rows) if trail_rows else "<tr><td colspan='7' style='text-align:center;color:#888;'>No assays revealed yet.</td></tr>"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>DECOUPLE Isolation Dossier · {html.escape(episode['id'])}</title>
<style>
  @page {{ size: A4; margin: 18mm; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #1a1a1a; line-height: 1.5; margin: 0; padding: 24px; max-width: 900px; margin: auto; font-size: 13px; }}
  .header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #141414; padding-bottom: 14px; margin-bottom: 20px; }}
  .header h1 {{ margin: 0; font-size: 22px; letter-spacing: -0.02em; font-weight: 700; }}
  .header p {{ margin: 3px 0 0; color: #555; font-size: 12px; }}
  .decision-box {{ border: 2px solid {badge_color}; border-radius: 8px; padding: 16px; margin-bottom: 24px; background: #fafafa; }}
  .badge {{ display: inline-block; background: {badge_color}; color: white; padding: 4px 10px; border-radius: 4px; font-weight: 700; font-size: 12px; letter-spacing: 0.05em; }}
  .decision-box h2 {{ margin: 10px 0 6px; font-size: 18px; }}
  .decision-box p {{ margin: 0; color: #444; }}
  .candidates-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }}
  .cand-card {{ border: 1px solid #ddd; border-radius: 6px; padding: 14px; background: white; }}
  .cand-card h3 {{ margin: 0 0 10px; font-size: 15px; display: flex; justify-content: space-between; align-items: baseline; }}
  .struct-box {{ display: flex; justify-content: center; align-items: center; background: #fdfdfd; border: 1px solid #eee; border-radius: 4px; padding: 6px; height: 130px; margin-bottom: 12px; }}
  .struct-box svg {{ max-height: 120px; max-width: 100%; }}
  table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 12px; }}
  th, td {{ padding: 8px 10px; border-bottom: 1px solid #eee; text-align: left; }}
  th {{ background: #f4f5f7; font-weight: 600; color: #444; }}
  .rec-box {{ background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 14px; margin-bottom: 24px; }}
  .rec-box h4 {{ margin: 0 0 8px; color: #1e40af; font-size: 13px; }}
  .rec-box ul {{ margin: 0; padding-left: 18px; color: #1e3a8a; }}
  .rec-box li {{ margin-bottom: 4px; }}
  .footer {{ border-top: 1px solid #ddd; padding-top: 12px; margin-top: 28px; font-size: 11px; color: #777; display: flex; justify-content: space-between; }}
  @media print {{ body {{ padding: 0; }} .no-print {{ display: none; }} }}
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>Natural Products Isolation Prioritization Dossier</h1>
    <p>Target: <b>{html.escape(cfg['target'])}</b> ({html.escape(cfg['target_chembl_id'])}) · ChEMBL Paper: <b>{html.escape(doc_id)}</b></p>
  </div>
  <div style="text-align:right;">
    <span style="font-weight:600;font-size:12px;">DECOUPLE Decision Engine</span><br>
    <span style="color:#777;font-size:11px;">{now}</span><br>
    <button class="no-print" onclick="window.print()" style="margin-top:6px;padding:4px 8px;font-size:11px;cursor:pointer;">Print / Save PDF</button>
  </div>
</div>

<div class="decision-box">
  <span class="badge">{badge_title}</span>
  <h2>{html.escape(c_a['name'] if dec.get('candidate') == 'A' else c_b['name'] if dec.get('candidate') == 'B' else 'Exploration Ended in Abstention')}</h2>
  <p>{html.escape(dec['explanation'])}</p>
  {f'<p style="margin-top:6px;font-weight:600;color:{badge_color};">Nomination Bayesian Posterior Confidence: {dec["probability"]:.4%}</p>' if is_nom else ''}
</div>

<div class="candidates-grid">
  <div class="cand-card" style="{'border:2px solid #15803d;' if dec.get('candidate') == 'A' else ''}">
    <h3><span>Candidate A · {html.escape(c_a['name'])}</span> <span style="font-size:11px;color:#777;">{html.escape(c_a['id'])}</span></h3>
    <div class="struct-box">{svg_a}</div>
    <table>
      <tr><td>Molecular Weight</td><td><b>{p_a.get('mw', '—')} g/mol</b></td></tr>
      <tr><td>cLogP (lipophilicity)</td><td><b>{p_a.get('logp', '—')}</b></td></tr>
      <tr><td>TPSA (polar surface)</td><td><b>{p_a.get('tpsa', '—')} Å²</b></td></tr>
      <tr><td>Fsp³ (3D complexity)</td><td><b>{p_a.get('fsp3', '—')}</b></td></tr>
      <tr><td>HBD / HBA</td><td><b>{p_a.get('hbd', '—')} / {p_a.get('hba', '—')}</b></td></tr>
      <tr><td>Lipinski Rule of 5</td><td><b>{html.escape(str(p_a.get('lipinski', '—')))}</b></td></tr>
    </table>
  </div>
  <div class="cand-card" style="{'border:2px solid #15803d;' if dec.get('candidate') == 'B' else ''}">
    <h3><span>Candidate B · {html.escape(c_b['name'])}</span> <span style="font-size:11px;color:#777;">{html.escape(c_b['id'])}</span></h3>
    <div class="struct-box">{svg_b}</div>
    <table>
      <tr><td>Molecular Weight</td><td><b>{p_b.get('mw', '—')} g/mol</b></td></tr>
      <tr><td>cLogP (lipophilicity)</td><td><b>{p_b.get('logp', '—')}</b></td></tr>
      <tr><td>TPSA (polar surface)</td><td><b>{p_b.get('tpsa', '—')} Å²</b></td></tr>
      <tr><td>Fsp³ (3D complexity)</td><td><b>{p_b.get('fsp3', '—')}</b></td></tr>
      <tr><td>HBD / HBA</td><td><b>{p_b.get('hbd', '—')} / {p_b.get('hba', '—')}</b></td></tr>
      <tr><td>Lipinski Rule of 5</td><td><b>{html.escape(str(p_b.get('lipinski', '—')))}</b></td></tr>
    </table>
  </div>
</div>

<h3 style="margin-bottom:6px;">Three-Assay Deconvolution Trace</h3>
<p style="margin-top:0;color:#666;font-size:12px;">Assay reveals selected by the expected utility acquisition policy to break collinear co-occurrence:</p>
<table>
  <thead>
    <tr>
      <th style="text-align:center;">Step</th>
      <th>Botanical Specimen</th>
      <th style="text-align:right;">[A]</th>
      <th style="text-align:right;">[B]</th>
      <th style="text-align:right;">Contrast Δ</th>
      <th style="text-align:right;">Response</th>
      <th style="text-align:right;">P(A) / P(B)</th>
    </tr>
  </thead>
  <tbody>
    {trail_html}
  </tbody>
</table>

<div class="rec-box">
  <h4>Confirmatory Wet-Lab Execution Protocol</h4>
  <ul>
    <li><b>Targeted Isolation:</b> Isolate and purify <b>{html.escape(c_a['name'] if dec.get('candidate') == 'A' else c_b['name'] if dec.get('candidate') == 'B' else 'the active extract')}</b> using flash chromatography guided by the target molecular weight.</li>
    <li><b>Primary Potency Validation:</b> Measure standard 10-point dose-response curves (<i>IC</i><sub>50</sub>) against intracellular <i>Trypanosoma cruzi</i> amastigotes.</li>
    <li><b>Host-Cell Selectivity Counter-Screen:</b> Determine mammalian cytotoxicity against rat L6 or Vero cells; confirm Selectivity Index (<i>SI</i> = <i>IC</i><sub>50</sub><sup>L6</sup> / <i>IC</i><sub>50</sub><sup>parasite</sup> &ge; 10).</li>
    <li><b>Negative Control:</b> Confirm lack of single-driver efficacy in pure samples of the rejected candidate ({html.escape(c_b['name'] if dec.get('candidate') == 'A' else c_a['name'])}).</li>
  </ul>
</div>

<div class="footer">
  <div>Episode: <code>{html.escape(episode['id'])}</code> · Assay: <code>{html.escape(assay_id)}</code></div>
  <div>DECOUPLE Decision Framework · CC-BY-SA-4.0</div>
</div>
</body>
</html>"""


import os
import re
from pathlib import Path
import markdown

report_md_path = Path("/work/docs/PROJECT_REPORT.md")
report_html_path = Path("/work/docs/PROJECT_REPORT.html")

with open(report_md_path, "r", encoding="utf-8") as f:
    text = f.read()

# Convert markdown to html with tables and code highlighting
html_body = markdown.markdown(text, extensions=["tables", "fenced_code", "codehilite"])

# Academic PDF styled HTML template
full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>HN HIT Predictor - Project Report</title>
<style>
  @page {{
    size: A4;
    margin: 20mm 15mm 20mm 15mm;
    @bottom-center {{
      content: counter(page);
      font-size: 9pt;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      color: #666;
    }}
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.5;
    color: #1a1a1a;
    font-size: 10pt;
    padding: 0;
    margin: 0;
  }}
  .cover-page {{
    page-break-after: always;
    text-align: center;
    padding-top: 60px;
    height: 90vh;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .cover-title-main {{
    font-size: 26pt;
    font-weight: 800;
    letter-spacing: 1px;
    color: #111;
    margin-bottom: 12px;
  }}
  .cover-subtitle {{
    font-size: 16pt;
    font-weight: 600;
    color: #2b3a4a;
    margin-bottom: 60px;
    line-height: 1.3;
  }}
  .cover-details {{
    font-size: 12pt;
    line-height: 2;
    color: #333;
    margin-bottom: 60px;
  }}
  .cover-guidance {{
    font-size: 12pt;
    line-height: 1.8;
    color: #444;
    margin-bottom: 80px;
  }}
  .lpu-logo-box {{
    margin: 0 auto;
    width: 280px;
    border: 2px solid #b85d19;
    padding: 12px;
    border-radius: 4px;
    background: #fff;
  }}
  .lpu-name {{
    font-size: 18pt;
    font-weight: 800;
    letter-spacing: 2px;
    color: #d35400;
    margin: 0;
  }}
  .lpu-sub {{
    font-size: 9pt;
    font-style: italic;
    color: #555;
    margin-top: 4px;
  }}
  h1 {{
    font-size: 16pt;
    font-weight: 700;
    color: #0b3954;
    border-bottom: 2px solid #0b3954;
    padding-bottom: 4px;
    margin-top: 28px;
    page-break-after: avoid;
  }}
  h2 {{
    font-size: 13pt;
    font-weight: 600;
    color: #087e8b;
    margin-top: 22px;
    border-bottom: 1px solid #e0e0e0;
    padding-bottom: 3px;
    page-break-after: avoid;
  }}
  h3 {{
    font-size: 11pt;
    font-weight: 600;
    color: #333;
    margin-top: 16px;
    page-break-after: avoid;
  }}
  p, li {{
    text-align: justify;
    font-size: 9.5pt;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
    font-size: 8.5pt;
    page-break-inside: avoid;
  }}
  th, td {{
    border: 1px solid #c8d1d9;
    padding: 6px 8px;
    text-align: left;
  }}
  th {{
    background-color: #f1f4f8;
    font-weight: 600;
    color: #1a252f;
  }}
  tr:nth-child(even) {{
    background-color: #fafbfc;
  }}
  code {{
    font-family: 'Consolas', 'Courier New', monospace;
    background-color: #f3f4f6;
    padding: 2px 4px;
    border-radius: 3px;
    font-size: 8.5pt;
    color: #c7254e;
  }}
  pre {{
    background-color: #f6f8fa;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 10px 12px;
    font-size: 7.8pt;
    overflow-x: auto;
    font-family: 'Consolas', 'Courier New', monospace;
    line-height: 1.35;
    page-break-inside: avoid;
  }}
  pre code {{
    background: transparent;
    padding: 0;
    color: #24292f;
  }}
  blockquote {{
    border-left: 4px solid #087e8b;
    margin: 0;
    padding-left: 12px;
    color: #4b5563;
  }}
  hr {{
    border: 0;
    height: 1px;
    background: #e1e4e8;
    margin: 20px 0;
  }}
</style>
</head>
<body>

<!-- Title Cover Page identical to Lovely Professional University submission standard -->
<div class="cover-page">
  <div>
    <div class="cover-title-main">PROJECT REPORT</div>
    <div class="cover-subtitle">HN HIT Predictor<br><span style="font-size:12pt; font-weight:normal; color:#555;">An MLOps Pipeline on AWS using CloudFormation, Jenkins and CloudWatch</span></div>
  </div>

  <div class="cover-details">
    <strong>Subject:-</strong> INT315 / MLOps &amp; Cloud Architecture<br><br>
    <strong>Submitted by:-</strong> Navdeep Singh<br>
    <strong>Reg No:</strong> 12308217 | <strong>Roll no:</strong> 43<br>
    <strong>Section:-</strong> K2O2313
  </div>

  <div class="cover-guidance">
    Under the guidance of: <strong>Arshiya (UID-29453)</strong><br>
    School of CSE Lovely Professional University
  </div>

  <div>
    <div class="lpu-logo-box">
      <div class="lpu-name">L O V E L Y</div>
      <div style="font-size:11pt; font-weight:bold; color:#222; letter-spacing:1px; margin-top:2px;">PROFESSIONAL UNIVERSITY</div>
      <div class="lpu-sub">Transforming Education Transforming India</div>
    </div>
  </div>
</div>

<!-- Report Content Body -->
{html_body}

</body>
</html>
"""

with open(report_html_path, "w", encoding="utf-8") as f:
    f.write(full_html)

print(f"HTML successfully generated at: {report_html_path}")

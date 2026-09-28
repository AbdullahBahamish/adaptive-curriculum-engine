"""Export OpenAPI JSON and Swagger UI HTML docs."""
import json
from pathlib import Path
from ace.api.main import app

def export_openapi():
    openapi_schema = app.openapi()
    
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    # Write openapi.json
    openapi_file = docs_dir / "openapi.json"
    with open(openapi_file, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"Exported OpenAPI JSON to {openapi_file} ({len(openapi_schema.get('paths', {}))} endpoints)")

    # Write standalone Swagger UI HTML
    swagger_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ACE AI Engine - OpenAPI Interactive Documentation</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css" />
  <style>
    body {{
      margin: 0;
      padding: 0;
      background: #0f172a;
      color: #f8fafc;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    .header-bar {{
      background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
      border-bottom: 1px solid #334155;
      padding: 1.25rem 2rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .header-title {{
      font-size: 1.25rem;
      font-weight: 700;
      color: #38bdf8;
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}
    .badge {{
      background: #0284c7;
      color: white;
      padding: 0.2rem 0.6rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
    }}
    #swagger-ui {{
      max-width: 1400px;
      margin: 0 auto;
      padding: 1rem 2rem 4rem;
      background: #ffffff;
      border-radius: 12px;
      margin-top: 1.5rem;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }}
  </style>
</head>
<body>
  <div class="header-bar">
    <div class="header-title">
      <span>🚀 Adaptive Curriculum Engine (ACE)</span>
      <span class="badge">OpenAPI 3.1.0</span>
    </div>
    <div style="font-size: 0.875rem; color: #94a3b8;">
      Fast, Deterministic DAG Curriculum Sequencing & Semantic Skill Matching
    </div>
  </div>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js" crossorigin></script>
  <script>
    window.onload = () => {{
      const spec = {json.dumps(openapi_schema)};
      window.ui = SwaggerUIBundle({{
        spec: spec,
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIBundle.SwaggerUIStandalonePreset
        ],
        layout: "BaseLayout"
      }});
    }};
  </script>
</body>
</html>
"""
    html_file = docs_dir / "api_docs.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(swagger_html)
    print(f"Exported standalone Swagger UI HTML to {html_file}")

if __name__ == "__main__":
    export_openapi()

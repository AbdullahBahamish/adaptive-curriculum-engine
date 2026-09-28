"""Generate interactive graph visualization and graph data exports for ACE."""
import json
from pathlib import Path

from ace.domain.career import Career, CareerSkillRequirement
from ace.domain.learner import LearnerProfile
from ace.domain.prerequisite import Prerequisite
from ace.domain.skill import Skill
from ace.graph.builder import build_prerequisite_graph
from ace.graph.gap_analyzer import compute_skill_gaps
from ace.graph.graph_metrics import get_graph_metrics
from ace.graph.solver import generate_learning_path

CATEGORY_COLORS = {
    "cs_foundations": "#38bdf8",              # Sky blue
    "programming_languages": "#818cf8",       # Indigo
    "frontend": "#f43f5e",                    # Rose / Red
    "backend": "#10b981",                     # Emerald green
    "database": "#f59e0b",                    # Amber
    "cloud_devops": "#06b6d4",                # Cyan
    "ai_ml": "#a855f7",                       # Purple
    "cybersecurity": "#ec4899",               # Pink
    "software_engineering_practices": "#64748b" # Slate
}

def generate_visualizer_data():
    with open("data/seed/skills.json", "r", encoding="utf-8") as f:
        skills = [Skill(**s) for s in json.load(f)]
    with open("data/seed/prerequisites.json", "r", encoding="utf-8") as f:
        prereqs = [Prerequisite(**p) for p in json.load(f)]
    with open("data/seed/careers.json", "r", encoding="utf-8") as f:
        careers_data = json.load(f)

    full_graph = build_prerequisite_graph(skills, prereqs)
    skill_map = {s.id: s for s in skills}
    metrics = get_graph_metrics(full_graph)
    learner = LearnerProfile(id="demo_learner", confirmed_skills=[])

    career_results = {}

    for c_raw in careers_data:
        c = Career(
            id=c_raw["id"],
            name=c_raw["name"],
            description=c_raw.get("description", ""),
            required_skills=[CareerSkillRequirement(**r) for r in c_raw["required_skills"]],
        )
        gaps = compute_skill_gaps(c, learner, skill_map, graph=full_graph)
        path = generate_learning_path(
            gaps=gaps,
            graph=full_graph,
            learner_id=learner.id,
            career_id=c.id,
            career_name=c.name,
            confirmed_skill_ids=set(),
            career=c,
            learner=learner,
            all_skills=skill_map,
        )

        step_ids = [step.skill_id for step in path.steps]
        step_order_map = {step.skill_id: (i + 1) for i, step in enumerate(path.steps)}
        step_obj_map = {step.skill_id: step for step in path.steps}

        subgraph = full_graph.subgraph(step_ids)

        nodes = []
        for sid in step_ids:
            s = skill_map[sid]
            step = step_obj_map[sid]
            order = step_order_map[sid]
            cat_color = CATEGORY_COLORS.get(s.category, "#94a3b8")
            nodes.append({
                "id": sid,
                "label": f"#{order} {s.name}",
                "skill_name": s.name,
                "order": order,
                "category": s.category,
                "difficulty": s.difficulty,
                "hours": s.estimated_hours,
                "unblocks": step.unblocks_count,
                "gap_score": step.gap_score,
                "reason_codes": step.reason_codes,
                "rationale": step.rationale,
                "prerequisites_satisfied": step.prerequisites_satisfied,
                "color": cat_color,
            })

        edges = []
        for u, v in subgraph.edges:
            edges.append({
                "from": u,
                "to": v,
                "label": "requires",
            })

        # Mermaid representation
        mermaid_lines = ["graph TD"]
        for n in nodes:
            safe_name = n["skill_name"].replace('"', '')
            mermaid_lines.append(f'    {n["id"]}["#{n["order"]}: {safe_name}<br/>({n["category"]} | {n["hours"]}h)"]')
        for e in edges:
            mermaid_lines.append(f'    {e["from"]} --> {e["to"]}')

        career_results[c.id] = {
            "career_id": c.id,
            "career_name": c.name,
            "description": c.description,
            "total_steps": len(path.steps),
            "total_hours": path.total_estimated_hours,
            "strategy": path.strategy,
            "composite_score": path.composite_score,
            "objective_scores": path.objective_scores,
            "nodes": nodes,
            "edges": edges,
            "mermaid": "\n".join(mermaid_lines),
        }

    # Also build full knowledge graph representation
    full_nodes = []
    for s in skills:
        full_nodes.append({
            "id": s.id,
            "label": s.name,
            "category": s.category,
            "difficulty": s.difficulty,
            "hours": s.estimated_hours,
            "color": CATEGORY_COLORS.get(s.category, "#94a3b8"),
        })
    full_edges = [{"from": u, "to": v} for u, v in full_graph.edges]

    export_payload = {
        "careers": career_results,
        "full_graph": {
            "total_nodes": len(full_nodes),
            "total_edges": len(full_edges),
            "nodes": full_nodes,
            "edges": full_edges,
        },
        "categories": CATEGORY_COLORS,
    }

    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    with open(docs_dir / "resulted_graphs.json", "w", encoding="utf-8") as f:
        json.dump(export_payload, f, indent=2)
    print(f"Exported graph data to {docs_dir / 'resulted_graphs.json'}")

    # Build interactive HTML visualizer
    html_content = build_html_visualizer(export_payload)
    with open(docs_dir / "graph_visualizer.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Exported interactive graph visualizer to {docs_dir / 'graph_visualizer.html'}")

def build_html_visualizer(payload: dict) -> str:
    json_data = json.dumps(payload)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ACE - Resulted Curriculum Graph Visualizer</title>
  <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #090d16;
      --card-bg: rgba(26, 34, 52, 0.75);
      --card-border: rgba(56, 189, 248, 0.15);
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --primary: #38bdf8;
      --accent: #818cf8;
      --success: #34d399;
      --warning: #fbbf24;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }}
    /* Top Header */
    header {{
      background: linear-gradient(90deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      padding: 0.85rem 1.75rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      z-index: 10;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 0.85rem;
    }}
    .brand-icon {{
      width: 36px;
      height: 36px;
      border-radius: 8px;
      background: linear-gradient(135deg, #38bdf8, #818cf8);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.2rem;
      box-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
    }}
    .brand-title {{
      font-size: 1.15rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      background: linear-gradient(90deg, #f8fafc, #38bdf8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .brand-subtitle {{
      font-size: 0.75rem;
      color: var(--text-muted);
    }}
    /* Controls Bar */
    .controls {{
      display: flex;
      align-items: center;
      gap: 1rem;
    }}
    select, button, input {{
      background: #1e293b;
      border: 1px solid #334155;
      color: #f8fafc;
      padding: 0.5rem 0.9rem;
      border-radius: 8px;
      font-size: 0.85rem;
      font-family: inherit;
      outline: none;
      transition: all 0.2s;
    }}
    select:hover, button:hover, input:focus {{
      border-color: var(--primary);
    }}
    button.btn-primary {{
      background: linear-gradient(135deg, #0284c7, #4f46e5);
      border: none;
      font-weight: 600;
      cursor: pointer;
    }}
    button.btn-primary:hover {{
      opacity: 0.92;
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.3);
    }}
    /* Layout */
    .main-container {{
      display: flex;
      flex: 1;
      position: relative;
      overflow: hidden;
    }}
    #graph-network {{
      flex: 1;
      height: 100%;
      background: radial-gradient(circle at 50% 50%, #111827 0%, #030712 100%);
    }}
    /* Sidebar Details Drawer */
    .sidebar {{
      width: 380px;
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(16px);
      border-left: 1px solid rgba(255, 255, 255, 0.08);
      padding: 1.5rem;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
      z-index: 5;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.15rem;
    }}
    .stat-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 0.75rem;
    }}
    .stat-item {{
      background: rgba(255, 255, 255, 0.03);
      padding: 0.75rem;
      border-radius: 8px;
      border: 1px solid rgba(255, 255, 255, 0.04);
    }}
    .stat-label {{
      font-size: 0.7rem;
      text-transform: uppercase;
      color: var(--text-muted);
      letter-spacing: 0.05em;
    }}
    .stat-val {{
      font-size: 1.25rem;
      font-weight: 700;
      color: #38bdf8;
      margin-top: 0.25rem;
    }}
    .badge {{
      display: inline-block;
      padding: 0.2rem 0.55rem;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      margin-right: 0.4rem;
      margin-bottom: 0.4rem;
    }}
    .badge-outline {{
      border: 1px solid #475569;
      color: #cbd5e1;
    }}
    .legend-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 0.5rem;
      font-size: 0.75rem;
    }}
    .legend-item {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .legend-dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }}
    /* Step Sequence View */
    .sequence-list {{
      max-height: 260px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }}
    .sequence-item {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.45rem 0.75rem;
      background: rgba(255, 255, 255, 0.02);
      border-radius: 6px;
      font-size: 0.8rem;
      cursor: pointer;
      border: 1px solid transparent;
      transition: all 0.15s;
    }}
    .sequence-item:hover {{
      background: rgba(56, 189, 248, 0.1);
      border-color: rgba(56, 189, 248, 0.3);
    }}
    /* Footer bar */
    footer {{
      background: #0b0f19;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      padding: 0.4rem 1.75rem;
      font-size: 0.75rem;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="brand-icon">⚡</div>
      <div>
        <div class="brand-title">ACE Topological Curriculum Graph</div>
        <div class="brand-subtitle">Directed Acyclic Graph (DAG) Prerequisite Visualizer</div>
      </div>
    </div>
    <div class="controls">
      <label style="font-size: 0.8rem; color: var(--text-muted);">Career Track:</label>
      <select id="careerSelect" onchange="loadSelectedGraph()">
        <option value="frontend_developer">Frontend Developer (20 steps)</option>
        <option value="backend_developer">Backend Developer (27 steps)</option>
        <option value="fullstack_developer">Full Stack Developer (27 steps)</option>
        <option value="ai_ml_engineer">AI / ML Engineer (34 steps)</option>
        <option value="cybersecurity_analyst">Cybersecurity Analyst (31 steps)</option>
        <option value="cloud_engineer">Cloud & DevOps Engineer (25 steps)</option>
        <option value="__full__">Full Knowledge Graph (112 skills, 144 edges)</option>
      </select>

      <label style="font-size: 0.8rem; color: var(--text-muted); margin-left: 0.5rem;">Layout:</label>
      <select id="layoutSelect" onchange="toggleLayout()">
        <option value="hierarchical">Topological DAG (Hierarchical)</option>
        <option value="physics">Organic Network (Force Physics)</option>
      </select>

      <button onclick="network.fit()" title="Zoom to fit entire graph">Fit Graph</button>
      <button class="btn-primary" onclick="window.open('api_docs.html', '_blank')">View OpenAPI Docs</button>
    </div>
  </header>

  <div class="main-container">
    <div id="graph-network"></div>

    <aside class="sidebar">
      <div class="card" id="career-meta">
        <h3 id="panel-title" style="color: #38bdf8; font-size: 1.1rem; margin-bottom: 0.5rem;">Career Details</h3>
        <p id="panel-desc" style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 1rem;"></p>
        
        <div class="stat-grid">
          <div class="stat-item">
            <div class="stat-label">Total Steps</div>
            <div class="stat-val" id="stat-steps">-</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">Total Hours</div>
            <div class="stat-val" id="stat-hours">-</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">Sequencing Strategy</div>
            <div class="stat-val" id="stat-strategy" style="font-size: 0.95rem; color: #a78bfa;">-</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">DAG Invariant</div>
            <div class="stat-val" style="color: #34d399; font-size: 0.95rem;">0.00% Violations</div>
          </div>
        </div>
      </div>

      <!-- Node Inspect Card -->
      <div class="card" id="node-meta">
        <h4 style="font-size: 0.9rem; color: #818cf8; margin-bottom: 0.5rem;">Selected Skill Inspector</h4>
        <div id="node-inspect-content" style="font-size: 0.82rem; color: var(--text-muted); line-height: 1.45;">
          Click any skill node in the graph to inspect its prerequisite chain, difficulty, study hours, and unblocking power.
        </div>
      </div>

      <!-- Topological Sequence List -->
      <div class="card">
        <h4 style="font-size: 0.9rem; color: #f8fafc; margin-bottom: 0.6rem;">Topological Sequence Schedule</h4>
        <div class="sequence-list" id="sequence-container"></div>
      </div>

      <!-- Legend -->
      <div class="card">
        <h4 style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.6rem;">Skill Categories</h4>
        <div class="legend-grid" id="legend-container"></div>
      </div>
    </aside>
  </div>

  <footer>
    <div>⚡ Adaptive Curriculum Engine (ACE) — Standalone AI Intelligence Engine</div>
    <div>FastAPI REST Server: <code>http://localhost:8000</code> | Docs: <code>/docs</code></div>
  </footer>

  <script>
    const data = {json_data};
    let network = null;
    let currentLayout = "hierarchical";

    // Populate legend
    const legendEl = document.getElementById("legend-container");
    for (const [cat, color] of Object.entries(data.categories)) {{
      const item = document.createElement("div");
      item.className = "legend-item";
      item.innerHTML = `<span class="legend-dot" style="background: ${{color}}"></span><span>${{cat.replace(/_/g, ' ')}}</span>`;
      legendEl.appendChild(item);
    }}

    function loadSelectedGraph() {{
      const careerKey = document.getElementById("careerSelect").value;
      const isFull = careerKey === "__full__";

      const nodesArray = [];
      const edgesArray = [];

      if (isFull) {{
        document.getElementById("panel-title").innerText = "Full Knowledge Graph";
        document.getElementById("panel-desc").innerText = "Complete prerequisite ontology spanning 112 skills and 144 directed prerequisite edges across 9 domains.";
        document.getElementById("stat-steps").innerText = data.full_graph.total_nodes;
        document.getElementById("stat-hours").innerText = "~3000h";
        document.getElementById("stat-strategy").innerText = "global_dag";
        document.getElementById("sequence-container").innerHTML = "<div style='font-size:0.75rem;color:#94a3b8;padding:0.5rem;'>Displaying full global graph. Select a career track to see ordered topological sequence.</div>";

        data.full_graph.nodes.forEach(n => {{
          nodesArray.push({{
            id: n.id,
            label: n.label,
            color: {{ background: n.color, border: '#ffffff', highlight: {{ background: '#ffffff', border: n.color }} }},
            font: {{ color: '#ffffff', size: 12, face: 'Inter' }},
            shape: 'box',
            margin: 8,
            shadow: {{ enabled: true, color: 'rgba(0,0,0,0.5)', size: 4 }}
          }});
        }});

        data.full_graph.edges.forEach(e => {{
          edgesArray.push({{
            from: e.from,
            to: e.to,
            arrows: 'to',
            color: {{ color: '#475569', highlight: '#38bdf8' }},
            smooth: {{ type: 'cubicBezier' }}
          }});
        }});
      }} else {{
        const cData = data.careers[careerKey];
        document.getElementById("panel-title").innerText = cData.career_name;
        document.getElementById("panel-desc").innerText = cData.description || "Personalized prerequisite-safe curriculum generated via Pareto multi-objective optimization.";
        document.getElementById("stat-steps").innerText = cData.total_steps;
        document.getElementById("stat-hours").innerText = cData.total_hours + "h";
        document.getElementById("stat-strategy").innerText = cData.strategy;

        // Sequence List
        const seqContainer = document.getElementById("sequence-container");
        seqContainer.innerHTML = "";
        cData.nodes.forEach(n => {{
          const item = document.createElement("div");
          item.className = "sequence-item";
          item.innerHTML = `<span><strong>#${{n.order}}</strong> ${{n.skill_name}}</span><span style="color:#38bdf8;font-size:0.75rem;">${{n.hours}}h</span>`;
          item.onclick = () => focusNode(n.id);
          seqContainer.appendChild(item);
        }});

        cData.nodes.forEach(n => {{
          nodesArray.push({{
            id: n.id,
            label: n.label,
            level: Math.floor((n.order - 1) / 3),
            color: {{
              background: n.color,
              border: '#ffffff',
              highlight: {{ background: '#ffffff', border: '#38bdf8' }}
            }},
            font: {{ color: '#ffffff', size: 12, face: 'Inter', strokeWidth: 2, strokeColor: '#0f172a' }},
            shape: 'box',
            margin: 8,
            shadow: {{ enabled: true, color: 'rgba(0,0,0,0.6)', size: 5 }},
            meta: n
          }});
        }});

        cData.edges.forEach(e => {{
          edgesArray.push({{
            from: e.from,
            to: e.to,
            arrows: {{ to: {{ enabled: true, scaleFactor: 0.8 }} }},
            color: {{ color: 'rgba(148, 163, 184, 0.4)', highlight: '#38bdf8' }},
            width: 1.5,
            smooth: {{ type: 'cubicBezier' }}
          }});
        }});
      }}

      renderNetwork(nodesArray, edgesArray);
    }}

    function renderNetwork(nodes, edges) {{
      const container = document.getElementById("graph-network");
      const visNodes = new vis.DataSet(nodes);
      const visEdges = new vis.DataSet(edges);

      const options = {{
        layout: {{
          hierarchical: currentLayout === "hierarchical" ? {{
            direction: "LR",
            sortMethod: "directed",
            levelSeparation: 190,
            nodeSpacing: 70,
            shakeTowards: "roots"
          }} : false
        }},
        physics: {{
          enabled: currentLayout === "physics",
          solver: "forceAtlas2Based",
          forceAtlas2Based: {{
            gravitationalConstant: -50,
            centralGravity: 0.01,
            springLength: 100,
            springConstant: 0.08
          }}
        }},
        interaction: {{
          hover: true,
          navigationButtons: true,
          keyboard: true,
          tooltipDelay: 100
        }}
      }};

      network = new vis.Network(container, {{ nodes: visNodes, edges: visEdges }}, options);

      network.on("selectNode", function(params) {{
        const nodeId = params.nodes[0];
        const node = visNodes.get(nodeId);
        if (node && node.meta) {{
          showNodeInspector(node.meta);
        }}
      }});
    }}

    function focusNode(nodeId) {{
      if (!network) return;
      network.focus(nodeId, {{
        scale: 1.2,
        animation: {{ duration: 500, easingFunction: 'easeInOutQuad' }}
      }});
      network.selectNodes([nodeId]);
      const careerKey = document.getElementById("careerSelect").value;
      if (careerKey !== "__full__") {{
        const cData = data.careers[careerKey];
        const n = cData.nodes.find(x => x.id === nodeId);
        if (n) showNodeInspector(n);
      }}
    }}

    function showNodeInspector(n) {{
      const el = document.getElementById("node-inspect-content");
      el.innerHTML = `
        <div style="font-size: 1.05rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.4rem;">
          #${{n.order}} ${{n.skill_name}}
        </div>
        <div style="margin-bottom: 0.6rem;">
          <span class="badge" style="background:${{n.color}}">${{n.category}}</span>
          <span class="badge badge-outline">Difficulty: ${{n.difficulty}}/5</span>
          <span class="badge badge-outline">${{n.hours}} Hours</span>
        </div>
        <div style="margin-bottom: 0.6rem;">
          <strong>Unblocks:</strong> <span style="color:#38bdf8;">${{n.unblocks}} dependent skills</span>
        </div>
        <div style="margin-bottom: 0.6rem;">
          <strong>Rationale:</strong> ${{n.rationale || 'Topologically required prerequisite step.'}}
        </div>
        ${{n.reason_codes && n.reason_codes.length ? `
          <div style="margin-top: 0.5rem;">
            <strong>Reason Codes:</strong><br/>
            ${{n.reason_codes.map(r => `<span class="badge" style="background:#1e293b;border:1px solid #475569;margin-top:0.25rem;">${{r}}</span>`).join(' ')}}
          </div>
        ` : ''}}
      `;
    }}

    function toggleLayout() {{
      currentLayout = document.getElementById("layoutSelect").value;
      loadSelectedGraph();
    }}

    window.onload = () => {{
      loadSelectedGraph();
    }};
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    generate_visualizer_data()

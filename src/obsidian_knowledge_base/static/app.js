const svg = d3.select("#graph");
const statsEl = document.querySelector("#stats");
const inspectorEl = document.querySelector("#inspector");
const searchEl = document.querySelector("#search");
const filters = Array.from(document.querySelectorAll(".filter"));

let rawGraph = { nodes: [], edges: [], stats: {} };
let activeKind = "all";
let activeSearch = "";
let selectedId = null;
let simulation;

const colors = {
  note: "#56d4a5",
  tag: "#f2c14e",
  missing: "#ef6f6c",
};

function radius(node) {
  const degree = (node.backlinks || 0) + (node.outlinks || 0);
  if (node.kind === "tag") return 8 + Math.min(degree, 10);
  if (node.kind === "missing") return 7;
  return 10 + Math.min(Math.sqrt(node.word_count || 1), 14) + Math.min(degree, 8);
}

function renderStats(stats) {
  const entries = [
    ["Notes", stats.notes],
    ["Edges", stats.edges],
    ["Tags", stats.tags],
    ["Missing", stats.missing],
    ["Words", stats.words],
    ["Avg Words", stats.average_words],
  ];
  statsEl.innerHTML = entries
    .map(([label, value]) => `<div class="stat"><b>${value ?? 0}</b><span>${label}</span></div>`)
    .join("");
}

function matchesFilter(node) {
  const haystack = `${node.title} ${node.path || ""} ${(node.tags || []).join(" ")}`.toLowerCase();
  return (activeKind === "all" || node.kind === activeKind) && haystack.includes(activeSearch);
}

function filteredGraph() {
  const nodes = rawGraph.nodes.filter(matchesFilter);
  const ids = new Set(nodes.map((node) => node.id));
  const edges = rawGraph.edges.filter((edge) => ids.has(edge.source) && ids.has(edge.target));
  return { nodes: nodes.map((node) => ({ ...node })), edges: edges.map((edge) => ({ ...edge })) };
}

function renderInspector(node) {
  if (!node) {
    inspectorEl.innerHTML = `<h2>No node selected</h2><p>Click a node to inspect its links, backlinks, tags, and summary.</p>`;
    return;
  }

  const tags = (node.tags || []).map((tag) => `<span class="pill">#${tag}</span>`).join("");
  inspectorEl.innerHTML = `
    <h2>${escapeHtml(node.title)}</h2>
    ${node.path ? `<p class="path">${escapeHtml(node.path)}</p>` : ""}
    <p>${escapeHtml(node.summary || `${node.kind} node`)}</p>
    <div class="meta-grid">
      <div class="stat"><b>${node.backlinks || 0}</b><span>Backlinks</span></div>
      <div class="stat"><b>${node.outlinks || 0}</b><span>Outlinks</span></div>
      <div class="stat"><b>${node.word_count || 0}</b><span>Words</span></div>
      <div class="stat"><b>${node.kind}</b><span>Kind</span></div>
    </div>
    ${tags ? `<h3>Tags</h3><div>${tags}</div>` : ""}
  `;
}

function renderGraph() {
  const width = svg.node().clientWidth;
  const height = svg.node().clientHeight;
  const graph = filteredGraph();

  svg.selectAll("*").remove();
  if (simulation) simulation.stop();

  const zoomLayer = svg.append("g");
  const linkLayer = zoomLayer.append("g");
  const nodeLayer = zoomLayer.append("g");
  const labelLayer = zoomLayer.append("g");

  svg.call(
    d3
      .zoom()
      .scaleExtent([0.25, 4])
      .on("zoom", (event) => zoomLayer.attr("transform", event.transform)),
  );

  const links = linkLayer
    .selectAll("line")
    .data(graph.edges)
    .join("line")
    .attr("class", "link");

  const nodes = nodeLayer
    .selectAll("circle")
    .data(graph.nodes)
    .join("circle")
    .attr("class", (node) => `node ${node.id === selectedId ? "selected" : ""}`)
    .attr("r", radius)
    .attr("fill", (node) => colors[node.kind] || colors.note)
    .on("click", (_, node) => {
      selectedId = node.id;
      renderInspector(node);
      renderGraph();
    })
    .call(drag());

  const labels = labelLayer
    .selectAll("text")
    .data(graph.nodes.filter((node) => node.kind !== "missing"))
    .join("text")
    .attr("class", "label")
    .text((node) => node.title)
    .attr("text-anchor", "middle");

  simulation = d3
    .forceSimulation(graph.nodes)
    .force(
      "link",
      d3
        .forceLink(graph.edges)
        .id((node) => node.id)
        .distance((edge) => (edge.kind === "tag" ? 70 : 110)),
    )
    .force("charge", d3.forceManyBody().strength(-280))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius((node) => radius(node) + 18))
    .on("tick", () => {
      links
        .attr("x1", (edge) => edge.source.x)
        .attr("y1", (edge) => edge.source.y)
        .attr("x2", (edge) => edge.target.x)
        .attr("y2", (edge) => edge.target.y);

      nodes.attr("cx", (node) => node.x).attr("cy", (node) => node.y);

      labels.attr("x", (node) => node.x).attr("y", (node) => node.y + radius(node) + 15);
    });
}

function drag() {
  return d3
    .drag()
    .on("start", (event) => {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    })
    .on("drag", (event) => {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    })
    .on("end", (event) => {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

filters.forEach((button) => {
  button.addEventListener("click", () => {
    activeKind = button.dataset.kind;
    filters.forEach((item) => item.classList.toggle("active", item === button));
    renderGraph();
  });
});

searchEl.addEventListener("input", (event) => {
  activeSearch = event.target.value.trim().toLowerCase();
  renderGraph();
});

window.addEventListener("resize", () => renderGraph());

fetch("/api/graph")
  .then((response) => response.json())
  .then((graph) => {
    rawGraph = graph;
    renderStats(graph.stats);
    renderGraph();
  });

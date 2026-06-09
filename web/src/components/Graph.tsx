import { useEffect, useRef } from "react";
import * as d3 from "d3";
import type { GraphData, GraphNode } from "../types";

interface Props {
  graph: GraphData;
  filter: string;
  search: string;
  selected: GraphNode | null;
  onSelect: (node: GraphNode | null) => void;
}

const COLORS: Record<string, string> = {
  note: "#56d4a5",
  tag: "#f2c14e",
  missing: "#ef6f6c",
};

type SimNode = GraphNode & d3.SimulationNodeDatum;
type SimLink = d3.SimulationLinkDatum<SimNode>;

function nodeRadius(n: GraphNode): number {
  const deg = (n.backlinks ?? 0) + (n.outlinks ?? 0);
  if (n.kind === "tag") return 8 + Math.min(deg, 10);
  if (n.kind === "missing") return 7;
  const markdownLength = n.markdown_length ?? 0;
  const lengthBoost = Math.min(Math.sqrt(Math.max(markdownLength, 1)) / 6, 16);
  return 10 + lengthBoost + Math.min(deg, 8);
}

function _filtered(graph: GraphData, filter: string, search: string) {
  const q = search.toLowerCase();
  const nodes = graph.nodes.filter((n) => {
    const hay = `${n.title} ${n.path ?? ""} ${(n.tags ?? []).join(" ")}`.toLowerCase();
    return (filter === "all" || n.kind === filter) && hay.includes(q);
  });
  const ids = new Set(nodes.map((n) => n.id));
  const edges = graph.edges.filter((e) => ids.has(e.source as string) && ids.has(e.target as string));
  return { nodes: nodes.map((n) => ({ ...n })), edges: edges.map((e) => ({ ...e })) };
}

function _buildSim(nodes: SimNode[], edges: SimLink[], w: number, h: number) {
  return d3
    .forceSimulation(nodes)
    .force("link", d3.forceLink<SimNode, SimLink>(edges).id((d) => d.id).distance(80))
    .force("charge", d3.forceManyBody().strength(-180))
    .force("center", d3.forceCenter(w / 2, h / 2))
    .force("collision", d3.forceCollide<SimNode>().radius((d) => nodeRadius(d) + 4));
}

function _asPoint(node: string | number | SimNode): { x: number; y: number } {
  if (typeof node === "string" || typeof node === "number") return { x: 0, y: 0 };
  return { x: node.x ?? 0, y: node.y ?? 0 };
}

export function Graph({ graph, filter, search, selected, onSelect }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const el = svgRef.current;
    if (!el) return;
    const filtered = _filtered(graph, filter, search);
    const nodes: SimNode[] = filtered.nodes.map((n) => ({ ...n }));
    const edges: SimLink[] = filtered.edges.map((e) => ({ ...e }));
    const w = el.clientWidth || 800;
    const h = el.clientHeight || 600;
    const root = d3.select(el);
    root.selectAll("*").remove();

    const zoom = d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.2, 4]).on("zoom", (ev) => layer.attr("transform", ev.transform));
    root.call(zoom);

    const layer = root.append("g");
    const links = layer.append("g").selectAll("line").data(edges).join("line").attr("class", "link");
    links
      .attr("stroke", (d) => _isSelectedEdge(d, selected?.id ?? "") ? "rgba(142, 202, 230, 0.8)" : "rgba(255,255,255,0.12)")
      .attr("stroke-width", (d) => _isSelectedEdge(d, selected?.id ?? "") ? 2.3 : 1.5);
    const nodeG = layer.append("g").selectAll("g").data(nodes).join("g").attr("class", "node-g");
    nodeG.append("circle").attr("r", nodeRadius).attr("fill", (d) => COLORS[d.kind] ?? "#888").attr("stroke", (d) => selected?.id === d.id ? "#fff" : "transparent").attr("stroke-width", 2);
    nodeG.append("text").attr("dy", "0.35em").attr("x", (d) => nodeRadius(d) + 4).text((d) => d.label || d.title).attr("font-size", 11).attr("fill", "var(--text)").attr("pointer-events", "none");
    nodeG.style("cursor", "pointer").on("click", (_, d) => onSelect(selected?.id === d.id ? null : d));

    const sim = _buildSim(nodes, edges, w, h);
    sim.on("tick", () => {
      links
        .attr("x1", (d) => _asPoint(d.source).x)
        .attr("y1", (d) => _asPoint(d.source).y)
        .attr("x2", (d) => _asPoint(d.target).x)
        .attr("y2", (d) => _asPoint(d.target).y);
      nodeG.attr("transform", (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    return () => { sim.stop(); };
  }, [graph, filter, search, selected, onSelect]);

  return <svg ref={svgRef} id="graph" className="graph-canvas" role="img" aria-label="Knowledge graph" />;
}


function _isSelectedEdge(edge: SimLink, selectedId: string): boolean {
  if (!selectedId) return false;
  const source = typeof edge.source === "object" ? edge.source.id : String(edge.source);
  const target = typeof edge.target === "object" ? edge.target.id : String(edge.target);
  return source === selectedId || target === selectedId;
}

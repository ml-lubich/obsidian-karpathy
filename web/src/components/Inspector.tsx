import type { GraphData, GraphNode } from "../types";

interface Props {
  node: GraphNode | null;
  graph: GraphData;
  onSelect: (node: GraphNode | null) => void;
}

function MetaGrid({ node }: { node: GraphNode }) {
  return (
    <div className="meta-grid">
      <div className="stat"><b>{node.backlinks ?? 0}</b><span>Backlinks</span></div>
      <div className="stat"><b>{node.outlinks ?? 0}</b><span>Outlinks</span></div>
      <div className="stat"><b>{node.word_count ?? 0}</b><span>Words</span></div>
      <div className="stat"><b>{node.kind}</b><span>Kind</span></div>
    </div>
  );
}

function TagList({ tags }: { tags: string[] }) {
  if (!tags.length) return null;
  return (
    <>
      <h3>Tags</h3>
      <div>{tags.map((t) => <span key={t} className="pill">#{t}</span>)}</div>
    </>
  );
}


function _relatedNodes(node: GraphNode, graph: GraphData): GraphNode[] {
  const linked = new Set<string>();
  for (const edge of graph.edges) {
    if (edge.source === node.id) linked.add(edge.target);
    if (edge.target === node.id) linked.add(edge.source);
  }
  return graph.nodes.filter((candidate) => linked.has(candidate.id)).slice(0, 24);
}

export function Inspector({ node, graph, onSelect }: Props) {
  if (!node) {
    return (
      <div>
        <h2>No node selected</h2>
        <p>Click a node in the graph to inspect its links, backlinks, tags, and summary.</p>
      </div>
    );
  }

  const related = _relatedNodes(node, graph);

  return (
    <div>
      <h2>{node.title}</h2>
      {node.path && <p className="path">{node.path}</p>}
      <p>{node.summary || `${node.kind} node`}</p>
      <MetaGrid node={node} />
      <TagList tags={node.tags ?? []} />

      {node.markdown && (
        <>
          <h3>Markdown</h3>
          <pre className="markdown-preview">{node.markdown}</pre>
        </>
      )}

      <h3>Connected nodes</h3>
      <div className="related-wrap">
        {related.map((relatedNode) => (
          <button key={relatedNode.id} className="related-node" onClick={() => onSelect(relatedNode)}>
            {relatedNode.label || relatedNode.title}
          </button>
        ))}
      </div>
    </div>
  );
}

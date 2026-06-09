import type { GraphNode } from "../types";

interface Props {
  node: GraphNode | null;
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

export function Inspector({ node }: Props) {
  if (!node) {
    return (
      <div>
        <h2>No node selected</h2>
        <p>Click a node in the graph to inspect its links, backlinks, tags, and summary.</p>
      </div>
    );
  }

  return (
    <div>
      <h2>{node.title}</h2>
      {node.path && <p className="path">{node.path}</p>}
      <p>{node.summary || `${node.kind} node`}</p>
      <MetaGrid node={node} />
      <TagList tags={node.tags ?? []} />
    </div>
  );
}

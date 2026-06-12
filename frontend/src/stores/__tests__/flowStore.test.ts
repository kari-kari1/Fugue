import { describe, it, expect, beforeEach } from 'vitest';
import { useFlowStore, validateDAG } from '../flowStore';
import type { Node, Edge, Connection } from '@xyflow/react';

// Reset store between tests
beforeEach(() => {
  useFlowStore.setState({
    nodes: [],
    edges: [],
    selectedNode: null,
    clipboard: null,
  });
});

const makeAgentNode = (id: string, name = 'Agent'): Node => ({
  id,
  type: 'agent',
  position: { x: 0, y: 0 },
  data: { name, role: 'researcher', llm_provider: 'openai', llm_model: 'gpt-4o', tools: [] },
});

const makeTaskNode = (id: string, name = 'Task'): Node => ({
  id,
  type: 'task',
  position: { x: 0, y: 0 },
  data: { name, description: 'test', output_type: 'text' },
});

describe('flowStore — node CRUD', () => {
  it('adds a node', () => {
    const { addNode } = useFlowStore.getState();
    addNode(makeAgentNode('a1'));
    expect(useFlowStore.getState().nodes).toHaveLength(1);
    expect(useFlowStore.getState().nodes[0].id).toBe('a1');
  });

  it('removes a node and its connected edges', () => {
    const { addNode, removeNode } = useFlowStore.getState();
    addNode(makeAgentNode('a1'));
    addNode(makeTaskNode('t1'));
    // Use onConnect to add edge (goes through validation)
    useFlowStore.getState().onConnect({ source: 'a1', target: 't1' } as Connection);
    expect(useFlowStore.getState().edges).toHaveLength(1);

    removeNode('a1');
    const state = useFlowStore.getState();
    expect(state.nodes).toHaveLength(1);
    expect(state.nodes[0].id).toBe('t1');
    expect(state.edges).toHaveLength(0);
  });

  it('updates node data', () => {
    const { addNode, updateNodeData } = useFlowStore.getState();
    addNode(makeAgentNode('a1', 'Old Name'));
    updateNodeData('a1', { name: 'New Name' });
    expect(useFlowStore.getState().nodes[0].data.name).toBe('New Name');
  });
});

describe('validateDAG (standalone)', () => {
  it('validates an empty graph with errors (no tasks, no agents)', () => {
    const result = validateDAG([], []);
    expect(result.valid).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
  });

  it('detects a cycle', () => {
    const nodes = [
      makeTaskNode('t1', 'Task 1'),
      makeTaskNode('t2', 'Task 2'),
    ];
    const edges: Edge[] = [
      { id: 'e1', source: 't1', target: 't2' },
      { id: 'e2', source: 't2', target: 't1' },
    ];
    const result = validateDAG(nodes, edges);
    expect(result.errors.some((e) => e.type === 'cycle')).toBe(true);
  });

  it('passes for a valid DAG', () => {
    const nodes = [
      makeAgentNode('a1'),
      makeTaskNode('t1'),
      makeTaskNode('t2'),
    ];
    const edges: Edge[] = [
      { id: 'e1', source: 'a1', target: 't1' },
      { id: 'e2', source: 'a1', target: 't2' },
    ];
    const result = validateDAG(nodes, edges);
    expect(result.errors.filter((e) => e.type === 'cycle')).toHaveLength(0);
  });
});

describe('flowStore — onConnect validation', () => {
  it('prevents self-loops', () => {
    useFlowStore.setState({ nodes: [makeTaskNode('t1')], edges: [] });
    useFlowStore.getState().onConnect({ source: 't1', target: 't1' } as Connection);
    expect(useFlowStore.getState().edges).toHaveLength(0);
  });

  it('prevents agent-as-target', () => {
    const nodes = [makeTaskNode('t1'), makeAgentNode('a1')];
    useFlowStore.setState({ nodes, edges: [] });
    useFlowStore.getState().onConnect({ source: 't1', target: 'a1' } as Connection);
    expect(useFlowStore.getState().edges).toHaveLength(0);
  });

  it('allows agent-to-task connection', () => {
    const nodes = [makeAgentNode('a1'), makeTaskNode('t1')];
    useFlowStore.setState({ nodes, edges: [] });
    useFlowStore.getState().onConnect({ source: 'a1', target: 't1' } as Connection);
    expect(useFlowStore.getState().edges).toHaveLength(1);
  });

  it('allows task-to-task connection', () => {
    const nodes = [makeTaskNode('t1'), makeTaskNode('t2')];
    useFlowStore.setState({ nodes, edges: [] });
    useFlowStore.getState().onConnect({ source: 't1', target: 't2' } as Connection);
    expect(useFlowStore.getState().edges).toHaveLength(1);
  });
});

describe('flowStore — clipboard', () => {
  it('copies selected node and pastes with new ID', () => {
    const { addNode, setSelectedNode, copySelected, paste } = useFlowStore.getState();
    addNode(makeAgentNode('a1', 'Original'));
    setSelectedNode(useFlowStore.getState().nodes[0]);
    copySelected();
    paste();
    const state = useFlowStore.getState();
    expect(state.nodes).toHaveLength(2);
    expect(state.nodes[1].id).not.toBe('a1');
    expect((state.nodes[1].data as any).name).toBe('Original');
  });

  it('does nothing when clipboard is empty', () => {
    useFlowStore.getState().paste();
    expect(useFlowStore.getState().nodes).toHaveLength(0);
  });
});

import type { EdgeTypes } from '@xyflow/react';
import CyberTrail from '../cyber/CyberTrail';

// 注册 cyber 和 particle 两种类型名 — 既处理新建连线也处理已有的 particle 类型边
export const cyberEdgeTypes: EdgeTypes = {
  cyber: CyberTrail,
  particle: CyberTrail,
};

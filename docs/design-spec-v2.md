# Fugue 设计方案 V2：双态动能 (Dual-State Kinetic)

> **一句话定义**：静态是 Apple.com 级别的克制艺术品，动态是 WWDC 级别的赛博光流引擎，两者通过弹簧物理动效无缝连接。
>
> 设计哲学：**静若处子，动若脱兔。**

---

## 一、双态架构总览

```
┌─────────────────────────────────────────────────────────┐
│                    Fugue 双态系统                     │
├──────────────────────┬──────────────────────────────────┤
│   STATE 1: CARBON    │   STATE 2: CYBER                 │
│   (静态 / 配置态)     │   (动态 / 执行态)                 │
│                      │                                  │
│   ● 纯白 / 纯黑      │   ● 纯黑深渊 #000000             │
│   ● Apple 极简排版    │   ● 霓虹光轨 + 粒子              │
│   ● 弹簧遮罩动效     │   ● 节点脉冲呼吸光               │
│   ● 克制到极致       │   ● 夸张到极致                    │
│                      │                                  │
│   适用页面：          │   适用页面：                      │
│   - Login / Register │   - ExecutionView (运行中)        │
│   - Dashboard        │   - Editor 画布 (运行时变形)       │
│   - Templates        │   - 实时监控面板                   │
│   - Settings         │                                  │
│   - Plugins          │                                  │
│   - Editor (编辑态)   │                                  │
│   - Published        │                                  │
│   - Webhooks         │                                  │
│   - Schedules        │                                  │
├──────────────────────┴──────────────────────────────────┤
│              TRANSITION: 隧道纵深缩放                      │
│   ● 共有元素锁定 → 空间拉远 → 色彩暗转 → 霓虹点亮          │
│   ● 持续 0.6s, spring(120, 14)                          │
└─────────────────────────────────────────────────────────┘
```

---

## 二、STATE 1: CARBON — 静态配置态

### 2.1 视觉规范

#### 2.1.1 背景

| 模式 | 色值 | 用途 |
|------|------|------|
| Light | `#FFFFFF` 纯白 | 主背景，不含任何灰色杂色 |
| Dark | `#000000` 纯黑 | 主背景，不含灰色 |
| 表面层 Light | `#FBFBFD` | 卡片底色（极浅，接近白） |
| 表面层 Dark | `#0A0A0A` | 卡片底色（极浅灰，接近黑） |

**禁止**：`#F3F4F6`、`#E5E7EB` 等浑浊灰色背景。表面层只能用近乎透明的微量灰。

#### 2.1.2 排版系统

**字体**：
- 首选：SF Pro Display（macOS/iOS 内置）
- 备选：Geist（Vercel 开源）或 Inter Display
- 代码：JetBrains Mono / SF Mono

**字重策略 — 极端对比制造高级感**：

| 元素 | 字重 | 示例 |
|------|------|------|
| 页面标题 | `800 (Heavy)` | `Your Workflows.` |
| 数据/数字 | `400 (Regular)` | `12 agents · 3 running` |
| 辅助文字 | `300 (Light)` | `Last updated 2 min ago` |
| **绝对禁止** | `500 Medium` / `600 Semibold` | 中等粗细 = 平庸 |

**字号系统**：

| Token | Size | 用途 |
|-------|------|------|
| `display` | 64px / 72px | 页面主标题（如 Apple 的 "iPhone 16 Pro."） |
| `headline` | 40px / 48px | 区域标题 |
| `title` | 24px / 28px | 卡片标题 |
| `body` | 15px / 17px | 正文 |
| `caption` | 12px / 13px | 辅助说明 |
| `mono` | 13px | 代码、ID、数据 |

**行高**：标题 `1.05-1.1`（紧凑），正文 `1.5-1.6`（舒适）

**字间距**：标题 `-0.02em`（紧排，Apple 特征），正文 `0`（默认）

#### 2.1.3 颜色系统

**静态态下，颜色极度克制**：

| Token | Light | Dark | 用途 |
|-------|-------|------|------|
| `text-primary` | `#1D1D1F` | `#F5F5F7` | 主要文字 |
| `text-secondary` | `#86868B` | `#86868B` | 次要文字（两个模式下同色） |
| `text-tertiary` | `#AEAEB2` | `#6E6E73` | 占位符、禁用文字 |
| `accent` | `#0071E3` | `#2997FF` | 唯一强调色（Apple Blue） |
| `accent-hover` | `#0077ED` | `#4DA6FF` | 悬停态 |
| `success` | `#30D158` | `#30D158` | 完成态 |
| `error` | `#FF3B30` | `#FF453A` | 错误态 |
| `warning` | `#FF9F0A` | `#FF9F0A` | 警告态 |

**关键原则**：
- 静态态下**只有一个强调色**（Apple Blue），不用彩虹色
- 文字与背景对比度 ≥ 7:1（AAA 级）
- 不使用渐变背景（渐变只在动态态出现）

#### 2.1.4 间距系统

基于 **8pt 网格**：

| Token | Value | 用途 |
|-------|-------|------|
| `xs` | 4px | 图标与文字间距 |
| `sm` | 8px | 紧凑元素间距 |
| `md` | 16px | 卡片内边距 |
| `lg` | 24px | 区域间距 |
| `xl` | 32px | 大区域分隔 |
| `2xl` | 48px | 页面级间距 |
| `3xl` | 64px | 标题与内容间距 |
| `4xl` | 96px | 英雄区间距 |

#### 2.1.5 圆角系统

| Token | Value | 用途 |
|-------|-------|------|
| `squircle-sm` | 8px | 按钮、输入框 |
| `squircle-md` | 12px | 卡片 |
| `squircle-lg` | 20px | 大卡片、模态框 |
| `pill` | 980px | 胶囊节点、标签 |

**关键**：使用 `border-radius` + 极轻微的 `box-shadow: 0 0 0 0.5px rgba(0,0,0,0.04)` 做边框，**不使用**显眼的 border。

#### 2.1.6 阴影系统

静态态下阴影**几乎不可见**，仅用于暗示层级：

| Token | Value |
|-------|-------|
| `shadow-subtle` | `0 1px 2px rgba(0,0,0,0.04)` |
| `shadow-card` | `0 2px 8px rgba(0,0,0,0.06)` |
| `shadow-elevated` | `0 8px 30px rgba(0,0,0,0.08)` |

**禁止**：重阴影、彩色阴影、发光阴影（这些只在动态态使用）。

---

### 2.2 组件规范 — 静态态

#### 2.2.1 按钮

**Primary Button**：
```
背景：#0071E3 (Light) / #2997FF (Dark)
文字：#FFFFFF
字重：400
字号：15px
圆角：squircle-sm (8px)
内边距：12px 22px
悬停：背景变亮 5%，scale(1.02)
按下：scale(0.98)，弹簧回弹
无阴影
```

**Secondary Button**：
```
背景：透明
边框：1px solid rgba(0,0,0,0.08)
文字：#1D1D1F (Light) / #F5F5F7 (Dark)
悬停：背景 rgba(0,0,0,0.03)
按下：scale(0.98)
```

**Ghost Button**：
```
背景：透明
文字：#0071E3
悬停：背景 rgba(0,113,227,0.06)
按下：scale(0.98)
```

#### 2.2.2 卡片

```
背景：#FBFBFD (Light) / #0A0A0A (Dark)
圆角：squircle-md (12px)
边框：无（用极微弱阴影分隔层级）
内边距：24px
悬停：translateY(-2px)，shadow-card 增强
进入动画：遮罩揭示（见动效章节）
```

#### 2.2.3 输入框

```
背景：#FFFFFF (Light) / #1D1D1F (Dark)
边框：1px solid rgba(0,0,0,0.08)
圆角：squircle-sm (8px)
内边距：12px 16px
字号：15px
聚焦：边框变为 accent，无外发光
标签：浮动标签（label 在输入框内部上方，字号 12px）
```

#### 2.2.4 侧边面板（PropertyPanel）

```
背景：rgba(255,255,255,0.85) backdrop-blur(20px) (Light)
       rgba(10,10,10,0.85) backdrop-blur(20px) (Dark)
宽度：320px
圆角：squircle-lg (20px)
边距：距画布边缘 12px
进入方式：共有元素形变（见动效章节）
```

#### 2.2.5 导航栏

```
背景：rgba(255,255,255,0.72) backdrop-blur(20px) (Light)
       rgba(0,0,0,0.72) backdrop-blur(20px) (Dark)
高度：52px
边框：底部 hairline rgba(0,0,0,0.06)
Logo：左侧，SF Pro Heavy 18px
导航项：字重 400，字号 13px，间距 28px
活跃项：下划线指示器（2px accent，圆角 pill）
```

#### 2.2.6 Agent 节点（编辑态）

```
形状：胶囊（pill 圆角）
背景：#F5F5F7 (Light) / #1D1D1F (Dark)
尺寸：180px × 56px
边框：无
阴影：shadow-subtle
内容：
  - 左侧：几何 SVG 图标（渐变色，20px）
  - 中间：名称（15px, 500）、角色（12px, 300, text-secondary）
  - 右上：状态指示点（8px 圆点）
顶部：2px accent 色线（标识类型）
连线：1px #D2D2D7 线，无箭头
```

#### 2.2.7 Task 节点（编辑态）

```
形状：圆角矩形
背景：#F0FDF4 (Light) / #0A1A0A (Dark) — 极淡绿
尺寸：200px × 72px
其余同 Agent 节点
```

---

### 2.3 动效规范 — Carbon Neutral Kinetic

> 这是静态态的灵魂。**普通的 fade-in/out 绝对不够。**

#### 2.3.1 核心技术栈

| 技术 | 用途 | 必要性 |
|------|------|--------|
| **Framer Motion** | 所有组件动效 | 必须 |
| **Clip-path masking** | 文字遮罩揭示 | 必须 |
| **Spring physics** | 所有弹性运动 | 必须 |
| **Shared Layout (layoutId)** | 节点↔面板形变 | 必须 |

**禁用**：CSS `transition` 的 `ease-in-out` 做主过渡。所有动效必须用 Framer Motion 的 spring 物理引擎。

#### 2.3.2 全局弹簧参数

```typescript
// 标准弹簧 — 用于大多数过渡
const SPRING_DEFAULT = {
  type: "spring",
  damping: 25,       // 阻尼：越高越快停下，无回弹
  stiffness: 200,    // 刚度：越高初速度越快
  mass: 0.5          // 质量：越小越轻快
};

// 快速弹簧 — 用于微交互（按钮、标签）
const SPRING_SNAPPY = {
  type: "spring",
  damping: 30,
  stiffness: 400,
  mass: 0.3
};

// 柔和弹簧 — 用于大面积过渡（页面切换）
const SPRING_GENTLE = {
  type: "spring",
  damping: 20,
  stiffness: 120,
  mass: 0.8
};

// 超级弹簧 — 用于文字揭示
const SPRING_REVEAL = {
  type: "spring",
  damping: 25,
  stiffness: 200,
  mass: 0.5
};
```

#### 2.3.3 文字遮罩揭示 (Text Reveal)

**这是页面加载时的第一个 wow moment。**

```tsx
// 组件：<TextReveal />
const revealVariants = {
  hidden: {
    y: "100%",
    clipPath: "inset(0% 0% 100% 0%)"
  },
  visible: {
    y: "0%",
    clipPath: "inset(0% 0% 0% 0%)",
    transition: SPRING_REVEAL
  }
};

// 使用方式
<TextReveal>
  <h1 className="text-display">Your Workflows.</h1>
</TextReveal>
```

**效果**：标题从下方以极快速度、带 Q 弹阻尼感向上滑出，如同被一把无形的刀从缝隙中切开揭示。

#### 2.3.4 瀑布流坠落 (Cascade Stagger)

**标题下方的次级元素依次出现：**

```tsx
const cascadeContainer = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.05,  // 每个子元素延迟 50ms
      delayChildren: 0.1      // 父容器延迟 100ms 后开始
    }
  }
};

const cascadeItem = {
  hidden: {
    y: 40,
    opacity: 0,
    clipPath: "inset(0% 0% 60% 0%)"
  },
  visible: {
    y: 0,
    opacity: 1,
    clipPath: "inset(0% 0% 0% 0%)",
    transition: SPRING_DEFAULT
  }
};
```

**效果**：按钮、描述文字等次级元素以 50ms 间隔依次从下方弹出，有一种"字母在跳舞"的灵动感。

#### 2.3.5 共有元素形变 (Shared Layout Transition)

**点击 Agent 节点 → 右侧配置面板展开：**

```tsx
// 画布上的节点
<motion.div
  layoutId={`agent-${node.id}`}
  className="node-capsule"  // 180×56 胶囊
>
  <AgentIcon /> {agentName}
</motion.div>

// 点击后展开的配置面板
<motion.div
  layoutId={`agent-${node.id}`}
  className="property-panel"  // 320px 宽面板
>
  <AgentConfigForm />
</motion.div>
```

**效果**：Framer Motion 自动计算两个元素的几何位置差，生成完美的无缝形变动画。胶囊节点像被拉伸一样膨胀为配置面板，关闭时收缩回去。

#### 2.3.6 页面切换动效

```
离开页面：
  - 标题文字向左滑出并被 clip-path 裁切消失
  - 持续 200ms, SPRING_SNAPPY

进入页面：
  - 新页面标题从右侧遮罩滑入
  - 次级元素瀑布流坠落（stagger 50ms）
  - 持续 300ms, SPRING_DEFAULT

方向规则：
  - 前进导航（Dashboard → Editor）：内容从右侧进入
  - 后退导航（Editor → Dashboard）：内容从左侧进入
```

#### 2.3.7 按钮微交互

```
悬停：scale(1.02), spring(300, 20)
按下：scale(0.97), spring(400, 30)
释放：scale(1.0), spring(200, 25)
反馈延迟：< 80ms
```

#### 2.3.8 卡片悬停

```
悬停：translateY(-2px), shadow 增强
过渡：spring(200, 25), 150ms
按下：scale(0.99)
```

#### 2.3.9 列表项进入

```
每个列表项：
  - 从 y:20 opacity:0 开始
  - spring(200, 25) 弹入
  - stagger: 30ms（比文字揭示更快）

用于：Dashboard 的 Crew 卡片列表、模板列表
```

---

## 三、STATE 2: CYBER — 动态执行态

### 3.1 触发条件

当用户点击 **「运行」** 按钮时，界面从 CARBON 态无缝过渡到 CYBER 态。

触发场景：
- 点击「运行工作流」
- 进入 ExecutionView 且状态为 `running`
- Editor 画布进入执行模式

恢复条件：
- 执行完成/失败/取消
- 用户点击「返回编辑」
- 3 秒延迟后渐变回 CARBON（可配置）

### 3.2 视觉规范

#### 3.2.1 背景

```
绝对纯黑：#000000
无任何表面层、无网格、无十字标
画布变为"深渊" — 无限空间感
```

#### 3.2.2 霓虹色彩系统

| Token | 色值 | 用途 |
|-------|------|------|
| `neon-cyan` | `#00F5FF` | 主光轨、活跃节点 |
| `neon-purple` | `#A855F7` | 次光轨、Agent 激活 |
| `neon-pink` | `#FF2D78` | 错误态、警告 |
| `neon-green` | `#00FF88` | 完成态、成功 |
| `neon-amber` | `#FFB800` | 等待态、队列中 |
| `neon-blue` | `#3B82F6` | 信息流、数据传输 |

**渐变**：光轨使用多色渐变
```
linear-gradient(90deg, #A855F7, #00F5FF, #00FF88)
```

#### 3.2.3 文字

```
主文字：#FFFFFF
次文字：rgba(255,255,255,0.6)
状态文字：使用对应 neon 色
所有文字加 text-shadow: 0 0 10px rgba(对应色, 0.5)
```

#### 3.2.4 节点（执行态）

```
边框：1px neon-cyan + 外发光
  box-shadow:
    0 0 15px rgba(0,245,255,0.3),
    0 0 30px rgba(0,245,255,0.1),
    inset 0 0 15px rgba(0,245,255,0.05)
背景：rgba(0,245,255,0.03) — 几乎透明

正在执行的节点：
  - 边框呼吸动画（opacity 0.5→1→0.5, 2s 周期）
  - 内部状态文字打字机闪烁："Processing..."
  - 外发光脉冲（shadow 半径 15px→25px→15px）

已完成节点：
  - 边框变为 neon-green
  - 内部显示 ✓ + 完成时间
  - 外发光稳定

失败节点：
  - 边框变为 neon-pink
  - 闪烁 3 次后稳定
```

#### 3.2.5 连线（执行态）

**霓虹光轨 — WWDC 级别的流光效果：**

```css
.cyber-trail {
  stroke: url(#neon-gradient);
  stroke-width: 3px;
  stroke-linecap: round;
  filter: drop-shadow(0 0 8px rgba(0, 245, 255, 0.6))
          drop-shadow(0 0 20px rgba(168, 85, 247, 0.3));
  stroke-dasharray: 40 1000;
  animation: flowLight 1.5s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

@keyframes flowLight {
  from { stroke-dashoffset: 1040; }
  to { stroke-dashoffset: 0; }
}
```

**效果**：
- 光轨从源节点射向目标节点
- 带有拖尾效果（dasharray 40px 光点 + 1000px 间隔）
- 双层外发光（cyan + purple）
- 运动速度与数据流速同步

**连线 SVG 渐变定义：**
```svg
<defs>
  <linearGradient id="neon-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#A855F7" />
    <stop offset="50%" stop-color="#00F5FF" />
    <stop offset="100%" stop-color="#00FF88" />
  </linearGradient>
</defs>
```

#### 3.2.6 粒子系统

在光轨路径上添加微粒子：

```
粒子数量：每条连线 5-8 个
粒子大小：2-4px
粒子颜色：同光轨渐变
运动：沿 SVG path 匀速运动，animateMotion
粒子尾迹：CSS drop-shadow 4px
生命周期：沿 path 走完即消亡，循环重生
```

```svg
<circle r="2" fill="#00F5FF">
  <animateMotion dur="1.5s" repeatCount="indefinite">
    <mpath href="#trail-path" />
  </animateMotion>
</circle>
```

#### 3.2.7 环境粒子背景

在纯黑背景上飘散微弱的环境粒子：

```
粒子数量：50-100 个
粒子大小：1-2px
粒子颜色：rgba(255,255,255,0.1) — 极微弱
运动：随机布朗运动，速度 0.5-2px/s
效果：营造深度空间感，暗示"数据在流动"
实现：Canvas 2D 或 CSS animation
```

#### 3.2.8 数据面板（执行态）

```
背景：rgba(0,0,0,0.8) backdrop-blur(12px)
边框：1px solid rgba(0,245,255,0.15)
圆角：squircle-md
内边距：16px
标题：neon-cyan, 13px, 500
数值：#FFFFFF, 24px, 300, font-mono
图表/进度条：neon-cyan 渐变填充
```

---

## 四、TRANSITION: 隧道纵深过渡

### 4.1 触发

点击「运行」的瞬间。

### 4.2 动画序列（总时长 0.6s）

```
Phase 1: 色彩暗转 (0ms - 200ms)
  - 白色背景以 center-out 径向渐变暗转为纯黑
  - 所有静态 UI 元素 opacity → 0
  - 文字 clip-path 裁切消失
  - easing: cubic-bezier(0.4, 0, 0.2, 1)

Phase 2: 空间拉远 (100ms - 400ms, 与 Phase 1 重叠)
  - 视角 Zoom Out（scale 1.0 → 0.85 → 1.0）
  - 类似无人机升高俯瞰全局
  - 元素沿 Z 轴后退（translateZ）
  - easing: spring(120, 14)

Phase 3: 霓虹点亮 (300ms - 600ms)
  - 从第一个节点开始，霓虹光依次点亮
  - 光轨从源节点射出，带动连线亮起
  - 环境粒子淡入
  - easing: spring(200, 20)
```

### 4.3 反向过渡（执行结束 → 回到静态）

```
Phase 1: 光轨收拢 (0ms - 200ms)
  - 光轨从两端向中间收缩
  - 粒子淡出
  - neon 色逐渐 desaturate

Phase 2: 空间推近 (100ms - 300ms)
  - Zoom In（scale 0.85 → 1.0）
  - 背景从纯黑渐变为纯白
  - easing: spring(150, 18)

Phase 3: 元素恢复 (200ms - 500ms)
  - 静态 UI 元素依次遮罩揭示弹入
  - 按钮、导航栏恢复
  - stagger 50ms
  - 弹出成功/失败 toast
```

### 4.4 共有元素过渡

在两个态之间，以下元素**保持位置连续性**（Shared Layout）：
- 工作流名称标题
- 节点位置（不移动，只改变视觉样式）
- 侧边栏/面板

**不做连续的元素**（直接消失/出现）：
- 导航栏（静态态有，动态态无）
- 操作按钮（运行/编辑按钮）
- 背景装饰元素

---

## 五、页面级设计规格

### 5.1 Login 页面 (CARBON)

```
布局：全屏居中，上下大量留白
背景：纯白/纯黑
标题：超大字号 "Welcome to Fugue." (display, 64px)
副标题：Light 字重 "Build intelligent workflows." (20px)
表单：
  - 邮箱输入框 + 密码输入框
  - 登录按钮（Primary，全宽）
  - 注册链接（Ghost，居中）
动效：
  - 标题：文字遮罩揭示
  - 副标题：stagger 50ms 后遮罩揭示
  - 表单：stagger 100ms 后从下方弹入
  - 按钮：stagger 150ms
```

### 5.2 Dashboard 页面 (CARBON)

```
布局：左侧导航栏 + 右侧内容区
顶部：
  - 超大标题 "Your Workflows." (display, 56px)
  - 右侧：「新建工作流」按钮（Primary）
内容区：
  - Crew 卡片网格（3列，响应式）
  - 每张卡片：名称、描述、Agent/Task 数量、最后运行时间
  - 空状态：居中大文字 "Create your first workflow." + 按钮
搜索栏：
  - 位于标题下方，全宽
  - placeholder: "Search workflows..."
动效：
  - 页面标题：遮罩揭示
  - 搜索栏：stagger 50ms
  - 卡片列表：stagger 30ms，每张卡片从下方弹入
  - 卡片悬停：translateY(-2px) + 阴影增强
  - 卡片点击：scale(0.98) → 跳转
```

### 5.3 Editor 页面 — 编辑态 (CARBON)

```
布局：顶部工具栏 + 中央画布 + 右侧面板
顶部工具栏：
  - 左侧：返回按钮 + 工作流名称（可编辑）
  - 中间：节点添加工具栏（Agent / Task / Condition / Loop / Review）
  - 右侧：验证状态 + 运行按钮（Primary，带 ▶ 图标）
画布：
  - 背景：纯白/纯黑，无网格（或极微弱的 dot grid, opacity 0.03）
  - 节点：胶囊/矩形，CARBON 风格
  - 连线：1px 灰线
  - 选中节点：边框变为 accent
右侧面板：
  - 选中节点后出现
  - 共有元素形变进入（从节点膨胀为面板）
  - backdrop-blur 磨砂玻璃
动效：
  - 节点拖拽：实时跟随，spring 物理
  - 连线创建：从源端拖出一条虚线，松开后变为实线
  - 节点选中 → 面板展开：Shared Layout 形变
  - 面板关闭：收缩回节点
```

### 5.4 Editor 页面 — 执行态 (CYBER)

```
触发：点击「运行」
过渡：隧道纵深过渡（0.6s）
画布变形：
  - 背景：白 → 黑
  - 节点：胶囊 → 带霓虹边框的半透明节点
  - 连线：灰线 → 霓虹光轨
  - 环境粒子出现
新增元素：
  - 顶部状态栏：执行状态 + 耗时 + 费用
  - 右侧：实时思考面板（RealtimeThoughts），neon 风格
  - 节点内：状态文字 + 进度指示
工具栏变形：
  - 「运行」按钮变为「暂停」+「取消」
  - 按钮风格变为 neon outline
```

### 5.5 ExecutionView 页面 (CYBER)

```
进入：从 Editor 执行态直接进入，无额外过渡
背景：纯黑
布局：
  - 左侧面板：执行信息（名称、状态、耗时、费用、Token）
  - 中央：执行流程图（节点 + 光轨）
  - 右侧：实时日志流
  - 底部：时间线进度条
信息面板：
  - 半透明黑底 + neon 边框
  - 数字使用 mono 字体，neon-cyan
  - 进度条：neon-cyan 渐变
日志流：
  - 等宽字体
  - 不同类型事件使用不同 neon 色
  - 自动滚动 + 手动暂停
执行完成：
  - 光轨收拢 → 霓虹熄灭 → 背景渐白 → 回到 CARBON
  - 弹出结果摘要卡片（CARBON 风格，遮罩揭示进入）
```

### 5.6 Templates 页面 (CARBON)

```
布局：顶部标题 + 分类筛选 + 模板网格
标题："Templates." (display, 56px)
筛选栏：pill 形标签（全部 / 编码 / 分析 / 写作 / 研究）
模板卡片：
  - 200px 高
  - 图标 + 名称 + 描述 + Agent 数量 + 使用次数
  - 角标：⭐ 评分
动效：
  - 筛选切换：卡片 crossfade + 位移
  - 卡片进入：stagger 30ms 遮罩揭示
```

### 5.7 Settings 页面 (CARBON)

```
布局：左右分栏（左侧菜单，右侧内容）
标题："Settings." (display, 48px)
左侧菜单：
  - LLM Provider / API Keys / General
  - 字重 400，选中项字重 500 + accent 色
右侧面板：
  - Provider 卡片列表
  - 每个 Provider：图标 + 名称 + 状态指示 + 配置表单
  - 表单：标准输入框 + 保存按钮
```

### 5.8 其他页面（Published / Webhooks / Schedules / Plugins）

统一遵循 CARBON 态规范：
- 大标题 + 空白 + 内容区
- 列表使用 stagger 进入
- 空状态：居中大文字 + 引导按钮
- 表格使用极简样式（无 border，仅 hairline 分隔行）

---

## 六、技术实现清单

### 6.1 依赖变更

```json
// 新增依赖
{
  "framer-motion": "^11.0.0",        // 核心动效引擎
  "@fontsource/geist-sans": "^1.0.0", // 字体（如不用 SF Pro）
  "@fontsource/geist-mono": "^1.0.0", // 等宽字体
  "tsparticles": "^3.0.0"             // 环境粒子（可选，也可手写 Canvas）
}
```

### 6.2 文件结构变更

```
frontend/src/
├── design/
│   ├── tokens.ts              // 设计 Token 定义
│   ├── springs.ts             // 弹簧参数常量
│   └── themes.ts              // CARBON / CYBER 主题切换逻辑
├── components/
│   ├── ui/
│   │   ├── TextReveal.tsx     // 文字遮罩揭示组件
│   │   ├── CascadeReveal.tsx  // 瀑布流容器
│   │   ├── CyberNode.tsx      // 赛博态节点组件
│   │   ├── CyberTrail.tsx     // 霓虹光轨连线
│   │   ├── NeonGlow.tsx       // 霓虹发光效果封装
│   │   ├── ParticleField.tsx  // 环境粒子背景
│   │   └── TunnelTransition.tsx // 隧道过渡控制器
│   ├── layout/
│   │   ├── CarbonShell.tsx    // 静态态布局壳
│   │   └── CyberShell.tsx     // 动态态布局壳
│   └── ...existing...
├── hooks/
│   ├── useThemeTransition.ts  // 双态切换 Hook
│   └── useReducedMotion.ts    // 无障碍：检测减弱动效偏好
└── index.css                  // 重写：纯设计 Token 变量
```

### 6.3 关键实现原则

1. **所有动效用 Framer Motion**，不用 CSS transition/animation（除光轨 dashoffset 动画）
2. **spring 物理引擎**替代所有 cubic-bezier
3. **clip-path masking** 替代 opacity fade
4. **Shared Layout (layoutId)** 用于所有空间连续性过渡
5. **`prefers-reduced-motion`** 无障碍：检测后禁用所有动效，使用即时切换
6. **GPU 加速**：所有动画元素使用 `will-change: transform, opacity`
7. **60fps 保证**：只动画 `transform` 和 `opacity`，不动画 `width/height/top/left`

---

## 七、无障碍与性能

### 7.1 无障碍

| 需求 | 实现 |
|------|------|
| 减弱动效 | `prefers-reduced-motion: reduce` → 禁用所有 spring 动画，使用 instant 切换 |
| 对比度 | 静态态 ≥ 7:1 (AAA)；动态态 neon 色在纯黑上 ≥ 4.5:1 |
| 键盘导航 | 所有交互元素可达，Tab 顺序匹配视觉顺序 |
| 屏幕阅读器 | ARIA label 覆盖所有状态变化 |

### 7.2 性能

| 关注点 | 策略 |
|--------|------|
| Framer Motion 包体积 | tree-shake，只导入 `motion` 和 `AnimatePresence` |
| 粒子系统 | Canvas 2D，非 SVG/DOM 操作 |
| 光轨动画 | CSS `@keyframes` + SVG `animateMotion`（GPU 加速） |
| backdrop-blur | 仅用于面板/导航，不做全屏模糊 |
| will-change | 仅在动画进行时添加，动画结束后移除 |

---

## 八、实施路线

| 阶段 | 内容 | 工期 |
|------|------|------|
| **Phase 1** | 设计 Token + 弹簧系统 + TextReveal 组件 + index.css 重写 | 2-3天 |
| **Phase 2** | CARBON 态页面重写（Login/Dashboard/Settings/Templates） | 3-4天 |
| **Phase 3** | Editor 画布 CARBON 态 + 节点组件 + Shared Layout 面板 | 2-3天 |
| **Phase 4** | CYBER 态基础设施（neon 色系 + 光轨 + 粒子） | 3-4天 |
| **Phase 5** | 隧道过渡 + 双态切换引擎 + ExecutionView CYBER 态 | 2-3天 |
| **Phase 6** | 打磨 + 无障碍 + 性能优化 + 暗色模式 | 2-3天 |
| **总计** | | **14-20天** |

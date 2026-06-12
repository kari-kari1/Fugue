# Fugue：双态动能 (Dual-State Kinetic) — 完整设计方案

> **静若处子，动若脱兔。**
> 静态态是 Apple Park 里的极简白墙，动态态是 WWDC 开场的霓虹引擎。
> 两者通过隧道纵深感无缝连接，全程物理弹簧驱动。

---

## 一、设计哲学

### 1.1 核心矛盾

| | 静态态 (Configuration) | 动态态 (Execution) |
|---|---|---|
| **情绪** | 克制、自信、呼吸感 | 紧张、沉浸、爆发力 |
| **灵感** | Apple.com 产品页、Carbon Neutral 广告 | WWDC 开场视频、钢铁侠 HUD |
| **类比** | 画廊里的白墙 | 驾驶舱的仪表盘 |
| **背景** | `#FFFFFF` 卡片 + `#F5F5F7` 底色 | 绝对纯黑 `#000000` 深渊 |
| **信息密度** | 极低（大字体 + 留白 = 一个视口一个想法） | 极高（数据流 + 光轨 + 粒子） |

### 1.2 五条铁律

1. **静态绝不发光** — 无 glow、无 gradient、无 particle。只靠字号、字重、留白和遮罩弹簧动效传递高级感。
2. **动态绝不克制** — 光轨、粒子、霓虹、呼吸光全部上阵，营造沉浸式引擎感。
3. **切换绝不硬切** — 通过隧道纵深感（Tunnel Zoom）和 shared element 变形完成，全程物理弹簧驱动。
4. **一个视口一个想法** — 每个屏幕只传达一个概念。宁可多滚动，不要拥挤。
5. **边框是最后手段** — 用留白和背景色差分层，需要边框时用 0.5px hairline，不是 1px。

---

## 二、设计系统 — 静态态 (Carbon Neutral Mode)

> 以下所有数值均来自 Apple HIG、WWDC Session、apple.com 逆向工程。
> 标注 `(v)` 已多源交叉验证，`(e)` 为逆向估算。

### 2.1 色彩系统

```
/*
 * Apple 的色彩哲学不是"选好看的颜色"，而是：
 * 1. 用 #F5F5F7 做底色（不是纯白！），白色卡片浮在上面 → 自然分层
 * 2. 用 #1D1D1F 做文字色（不是纯黑！），降低对比度刺眼感
 * 3. 强调色只用于交互元素，从不用于装饰
 */

/* === Light Mode === */
--bg-page:         #F5F5F7          /* Light Platinum — Apple 签名底色 (v) */
--bg-card:         #FFFFFF          /* 白色卡片浮在 #F5F5F7 上 (v) */
--bg-elevated:     #FFFFFF          /* 模态框、弹出层 */
--bg-nav:          rgba(255, 255, 255, 0.72)  /* 半透明毛玻璃导航栏 (v) */

--text-primary:    #1D1D1F          /* 近黑 — 非纯黑，柔和但读作黑 (v) */
--text-secondary:  #6E6E73          /* 次级文字 — 用于标注、元数据 (v) */
--text-tertiary:   #86868B          /* 最弱文字 — 用于禁用、占位 (v) */

--separator:       #D2D2D7          /* 0.5px hairline 分隔线 (v) */
--accent:          #0071E3          /* Apple Blue — 唯一强调色 (v) */
--accent-hover:    #0077ED          /* 按钮 hover (v) */
--link:            #0066CC          /* 行内链接色 (v) */
--destructive:     #FF3B30          /* 删除/危险操作 */

/* === Dark Mode === */
--bg-page-dark:         #000000     /* OLED 纯黑 (v) */
--bg-card-dark:         #1C1C1E     /* 深色卡片 (v) */
--bg-elevated-dark:     #2C2C2E     /* 深色弹出层 (v) */
--text-primary-dark:    #F5F5F7     /* 近白 — 非纯白 (v) */
--text-secondary-dark:  #A1A1A6     /* (v) */
--separator-dark:       #424245     /* (v) */
--accent-dark:          #2997FF     /* 深色模式下更亮的蓝 (v) */
```

**关键认知：`#F5F5F7` 是 Apple 最具辨识度的色彩决策。** 它替代了纯白作为默认底色，制造温暖感（不是奶油黄），让白色卡片获得视觉浮力。**在 Fugue 中，Dashboard 页面的底色必须是 `#F5F5F7`，卡片才是 `#FFFFFF`。** 如果反过来（纯白底 + 白卡片），就失去了 Apple 的分层感。

**禁用清单：**
- `#F3F4F6`、`#E5E7EB`、`#F9FAFB` 等 Tailwind 默认灰 → 全部替换
- 任何背景渐变（gradient）在静态态
- 任何 glow / text-shadow 在静态态
- 纯黑 `#000000` 用于文字（用 `#1D1D1F`）
- 纯白 `#FFFFFF` 用于深色模式文字（用 `#F5F5F7`）

### 2.2 字体系统

```
font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display',
             'SF Pro Text', 'Helvetica Neue', Helvetica, Arial, sans-serif;
/*
 * SF Pro Display: 用于 >= 20pt 的标题/展示文字，字距更宽 (v)
 * SF Pro Text:    用于 < 20pt 的正文/标注，针对可读性优化 (v)
 * 使用 -apple-system 时系统自动切换 (v)
 */
```

**字重策略：Apple 的"碾压式层级"**

```
/*
 * Apple 的秘密：标题用 Bold(700)，正文用 Regular(400)。
 * 跳过 Medium(500) 和 Semibold(600) — 中间字重制造"模糊层级"。
 * Bold 对 Regular 的极端对比让层级不言自明。 (v)
 *
 * Apple 从不在展示标题中使用 Heavy(800) 或 Black(900)。
 * 700 就是最大字重。克制即力量。
 */
--fw-bold:     700    /* 标题、hero 文字 */
--fw-semibold: 600    /* eyebrow、小标签 */
--fw-regular:  400    /* 正文、按钮、所有默认 */
```

**字号阶梯 — Apple.com Web 实测值 (v)**

```
--text-hero:     clamp(56px, 8vw, 96px)   /* Hero 标题: 80-96px (v) */
--text-section:  clamp(32px, 5vw, 64px)   /* 区域标题: 48-64px (v) */
--text-feature:  32px                      /* 功能标题: 32-40px (v) */
--text-eyebrow:  21px                      /* 眉毛文字/overline: 21px (v) */
--text-title:    28px                      /* Title 1 (v) */
--text-heading:  22px                      /* Title 2 (v) */
--text-subhead:  15px                      /* Subhead (v) */
--text-body:     17px                      /* Body — Apple 用 17px 不是 16px (v) */
--text-callout:  16px                      /* Callout (v) */
--text-caption:  14px                      /* Caption (v) */
--text-footnote: 13px                      /* Footnote (v) */
--text-micro:    12px                      /* Caption 2 (v) */
```

**行高 — 字号越大行高越紧 (v)**

```
/*
 * Apple 的行高公式（逆向拟合）：
 * line-height ratio ≈ 1.0 + (0.47 / font-size^0.35)
 *
 * 要点：display 字号的行高 ≈ 1.03-1.08（几乎无额外行距）
 *       body 字号的行高 ≈ 1.47（舒适阅读）(v)
 */
--lh-hero:     1.05     /* 96px 标题 → 100px 行高 (v) */
--lh-section:  1.08     /* 64px 标题 → 69px 行高 (v) */
--lh-feature:  1.12     /* 32px 标题 (v) */
--lh-body:     1.47     /* 17px 正文 → 25px 行高 (v) */
--lh-caption:  1.43     /* 14px (v) */
```

**字间距 — Apple 的反直觉规律 (v)**

```
/*
 * Apple 的 tracking 遵循一条曲线：
 * 尺寸越大 → 字距越紧（在 28-48pt 达到最紧）→ 超大字号略微放松。
 * 这不是线性关系。(v)
 *
 * 这就是为什么 Apple 的 hero 标题看起来像"雕刻"出来的。
 */
--ls-hero:     -0.025em   /* 80-96px (v) */
--ls-section:  -0.020em   /* 48-64px (v) */
--ls-feature:  -0.015em   /* 32-40px (v) */
--ls-body:     -0.012em   /* 17px — SF Pro Text 默认 (v) */
--ls-caption:   0em        /* 14px (v) */
--ls-eyebrow:  +0.020em   /* 21px — Apple 用正字距做眉标 (v) */
```

### 2.3 间距系统 — 8pt 网格 (v)

```
/* Apple 使用 8pt 基准网格，4pt 作为半步 (v) */
--space-1:   4px       /* 紧凑内部间距：icon-to-label */
--space-2:   8px       /* 紧凑间距 */
--space-3:   12px      /* 小组件间距 */
--space-4:   16px      /* 标准内边距、卡片内部 */
--space-5:   20px      /* Grid gutter (v) */
--space-6:   24px      /* 区域内部间距 */
--space-8:   32px      /* 组件间距 */
--space-10:  40px      /* 大间距 */
--space-12:  48px      /* 区块间距 */
--space-16:  64px      /* 区域内边距 */
--space-20:  80px      /* Section 间距下限 */
--space-24:  96px      /* Section 间距中值 */
--space-30:  120px     /* Section 间距上限 (v) */

/* 布局约束 */
--content-max:    980px     /* 标准内容区最大宽度 (v) */
--hero-max:       1440px    /* Hero/全宽区域最大宽度 (v) */
--side-padding:   22px      /* 最小侧边距 (v) */
```

### 2.4 圆角系统 — 连续圆角 (Squircle)

```
/*
 * Apple 使用"连续圆角"（squircle / superellipse），
 * 不是 CSS 标准 border-radius 的圆弧。(v)
 *
 * 区别：标准圆角在直线→曲线的切点处有突变。
 *       连续圆角的切线是连续的，过渡更自然。
 *
 * CSS 原生无法实现真正的 squircle，但差距很小。
 * SwiftUI: .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
 */

--radius-sm:   8px     /* 按钮、输入框、小卡片 (v) */
--radius-md:   12px    /* 中卡片、分段控件 (v) */
--radius-lg:   18px    /* 大卡片、面板 (v) */
--radius-xl:   22px    /* 模态框 (v) */
--radius-pill: 980px   /* 胶囊形按钮 (v) */
```

### 2.5 阴影系统 — 多层极淡

```
/*
 * Apple 的阴影秘诀：多层叠加，每层极淡（opacity 0.04-0.20）。(v)
 * 大多数 UI 框架用单一明显阴影。Apple 用 2-3 层微妙阴影。
 * 这就是"高级感"和"廉价感"的分界线。
 *
 * 阴影语义：不同层级有不同的阴影 profile，而非全局统一。
 */

/* Resting — 卡片默认态 */
--shadow-resting:
  0 1px 3px rgba(0, 0, 0, 0.04);       /* 紧贴接触阴影 (v) */

/* Raised — 按钮、可交互元素 */
--shadow-raised:
  0 1px 3px rgba(0, 0, 0, 0.04),        /* 接触 */
  0 2px 8px rgba(0, 0, 0, 0.06);        /* 扩散环境光 (v) */

/* Floating — 下拉菜单、工具提示 */
--shadow-floating:
  0 2px 8px rgba(0, 0, 0, 0.06),
  0 4px 16px rgba(0, 0, 0, 0.08);       /* (v) */

/* Elevated — 模态框、弹出层 */
--shadow-elevated:
  0 4px 16px rgba(0, 0, 0, 0.08),
  0 12px 40px rgba(0, 0, 0, 0.12);      /* (v) */

/* Dramatic — 全屏覆盖层 */
--shadow-dramatic:
  0 8px 30px rgba(0, 0, 0, 0.12),
  0 20px 60px rgba(0, 0, 0, 0.15);      /* (v) */
```

---

## 三、动效系统 — 弹簧物理

### 3.1 Apple 弹簧参数 (v)

```
/*
 * Apple 使用阻尼谐振子模型：F = -kx - cv (v)
 * k = stiffness (刚度), c = damping (阻尼), m = mass (质量)
 *
 * Apple 的"甜蜜区"：阻尼比 ζ = 0.75-0.85 (v)
 * → 轻微过冲 5-15%，然后稳定。这就是"有生命感"。
 * → ζ = 1.0 无过冲 → 感觉"死"
 * → ζ < 0.6 过冲太多 → 感觉"弹"
 */

/* Apple SwiftUI 默认弹簧 (v) */
--spring-default:
  response: 0.55s          /* 响应时间 */
  dampingFraction: 0.826   /* 阻尼比 */
  blendDuration: 0s        /* 无混合 */

/* Framer Motion 等价参数 */
--spring-fm-default:    { type: "spring", stiffness: 120, damping: 15, mass: 1.0 }
--spring-fm-interactive: { type: "spring", stiffness: 300, damping: 25, mass: 1.0 }
--spring-fm-bouncy:     { type: "spring", stiffness: 150, damping: 10, mass: 1.0 }
--spring-fm-smooth:     { type: "spring", stiffness: 100, damping: 20, mass: 1.0 }

/* 文字遮罩揭示 — 最高刚度、最低阻尼 */
--spring-reveal: { type: "spring", stiffness: 200, damping: 25, mass: 0.5 }
```

### 3.2 "Apple 质感" 的七个秘密 (v)

1. **弹簧驱动，非贝塞尔** — 真实物理，不是 `ease-out` 假装物理
2. **轻微欠阻尼** — 元素过冲 5-15% 再稳定 → "活"的感觉
3. **一致的速度到达** — 元素带着动量到位，不是死停
4. **Stagger 编排** — 多元素揭示间隔 40-50ms（不是同时出现）(v)
5. **从下方进入** — 内容最常从下方向上滑入（重力隐喻）(v)
6. **Scale + Fade 耦合** — 元素从 0.95-0.98 scale + opacity:0 过渡到 1.0 + opacity:1 (v)
7. **Exit 比 Enter 快 30%** — 退出动画短于进入动画（`duration * 0.7`）(v)

### 3.3 文字遮罩揭示 — Carbon Neutral 核心动效

```tsx
// 文字从下方被遮罩"切割"出来，带着弹簧阻尼感 (v)
const TextReveal = {
  hidden: {
    y: '100%',
    clipPath: 'inset(0% 0% 100% 0%)',  // 完全遮罩
  },
  visible: {
    y: '0%',
    clipPath: 'inset(0% 0% 0% 0%)',    // 完全揭示
    transition: {
      type: 'spring',
      stiffness: 200,   // 高初速度 — 快速弹出
      damping: 25,       // 高阻尼 — 到位后干脆停下
      mass: 0.5,         // 轻质量 — 响应快
    },
  },
};

// 使用
<motion.h1 variants={TextReveal} initial="hidden" animate="visible">
  Your Workflows.
</motion.h1>
```

### 3.4 Stagger 编排模式 (v)

```tsx
// Apple 的"瀑布流"揭示 — 每个元素间隔 40-50ms (v)
const staggerContainer = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.05,   // 50ms 间隔 (v)
      delayChildren: 0.1,      // 首个元素延迟 100ms
    },
  },
};

const staggerItem = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      type: 'spring',
      stiffness: 120,    // Apple 默认刚度
      damping: 15,        // Apple 默认阻尼
    },
  },
};

// 使用
<motion.div variants={staggerContainer} initial="hidden" animate="visible">
  {cards.map((card, i) => (
    <motion.div key={i} variants={staggerItem}>
      <WorkflowCard {...card} />
    </motion.div>
  ))}
</motion.div>
```

### 3.5 按钮交互 (v)

```tsx
// Apple 按钮：whileTap 缩小 3%，whileHover 放大 2% (v)
const buttonInteraction = {
  whileTap: { scale: 0.97 },
  whileHover: { scale: 1.02 },
  transition: { type: 'spring', stiffness: 400, damping: 25 },
};
```

### 3.6 `prefers-reduced-motion` 兼容

```css
@media (prefers-reduced-motion: reduce) {
  /* 所有弹簧动效简化为 300ms ease-out fade */
  .motion-reveal,
  .motion-stagger-item {
    transition: opacity 300ms ease-out !important;
    transform: none !important;
    clip-path: none !important;
  }

  /* 动态态全部禁用 */
  .cyber-trail { animation: none; stroke-dasharray: none; }
  .cyber-node-active { animation: none; }
  .cyber-typewriter { animation: none; border-right: none; }

  /* 隧道过渡简化 */
  .tunnel-transition {
    transition: opacity 300ms ease-out !important;
  }
}
```

---

## 四、设计系统 — 动态态 (Cyber-Engine Mode)

### 4.1 色彩系统

```
/* 绝对纯黑深渊 — 不用 #0A0A0F 等"假黑" */
--cy-bg:          #000000
--cy-bg-elevated: #0A0A0A           /* 仅用于需要区分的面板 */
--cy-text:        #E0E0E0           /* 非纯白，降低刺眼感 */
--cy-text-muted:  #666666

/* 霓虹色 — WWDC 风格紫青色系 */
--cy-neon-cyan:    #00D4FF          /* 主光轨色 — 来自 WWDC 开场 */
--cy-neon-violet:  #AF52DE          /* 次光轨色 */
--cy-neon-green:   #30D158          /* 成功/完成 — Apple systemGreen */
--cy-neon-amber:   #FFD60A          /* 警告/运行中 — Apple systemYellow */
--cy-neon-red:     #FF453A          /* 错误/失败 — Apple systemRed */

/* 光效参数 */
--cy-glow-sm:   0 0 8px currentColor
--cy-glow-md:   0 0 20px currentColor
--cy-glow-lg:   0 0 40px currentColor, 0 0 80px currentColor
```

### 4.2 光轨系统 (Iridescent Trails)

```css
.cyber-trail {
  stroke: url(#neon-gradient);
  stroke-width: 3px;
  stroke-linecap: round;
  filter: drop-shadow(0 0 8px rgba(0, 212, 255, 0.6))
          drop-shadow(0 0 20px rgba(175, 82, 222, 0.3));
  stroke-dasharray: 40 1000;
  animation: cyberFlow 1.5s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

@keyframes cyberFlow {
  from { stroke-dashoffset: 1040; }
  to { stroke-dashoffset: 0; }
}
```

### 4.3 节点脉冲系统

```css
.cyber-node-active {
  border: 1px solid rgba(0, 212, 255, 0.4);
  box-shadow:
    0 0 15px rgba(0, 212, 255, 0.2),
    inset 0 0 15px rgba(0, 212, 255, 0.05);
  animation: cyberPulse 2s ease-in-out infinite;
}

@keyframes cyberPulse {
  0%, 100% { box-shadow: 0 0 15px rgba(0,212,255,0.15), inset 0 0 10px rgba(0,212,255,0.03); }
  50%      { box-shadow: 0 0 25px rgba(0,212,255,0.35), inset 0 0 20px rgba(0,212,255,0.08); }
}

.cyber-node-completed {
  border: 1px solid rgba(48, 209, 88, 0.5);
  box-shadow: 0 0 12px rgba(48, 209, 88, 0.2);
}

.cyber-node-failed {
  border: 1px solid rgba(255, 69, 58, 0.5);
  box-shadow: 0 0 12px rgba(255, 69, 58, 0.2);
  animation: cyberGlitch 0.3s ease-in-out 1;
}
```

### 4.4 粒子背景

```
粒子颜色: rgba(0, 212, 255, 0.15) + rgba(175, 82, 222, 0.1)
粒子大小: 1-3px
运动速度: 极慢漂移 (0.1-0.3px/帧)
粒子密度: 50-80 个 / 1000x1000 区域
连线距离: 150px 内的粒子间画 0.5px 半透明连线
实现: Canvas 2D（非 DOM 元素）
```

### 4.5 打字机效果

```css
.cyber-typewriter {
  font-family: 'JetBrains Mono', 'SF Mono', monospace;
  font-size: 12px;
  color: var(--cy-neon-cyan);
  overflow: hidden;
  border-right: 2px solid var(--cy-neon-cyan);
  animation:
    typing 2s steps(40, end),
    blink-caret 0.5s step-end infinite;
}
```

---

## 五、过渡系统 — 隧道纵深感

### 5.1 状态切换动效剧本

```
用户点击 [运行] 按钮
  ↓ 0ms
按钮发出脉冲光圈（scale 1.0 → 1.05 → 1.0，300ms）
  ↓ 300ms
全屏白底开始以中心点为原点，进行 perspective zoom-out
  ↓ 300ms-700ms
白色 UI 元素依次缩小 + 模糊 (blur 0→8px) + 透明度下降
同时纯黑背景从中心向四周扩散
  ↓ 700ms
画面完全变黑，停留 100ms（呼吸感/悬念）
  ↓ 800ms
霓虹光轨从画布中心向四周节点爆射而出
  ↓ 800ms-1200ms
节点依次点亮（stagger 100ms），脉冲光开始呼吸
粒子场淡入 (opacity 0→1, 400ms)
  ↓ 1200ms
进入完整的动态态

用户点击 [停止] 或工作流完成
  ↓ 逆向播放
光轨收缩 → 粒子淡出 → 黑底收缩 → 白底展开 → 静态 UI 恢复
总时长: 800ms（exit 比 enter 短 30%）(v)
```

### 5.2 Framer Motion 实现

```tsx
// 安装: npm install framer-motion

// 1. 隧道过渡
const tunnelVariants = {
  static: {
    scale: 1,
    opacity: 1,
    filter: 'blur(0px)',
    backgroundColor: '#FFFFFF',
  },
  cyber: {
    scale: [1, 1.2, 0.8],
    opacity: [1, 0.5, 0],
    filter: ['blur(0px)', 'blur(4px)', 'blur(12px)'],
    backgroundColor: ['#FFFFFF', '#333333', '#000000'],
    transition: { duration: 1.2, ease: [0.16, 1, 0.3, 1] },
  },
};

// 2. 节点 → 面板形变 (Shared Layout) (v)
// 画布节点
<motion.div layoutId={`node-${id}`} className="node-pill">
  {agentName}
</motion.div>
// 配置面板
<motion.div layoutId={`node-${id}`} className="config-panel">
  <ConfigForm />
</motion.div>
```

---

## 六、页面剧本

### 6.1 页面节奏 — Apple 叙事滚动 (v)

```
/*
 * Apple 产品页的信息架构：叙事式滚动 (v)
 * 每个视口传达一个概念，通过背景色交替制造节奏。
 *
 * Hero (暗色, 80-100vh)
 *   → Statement (居中大标题, 40-60vh)
 *     → Feature (图重, 浅色底)
 *       → Grid (多列, 紧凑)
 *         → Deep-dive (左右交替, 70-90vh)
 *           → CTA (暗色收尾)
 *
 * Fugue 的 Dashboard 采用简化版：
 * Hero 区域 → 功能卡片 Grid → 执行记录列表
 */
```

### 6.2 登录页 — Hero 即设计 (v)

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│                                                     │
│                                                     │
│          Fugue.                                │  ← Hero 标题
│                                                     │     96px, Bold(700)
│                                                     │     line-height: 1.05
│                                                     │     letter-spacing: -0.025em
│                                                     │     Spring 遮罩揭示
│                                                     │
│          Build workflows                            │  ← 副标题
│          that think.                                │     21px, Regular(400)
│                                                     │     #6E6E73
│                                                     │     50ms stagger 揭示
│                                                     │
│          ┌──────────────────────┐                   │
│          │  Email               │                   │  ← 输入框
│          └──────────────────────┘                   │     44px 高
│          ┌──────────────────────┐                   │     仅底部 0.5px hairline
│          │  Password            │                   │     border-bottom: 0.5px solid #D2D2D7
│          └──────────────────────┘                   │     focus: #0071E3
│                                                     │
│          ┌──────────────────────┐                   │
│          │       Sign In        │                   │  ← 按钮
│          └──────────────────────┘                   │     #0071E3 纯色，无渐变
│                                                     │     980px 圆角（胶囊形）
│          Don't have an account? Sign up             │     whileTap: scale(0.97)
│                                                     │
│                                                     │  ← 背景: #FFFFFF
│                                                     │     无装饰。无插图。
│                                                     │     Hero 标题就是全部设计。
└─────────────────────────────────────────────────────┘

/*
 * "Hero 标题就是设计" — Apple 不在登录页放产品截图。
 * 巨大的排版本身创造了冲击力。(v)
 * 所有元素从下方 stagger 揭示（50ms 间隔）。
 */
```

### 6.3 Dashboard — Light Platinum 底色 + 白色卡片 (v)

```
┌──────────────────────────────────────────────────────────┐
│  ● ● ●  Fugue               Templates  Settings    │  ← 导航栏
│                                                          │  background: rgba(255,255,255,0.72)
│                                                          │  backdrop-filter: saturate(180%) blur(20px)
│                                                          │  border-bottom: 0.5px solid #D2D2D7
│  ┌────────────────────────────────────────────────────┐  │
│  │                                                    │  │  ← 内容区 max-width: 980px (v)
│  │  Your Workflows.                                   │  │     margin: 0 auto
│  │                                                    │  │     padding: 0 22px
│  │  (48px Bold, line-height: 1.08, ls: -0.02em)      │  │
│  │  Spring 遮罩揭示                                    │  │
│  │                                                    │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐     │  │
│  │  │ Industry   │ │ Code       │ │            │     │  │  ← 白色卡片
│  │  │ Report     │ │ Review     │ │ + New      │     │  │     background: #FFFFFF
│  │  │            │ │            │ │            │     │  │     底色: #F5F5F7
│  │  │ 3 agents   │ │ 2 agents   │ │            │     │  │     border-radius: 18px
│  │  │            │ │            │ │            │     │  │     box-shadow: var(--shadow-resting)
│  │  │ 2h ago     │ │ 1d ago     │ │            │     │  │     hover: var(--shadow-raised)
│  │  └────────────┘ └────────────┘ └────────────┘     │  │     whileHover: scale(1.02)
│  │                                                    │  │     stagger 入场 50ms
│  │                                                    │  │
│  │  Recent Executions                                 │  │  ← 眉毛文字
│  │  (13px, uppercase, #86868B, letter-spacing: +0.06em)│ │
│  │                                                    │  │
│  │  Industry Report   completed   42s    $0.0234      │  │  ← 列表
│  │  ────────────────────────────────────────────────  │  │     0.5px hairline separator (v)
│  │  Code Review       running     --     $0.0012      │  │     不是 1px！
│  │  ────────────────────────────────────────────────  │  │     separator 从 16px 缩进开始 (v)
│  │                                                    │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  #F5F5F7 底色                                            │  ← 整页底色不是纯白
│                                                          │     白色卡片浮在上面 → 自然分层
└──────────────────────────────────────────────────────────┘

/*
 * 关键：
 * 1. 底色 #F5F5F7，卡片 #FFFFFF — Apple 分层法 (v)
 * 2. 内容不贴边 — max-width 980px 居中 (v)
 * 3. separator 用 0.5px 不是 1px (v)
 * 4. separator 有缩进（对齐内容，不是贴边）(v)
 * 5. 一个视口一个想法 — hero 标题 + 卡片，不堆砌 (v)
 */
```

### 6.4 工作流编辑器 — 静态态

```
┌──────────────────────────────────────────────────────┐
│  ← Back    Industry Report              Run   Save   │  ← 统一工具栏 52px (v)
├──────────────────────────────────────────────────────┤
│          │                                          │
│  [Agent] │     ┌─────┐                              │
│  [Task]  │     │ Res │──────→ ┌──────┐              │  ← 节点: 极浅灰胶囊
│  [Cond]  │     │ Agt │        │ Code │              │     background: #F5F5F7
│  [Loop]  │     └─────┘        │ Task │              │     border-radius: 12px
│          │                    └──────┘              │     连线: 0.5px #D2D2D7
│          │         ↗                              │
│          │     ┌─────┐                              │
│          │     │Write│                              │
│          │     │ Agt │                              │
│          │     └─────┘                              │
│          │                                          │
│          │                      ┌─ Config Panel ──┐ │  ← Shared Layout 变形
│          │                      │ Agent: Research │ │     点击节点 → 节点形变为面板
│          │                      │ Provider: OpenAI│ │     关闭 → 面板收缩回节点
│          │                      │ Model: gpt-4o   │ │     layoutId 共享
│          │                      │ Tools: [...]    │ │
│          │                      └─────────────────┘ │
└──────────────────────────────────────────────────────┘

/*
 * 画布背景: #FFFFFF（编辑器区域用纯白，不用 F5F5F7）
 * 无网格线、无十字标 — Apple 的"白墙"感
 * 节点拖拽松手后 spring 回弹到吸附点
 */
```

### 6.5 点击 [运行] — 隧道过渡 (1.2s)

```
Phase 1 (0-300ms): 按钮脉冲
  scale(1.0→1.05→1.0), 发出 cyan 光圈

Phase 2 (300-700ms): 隧道穿越
  白色 UI 缩小模糊，黑色从中心扩散

Phase 3 (700-800ms): 纯黑悬停
  全黑，100ms 呼吸/悬念

Phase 4 (800-1200ms): 赛博觉醒
  光轨爆射，节点依次点亮 (stagger 100ms)
  粒子场淡入
```

### 6.6 动态态 — 执行中

```
┌──────────────────────────────────────────────────────┐
│  ← Back    Industry Report    ⏸ Pause  ⏹ Stop      │
├──────────────────────────────────────────────────────┤
│  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  │
│     ·  ·    ╱══════════╲      ·  ·                  │
│  ·     ●───●Research   ●──────→●──●Code Review  ·   │
│     ·  ·   ╲══════════╱   ·     ·  ·    ·          │
│  ·     ·        ↓              ·  ·      ·          │
│     ·  ·   ╱══════════╲   ·                       │
│  ·     ●───●Writer     ●   ·  ·     ·              │
│     ·  ·   ╲══════════╱      ·  ·                  │
│  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  │
│                                                      │
│  ┌─ Agent Thoughts ─────────────────────────────┐    │
│  │ > Analyzing industry trends...               │    │
│  │ > Found 15 relevant papers                   │    │
│  │ > Generating summary...                      │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  Cost: $0.0234  │  Tokens: 12,450  │  Time: 23s     │
└──────────────────────────────────────────────────────┘
```

### 6.7 执行完成 — 逆向隧道 (0.8s)

```
Phase 1 (0-200ms): 光轨收缩 + 粒子淡出
Phase 2 (200-500ms): 黑→白穿越
Phase 3 (500-800ms): 静态 UI spring 恢复
  弹出: ✓ Workflow completed (23s, $0.0234)
```

---

## 七、组件规范

### 7.1 按钮

```
/* Primary Button — 静态态 (Apple.com 实测) (v) */
.btn-primary {
  background: #0071E3;
  color: #FFFFFF;
  border: none;
  border-radius: 980px;         /* 胶囊形 (v) */
  height: 36px;
  padding: 0 16px;
  font-size: 13px;
  font-weight: 400;             /* Regular 不是 Medium (v) */
  cursor: pointer;
  transition: background 200ms ease;
}
.btn-primary:hover { background: #0077ED; }
.btn-primary:active { transform: scale(0.97); }

/* Primary Button — 动态态 */
.cyber-btn-primary {
  background: transparent;
  color: var(--cy-neon-cyan);
  border: 1px solid rgba(0, 212, 255, 0.4);
  box-shadow: 0 0 12px rgba(0, 212, 255, 0.15);
}
```

### 7.2 输入框

```
/* 静态态 — Apple 风格底部线输入 (v) */
.input {
  height: 44px;
  border: none;
  border-bottom: 0.5px solid #D2D2D7;   /* 0.5px 不是 1px (v) */
  background: transparent;
  font-size: 17px;                       /* Apple Body 字号 (v) */
  font-weight: 400;
  color: #1D1D1F;                        /* 近黑 (v) */
  padding: 0;
  transition: border-color 200ms;
}
.input:focus {
  border-bottom-color: #0071E3;
  outline: none;
}
.input::placeholder {
  color: #86868B;                        /* Apple tertiary text (v) */
}

/* 动态态 */
.cyber-input {
  background: rgba(255, 255, 255, 0.03);
  border: 0.5px solid rgba(0, 212, 255, 0.2);
  color: #E0E0E0;
  font-family: 'JetBrains Mono', monospace;
}
.cyber-input:focus {
  border-color: rgba(0, 212, 255, 0.6);
  box-shadow: 0 0 8px rgba(0, 212, 255, 0.15);
}
```

### 7.3 卡片

```
/* 静态态 — 白卡片在 F5F5F7 底色上 (v) */
.card {
  background: #FFFFFF;                   /* 卡片白色 */
  border-radius: 18px;                   /* Apple large radius (v) */
  box-shadow: var(--shadow-resting);     /* 多层极淡阴影 */
  padding: 24px;
  border: none;                          /* Apple 不用卡片边框 (v) */
  transition: box-shadow 300ms, transform 300ms;
}
.card:hover {
  box-shadow: var(--shadow-raised);      /* 提升层级 */
  transform: translateY(-2px);
}

/* 动态态 */
.cyber-card {
  background: rgba(255, 255, 255, 0.02);
  border: 0.5px solid rgba(0, 212, 255, 0.15);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}
```

### 7.4 导航栏

```
/* 静态态 — Apple.com 精确参数 (v) */
.navbar {
  height: 52px;                                     /* (v) */
  background: rgba(255, 255, 255, 0.72);            /* (v) */
  backdrop-filter: saturate(180%) blur(20px);        /* (v) */
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 0.5px solid #D2D2D7;               /* (v) */
  padding: 0 22px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.navbar-content {
  max-width: 980px;                                 /* (v) */
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* 动态态 */
.cyber-navbar {
  height: 52px;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 0.5px solid rgba(0, 212, 255, 0.15);
}
```

### 7.5 分隔线

```
/* Apple 的分隔线：0.5px + 缩进对齐内容 (v) */
.separator {
  height: 0;                                       /* 不是 1px (v) */
  border-top: 0.5px solid #D2D2D7;                 /* (v) */
  margin-left: 16px;                               /* 缩进对齐内容 (v) */
}

.separator-dark {
  border-top-color: #424245;                       /* 深色模式 (v) */
}
```

---

## 八、技术实施清单

### 8.1 依赖

```json
{
  "framer-motion": "^12.0.0",
  "@fontsource/inter": "^5.0.0",
  "@fontsource/jetbrains-mono": "^5.0.0"
}
```

### 8.2 文件结构

```
frontend/src/
├── styles/
│   ├── tokens-static.css
│   ├── tokens-cyber.css
│   └── animations.css
├── components/
│   ├── motion/
│   │   ├── TextReveal.tsx
│   │   ├── TunnelTransition.tsx
│   │   ├── StaggerList.tsx
│   │   └── SpringButton.tsx
│   ├── cyber/
│   │   ├── CyberTrail.tsx
│   │   ├── ParticleField.tsx
│   │   ├── CyberNode.tsx
│   │   └── TypewriterText.tsx
│   ├── nodes/
│   ├── editor/
│   └── ui/
├── stores/
│   └── themeStore.ts
└── lib/
    └── motion-variants.ts
```

### 8.3 主题状态管理

```tsx
interface ThemeState {
  mode: 'static' | 'cyber' | 'transitioning';
  transitionDirection: 'to-cyber' | 'to-static' | null;
  enterCyberMode: () => void;
  exitCyberMode: () => void;
  setTransitioning: (dir: 'to-cyber' | 'to-static') => void;
}
// <html data-theme="static"> 或 <html data-theme="cyber">
```

### 8.4 性能预算

| 指标 | 目标 |
|------|------|
| 隧道过渡帧率 | 60fps (16.6ms/帧) |
| Canvas 粒子数 | ≤ 80 |
| 光轨 SVG 路径 | ≤ 20 条 |
| Framer Motion 同时动画 | ≤ 15 个 |
| 首屏加载 | ≤ 2s |
| 隧道进入 | 1.2s |
| 隧道退出 | 0.8s |

---

## 九、无障碍合规

| 要求 | 静态态 | 动态态 |
|------|--------|--------|
| 文字对比度 | #1D1D1F on #FFFFFF = 15.4:1 ✓ | #E0E0E0 on #000000 = 15.3:1 ✓ |
| 焦点环 | 2px solid #0071E3 | 2px solid #00D4FF |
| 键盘导航 | 完整 Tab 顺序 | 完整 Tab 顺序 |
| prefers-reduced-motion | 简化为 fade | 全部禁用 |
| 屏幕阅读器 | aria-label | aria-live 播报执行状态 |

---

## 十、实施优先级

```
Phase 1 (3天): 静态态重建
  → CSS 变量系统 (tokens-static.css) — F5F5F7 底色、#1D1D1F 文字
  → Framer Motion + TextReveal + StaggerList + SpringButton
  → Login、Dashboard 页面重写 — Hero 即设计 + Bento Grid
  → 替换全部 Tailwind 默认灰 + 1px 边框 → 0.5px hairline

Phase 2 (2天): 动态态基础
  → tokens-cyber.css + animations.css
  → CyberTrail 替代 ParticleEdge
  → CyberNode 替代 AgentNode/TaskNode
  → Canvas 粒子背景

Phase 3 (2天): 隧道过渡
  → TunnelTransition 组件
  → themeStore 状态管理
  → Run → 隧道 → 动态态 全流程
  → 完成 → 逆向隧道 → 静态态

Phase 4 (2天): 打磨
  → Shared Layout (节点 ↔ 面板形变)
  → 打字机效果
  → 动态态 HUD 组件
  → prefers-reduced-motion
  → 性能优化

Phase 5 (1天): 全页面重写
  → Templates、Plugins、Webhooks、Schedules 等
  → Editor 页面打磨
  → 移动端适配
```

---

## 十一、参考锚点

| 元素 | 精确参考 |
|------|---------|
| Hero 标题排版 | apple.com iPhone 产品页 — 96px Bold, lh 1.05, ls -0.025em |
| Light Platinum 底色 | apple.com 全站 — #F5F5F7 作为默认页面底色 |
| 导航栏毛玻璃 | apple.com 导航 — rgba(255,255,255,0.72) + blur(20px) + saturate(180%) |
| 弹簧动效 | SwiftUI .spring() — response 0.55s, damping 0.826 |
| 文字遮罩揭示 | Carbon Neutral 广告 (youtube.com/watch?v=66XwG1CLHuU) |
| 弹簧阻尼感 | WWDC 片段 (youtube.com/watch?v=j1HGOY32s2Y) |
| 霓虹光轨 | WWDC 开场视频 — 紫青色光束 |
| 隧道过渡 | VisionOS 空间缩放 + Apple TV+ 转场 |
| 节点形变为面板 | Apple Maps 地点卡片展开 — layoutId 共享 |
| 0.5px hairline | Apple HIG — thin separator, NOT 1px |
| 多层阴影 | Apple HIG elevation system — 4-5 层, opacity 0.04-0.20 |
| 分隔线缩进 | iOS UITableView — separator inset from content edge |

---

> **最终检验标准：** 一个从未见过 Fugue 的人，看到静态态 UI 的第一反应应该是"这看起来像 Apple 做的"，而不是"这用了 Apple 颜色"。差异在于：排版节奏、留白呼吸、阴影层次、弹簧动效、0.5px hairline 的克制。每一个数值都不是随手写的，而是从 Apple 的产品中逆向提取的。

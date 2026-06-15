/**
 * Minimal i18n — tutorial/onboarding text translation.
 *
 * Usage:
 *   import { t, setLang, getLang } from '../lib/i18n';
 *   t('common.next_step')              // "下一步 →"
 *   t('common.step_counter', { current: 1, total: 7 })  // "1/7"
 */

type Translations = Record<string, string | Record<string, any>>;

// ─── English ─────────────────────────────────────────────────────────────────

const en: Translations = {
  common: {
    close_tutorial: 'Close tutorial',
    next_step: 'Next →',
    prev_step: '← Back',
    complete_tutorial: 'Finish tutorial',
    skip: 'Skip →',
    start_using: 'Start using',
    saving: 'Saving...',
    selected: 'Selected',
    agents_count: '{count} agents',
    tasks_count: '{count} tasks',
    step_counter: '{current}/{total}',
    tutorial_label: 'Tutorial',
    multi_select_hint: '(Multi-select available)',
    back: 'Back',
    refresh: 'Refresh',
    cancel: 'Cancel',
    confirm: 'Confirm',
    delete: 'Delete',
    edit: 'Edit',
    create: 'Create',
    search: 'Search',
    loading: 'Loading...',
    no_data: 'No data',
    save: 'Save',
    close: 'Close',
    submit: 'Submit',
    settings: 'Settings',
    switch_language: 'Switch Language',
    nav_templates: 'Templates',
    nav_plugins: 'Plugins',
    nav_mcp_tools: 'MCP Tools',
    nav_knowledge: 'Knowledge Bases',
    nav_settings: 'Settings',
    nav_webhooks: 'Webhooks',
    nav_schedules: 'Schedules',
    nav_api_publish: 'API Publish',
  },

  dashboard: {
    title: 'My Workflows',
    subtitle: 'Create and manage multi-agent workflows',
    new_workflow: 'New',
    total_runs: 'Total Runs',
    completed: 'Completed',
    success_rate: 'Success Rate',
    total_tokens: 'Total Tokens',
    edit_workflow: 'Edit workflow',
    delete_workflow: 'Delete workflow',
    run: 'Run',
    delete_confirm: 'Are you sure you want to delete "{name}"?',
    no_workflows: 'No workflows yet',
    no_workflows_desc: 'Click "New" to create your first workflow',
    agents: 'agents',
    tasks: 'tasks',
  },

  login: {
    title: 'Sign in to Fugue',
    email: 'Email',
    password: 'Password',
    sign_in: 'Sign In',
    no_account: "Don't have an account?",
    register: 'Register',
    forgot_password: 'Forgot password?',
  },

  register: {
    title: 'Create Account',
    username: 'Username',
    email: 'Email',
    password: 'Password',
    confirm_password: 'Confirm Password',
    sign_up: 'Sign Up',
    has_account: 'Already have an account?',
    sign_in: 'Sign In',
  },

  knowledge: {
    title: 'Knowledge Bases',
    subtitle: 'Upload documents to build knowledge bases for agents',
    create: 'Create Knowledge Base',
    name: 'Name',
    description: 'Description',
    search_placeholder: 'Search knowledge base content...',
    no_results: 'No results found',
    upload: 'Upload Document',
    vector_store_ok: 'Vector store running',
    vector_store_unavailable: 'ChromaDB not installed, using SQLite full-text search (functional, lower precision)',
  },

  templates: {
    title: 'Template Marketplace',
    search_placeholder: 'Search templates...',
    no_match: 'No matching templates found',
    use_template: 'Use Template',
    importing: 'Importing...',
  },

  plugins: {
    title: 'Plugin Management',
    subtitle: 'Manage installed plugins and tools to extend Fugue\'s capabilities',
    tab_plugins: 'Plugins',
    tab_tools: 'Tools',
    health_check: 'Health Check',
    reload: 'Reload',
    no_plugins: 'No plugins',
    no_plugins_desc: 'No plugins loaded yet. Plugins can extend Fugue\'s capabilities.',
    no_tools: 'No tools',
    no_tools_desc: 'No tools available. Install plugins to auto-register tools.',
    test: 'Test',
    testing: 'Testing...',
  },

  settings: {
    title: 'Settings',
    api_keys: 'API Keys',
    provider: 'Provider',
    api_key: 'API Key',
    save_keys: 'Save Keys',
    language: 'Language',
    chinese: 'Chinese',
    english: 'English',
  },

  tutorial: {
    tip_0: {
      title: 'Workflow list (1/7)',
      content: 'All your created workflows are shown here. Click "New" to create your first one.',
    },
    tip_1: {
      title: 'Create workflow (2/7)',
      content: 'Click this button to create a new multi-agent workflow. You can start from a template.',
    },
    tip_2: {
      title: 'Template library (3/7)',
      content: 'Browse preset templates and import them with one click to get started.',
    },
    tip_3: {
      title: 'Set API Key (4/7)',
      content: 'Configure your LLM Provider API Key in the settings page so agents can work properly.',
    },
    tip_4: {
      title: 'Knowledge bases (5/7)',
      content: 'Upload documents to build knowledge bases that agents can search to enhance response quality.',
    },
    tip_5: {
      title: 'MCP Tool Market (6/7)',
      content: 'Connect external MCP servers to extend agent capabilities, such as filesystem, GitHub, etc.',
    },
    tip_6: {
      title: 'Execution Monitor (7/7)',
      content: 'Watch agent execution in real time, including thought chains, tool calls, and task progress.',
    },
  },

  onboarding: {
    steps: {
      0: { title: 'Choose Scenario', desc: 'Tell us what you want to accomplish' },
      1: { title: 'Import Template', desc: 'Quick start from preset templates' },
      2: { title: 'Configure LLM', desc: 'Set up your AI model API Key' },
      3: { title: 'Create Agent', desc: 'Configure your first agent' },
      4: { title: 'Run Workflow', desc: 'Execute and observe results' },
      5: { title: 'View Results', desc: 'Learn how to optimize output' },
      6: { title: 'Preferences', desc: 'Customize your experience' },
    },

    scenarios: {
      research: { title: 'Research', desc: 'Multi-source search, summary analysis, report generation' },
      coding: { title: 'Coding', desc: 'Requirements analysis, code generation, test validation' },
      writing: { title: 'Writing', desc: 'Outline planning, draft generation, polish optimization' },
      data: { title: 'Data Processing', desc: 'Data cleaning, statistical analysis, visualization' },
      custom: { title: 'Custom', desc: 'Build workflows from scratch' },
    },

    templates: {
      research: {
        0: 'Deep Research Assistant',
        1: 'Competitive Analysis Workflow',
      },
      coding: {
        0: 'Full-stack Dev Assistant',
        1: 'Code Review Workflow',
      },
      writing: {
        0: 'Blog Writing Assistant',
        1: 'Tech Doc Generator',
      },
      data: {
        0: 'Data Analysis Pipeline',
        1: 'Report Generation Assistant',
      },
    },

    step1: {
      heading: 'What do you want to do with Fugue?',
      subheading: 'Choose the closest scenario and we will recommend suitable templates and configurations.',
    },
    step2: {
      heading: 'Choose a starter template',
      subheading: 'Start from a preset template, or build from scratch later in the editor.',
      custom_mode_title: 'You chose custom mode',
      custom_mode_desc: 'You can browse and import templates later in the template library',
      skip_later: 'Skip for now',
    },
    step3: {
      heading: 'Configure AI Model',
      subheading: "Enter your API Key to enable LLM capabilities. Keys are stored locally only.",
      select_provider: 'Select Provider',
      api_key_label: 'API Key',
      key_local_notice: 'Keys are only stored in browser local storage and will never be uploaded to any server.',
      skip_later: 'Skip, configure later',
    },
    step4: {
      heading: 'Create your first agent',
      subheading: 'Give your agent a name. You can configure roles and capabilities in detail later in the editor.',
      agent_name_label: 'Agent name',
      agent_name_placeholder: 'e.g.: Research Assistant, Code Reviewer, Copywriter...',
      tips_title: 'Tips',
      tip1: 'The name should reflect the role of the agent',
      tip2: 'You can create multiple agents to collaborate on complex tasks',
      tip3: 'You can modify role prompts and tool configurations later in the visual editor',
    },
    step5: {
      heading: 'Ready to go!',
      subheading: 'After clicking "Start using", the system will auto-create a sample workflow and guide you through your first run.',
      item1_title: 'Create workflow',
      item1_desc: 'The system will auto-create a workflow based on your selections',
      item2_title: 'Run execution',
      item2_desc: 'Observe the agent\'s real-time thinking and tool calls on the execution page',
      item3_title: 'Iterative optimization',
      item3_desc: 'Use the iteration feature to continuously optimize output based on result feedback',
      tutorial_banner: 'Tutorial mode is ON — after entering the main interface, key areas will show guided tips. You can turn it off anytime in settings.',
    },
    step6: {
      heading: 'All set!',
      subheading: "You've completed the basic configuration. Next you can create workflows in the visual editor or pick ready-made solutions from the template library.",
      card1_title: 'Visual Editor',
      card1_desc: 'Drag-and-drop workflow creation',
      card2_title: 'Template Library',
      card2_desc: 'Browse community templates',
      card3_title: 'MCP Tools',
      card3_desc: 'Connect external tools',
      card4_title: 'Documentation',
      card4_desc: 'View usage guide',
    },
    step7: {
      heading: 'Preferences',
      subheading: 'Adjust your experience according to your preferences. These settings can be changed anytime on the settings page.',
      guided_tips_label: 'Guided tips',
      guided_tips_desc: 'Show interactive hints on the interface',
      dark_theme_label: 'Dark theme',
      dark_theme_desc: 'Use dark interface (can follow system preference)',
      notifications_label: 'Notifications',
      notifications_desc: 'Send notifications when execution completes',
    },

    tutorial_mode_label: 'Tutorial mode',
    crew_workflow_name: '{name}\'s workflow',
    first_workflow_name: 'My first workflow',
    first_workflow_desc: 'Created via onboarding - {scenario} scenario',
    first_agent_name: 'Research Assistant',
    first_agent_role: 'You are a professional AI assistant',
    first_agent_goal: 'Help users accomplish tasks',
    first_agent_backstory: 'An experienced agent',
    first_task_name: 'Initial Task',
    first_task_desc: 'Analyze the {scenario} domain and provide a structured report.',
    first_task_output: 'A comprehensive analysis report with key findings and recommendations.',
    config_saved: 'Configuration saved! Welcome to Fugue',
    config_save_failed: 'Failed to save configuration',
    skip_toast: 'You can reconfigure anytime in settings',
  },
};

// ─── Chinese ─────────────────────────────────────────────────────────────────

const zh: Translations = {
  common: {
    close_tutorial: '关闭教程',
    next_step: '下一步 →',
    prev_step: '← 上一步',
    complete_tutorial: '完成教程',
    skip: '跳过 →',
    start_using: '开始使用',
    saving: '保存中...',
    selected: '已选',
    agents_count: '{count} 个智能体',
    tasks_count: '{count} 个任务',
    step_counter: '{current}/{total}',
    tutorial_label: '教程',
    multi_select_hint: '（可多选）',
    back: '返回',
    refresh: '刷新',
    cancel: '取消',
    confirm: '确认',
    delete: '删除',
    edit: '编辑',
    create: '创建',
    search: '搜索',
    loading: '加载中...',
    no_data: '暂无数据',
    save: '保存',
    close: '关闭',
    submit: '提交',
    settings: '设置',
    switch_language: '切换语言',
    nav_templates: '模板市场',
    nav_plugins: '插件管理',
    nav_mcp_tools: 'MCP 工具',
    nav_knowledge: '知识库',
    nav_settings: '设置',
    nav_webhooks: 'Webhooks',
    nav_schedules: '定时任务',
    nav_api_publish: 'API 发布',
  },

  dashboard: {
    title: '我的工作流',
    subtitle: '创建和管理多智能体工作流',
    new_workflow: '新建',
    total_runs: '总运行次数',
    completed: '已完成',
    success_rate: '成功率',
    total_tokens: '总 Token 数',
    edit_workflow: '编辑工作流',
    delete_workflow: '删除工作流',
    run: '运行',
    delete_confirm: '确定要删除「{name}」吗？',
    no_workflows: '暂无工作流',
    no_workflows_desc: '点击「新建」创建您的第一个工作流',
    agents: '个智能体',
    tasks: '个任务',
  },

  login: {
    title: '登录 Fugue',
    email: '邮箱',
    password: '密码',
    sign_in: '登录',
    no_account: '还没有账号？',
    register: '注册',
    forgot_password: '忘记密码？',
  },

  register: {
    title: '创建账号',
    username: '用户名',
    email: '邮箱',
    password: '密码',
    confirm_password: '确认密码',
    sign_up: '注册',
    has_account: '已有账号？',
    sign_in: '登录',
  },

  knowledge: {
    title: '知识库',
    subtitle: '上传文档构建知识库，供智能体检索',
    create: '创建知识库',
    name: '名称',
    description: '描述',
    search_placeholder: '搜索知识库内容...',
    no_results: '未找到结果',
    upload: '上传文档',
    vector_store_ok: '向量存储正常运行',
    vector_store_unavailable: 'ChromaDB 未安装，知识库搜索使用 SQLite 全文查询（功能可用，精度较低）',
  },

  templates: {
    title: '模板市场',
    search_placeholder: '搜索模板...',
    no_match: '没有找到匹配的模板',
    use_template: '使用模板',
    importing: '导入中...',
  },

  plugins: {
    title: '插件管理',
    subtitle: '管理已安装的插件和工具，扩展 Fugue 的功能',
    tab_plugins: '插件',
    tab_tools: '工具',
    health_check: '健康检查',
    reload: '重载',
    no_plugins: '暂无插件',
    no_plugins_desc: '还没有加载任何插件。插件可以扩展 Fugue 的功能。',
    no_tools: '暂无工具',
    no_tools_desc: '还没有可用的工具。安装插件后会自动注册工具。',
    test: '测试',
    testing: '测试中...',
  },

  settings: {
    title: '设置',
    api_keys: 'API 密钥',
    provider: '提供商',
    api_key: 'API Key',
    save_keys: '保存密钥',
    language: '语言',
    chinese: '中文',
    english: '英文',
  },

  tutorial: {
    tip_0: {
      title: '工作流列表 (1/7)',
      content: '这里展示您创建的所有工作流。点击"新建"开始第一个。',
    },
    tip_1: {
      title: '创建工作流 (2/7)',
      content: '点击此按钮创建新的多智能体工作流。可以先从模板开始。',
    },
    tip_2: {
      title: '模板库 (3/7)',
      content: '浏览预设模板，一键导入即可开始使用。',
    },
    tip_3: {
      title: '设置 API Key (4/7)',
      content: '在设置页面配置您的 LLM Provider API Key，智能体才能正常工作。',
    },
    tip_4: {
      title: '知识库 (5/7)',
      content: '上传文档构建知识库，Agent 可检索其中的信息来增强回答质量。',
    },
    tip_5: {
      title: 'MCP 工具市场 (6/7)',
      content: '连接外部 MCP 服务器扩展 Agent 的工具能力，如文件系统、GitHub 等。',
    },
    tip_6: {
      title: '执行监控 (7/7)',
      content: '实时查看 Agent 执行过程，包括思考链、工具调用和任务进度。',
    },
  },

  onboarding: {
    steps: {
      0: { title: '选择场景', desc: '告诉我们您的使用目标' },
      1: { title: '导入模板', desc: '从预设模板快速开始' },
      2: { title: '配置LLM', desc: '设置AI模型API Key' },
      3: { title: '创建Agent', desc: '配置您的第一个智能体' },
      4: { title: '运行工作流', desc: '执行并观察结果' },
      5: { title: '查看结果', desc: '了解如何优化输出' },
      6: { title: '个性化设置', desc: '定制您的使用偏好' },
    },

    scenarios: {
      research: { title: '信息调研', desc: '多源搜索、汇总分析、生成报告' },
      coding: { title: '代码开发', desc: '需求分析、代码生成、测试验证' },
      writing: { title: '内容创作', desc: '大纲规划、初稿生成、润色优化' },
      data: { title: '数据处理', desc: '数据清洗、统计分析、可视化' },
      custom: { title: '自定义', desc: '从零开始构建工作流' },
    },

    templates: {
      research: {
        0: '深度调研助手',
        1: '竞品分析工作流',
      },
      coding: {
        0: '全栈开发助手',
        1: '代码审查工作流',
      },
      writing: {
        0: '博客写作助手',
        1: '技术文档生成器',
      },
      data: {
        0: '数据分析流水线',
        1: '报表生成助手',
      },
    },

    step1: {
      heading: '您想用 Fugue 做什么？',
      subheading: '选择最接近的使用场景，我们会推荐合适的模板和配置。',
    },
    step2: {
      heading: '选择起始模板',
      subheading: '从预设模板开始，或者稍后在编辑器中从零构建。',
      custom_mode_title: '您选择了自定义模式',
      custom_mode_desc: '稍后可在模板库中浏览和导入',
      skip_later: '跳过，稍后选择',
    },
    step3: {
      heading: '配置 AI 模型',
      subheading: '输入您的 API Key 以启用 LLM 能力。密钥仅存储在本地。',
      select_provider: '选择 Provider',
      api_key_label: 'API Key',
      key_local_notice: '密钥仅保存在浏览器本地存储中，不会上传到任何服务器。',
      skip_later: '跳过，稍后配置',
    },
    step4: {
      heading: '创建您的第一个智能体',
      subheading: '给智能体起个名字，后续可在编辑器中详细配置角色和能力。',
      agent_name_label: '智能体名称',
      agent_name_placeholder: '例如: 研究助手、代码审查员、文案策划...',
      tips_title: '提示',
      tip1: '名称应体现智能体的角色定位',
      tip2: '可以创建多个智能体协作完成复杂任务',
      tip3: '后续可在可视化编辑器中修改角色提示词和工具配置',
    },
    step5: {
      heading: '准备就绪！',
      subheading: '点击"开始使用"后，系统将自动创建示例工作流并引导您首次运行。',
      item1_title: '创建工作流',
      item1_desc: '系统将根据您的选择自动创建工作流',
      item2_title: '运行执行',
      item2_desc: '在执行页面观察智能体的实时思考和工具调用',
      item3_title: '迭代优化',
      item3_desc: '根据结果反馈，使用迭代功能持续优化输出',
      tutorial_banner: '新手教程模式已开启 — 进入主界面后，关键操作区域会显示引导提示。您可以随时在设置中关闭。',
    },
    step6: {
      heading: '一切就绪！',
      subheading: '您已完成基础配置。接下来可以在可视化编辑器中创建工作流，或从模板库中选择现成方案。',
      card1_title: '可视化编辑器',
      card1_desc: '拖拽式创建工作流',
      card2_title: '模板库',
      card2_desc: '浏览社区模板',
      card3_title: 'MCP 工具',
      card3_desc: '连接外部工具',
      card4_title: '文档',
      card4_desc: '查看使用指南',
    },
    step7: {
      heading: '个性化设置',
      subheading: '根据您的偏好调整使用体验。这些设置可随时在设置页面更改。',
      guided_tips_label: '新手引导',
      guided_tips_desc: '在界面上显示交互式提示',
      dark_theme_label: '暗色主题',
      dark_theme_desc: '使用深色界面（可随系统切换）',
      notifications_label: '通知偏好',
      notifications_desc: '执行完成时发送通知',
    },

    tutorial_mode_label: '新手教程模式',
    crew_workflow_name: '{name}的工作流',
    first_workflow_name: '我的第一个工作流',
    first_workflow_desc: '通过新手教程创建 - {scenario}场景',
    first_agent_name: '研究助手',
    first_agent_role: '你是一个专业的AI助手',
    first_agent_goal: '帮助用户完成任务',
    first_agent_backstory: '一个经验丰富的智能体',
    first_task_name: '初始任务',
    first_task_desc: '分析{scenario}领域并生成结构化报告。',
    first_task_output: '包含关键发现和建议的综合分析报告。',
    config_saved: '配置完成！欢迎使用 Fugue',
    config_save_failed: '保存配置失败',
    skip_toast: '您可以随时在设置中重新配置',
  },
};

// ─── Engine ──────────────────────────────────────────────────────────────────

const packs: Record<string, Translations> = { zh, en };

/**
 * Get current language code. Defaults to 'zh'.
 */
export function getLang(): string {
  return localStorage.getItem('lang') || 'zh';
}

/**
 * Set current language and persist to localStorage.
 */
export function setLang(lang: string): void {
  localStorage.setItem('lang', lang);
}

/**
 * Translate a dot-separated key path into a string for the current language.
 * Supports {variable} interpolation.
 *
 * @example
 *   t('tutorial.tip_0.title')                        // "工作流列表 (1/7)"
 *   t('common.step_counter', { current: 1, total: 7 }) // "1/7"
 */
export function t(key: string, vars?: Record<string, string | number>): string {
  const lang = getLang();
  const pack = packs[lang] || packs.zh;

  const parts = key.split('.');
  let value: any = pack;
  for (const part of parts) {
    if (value == null || typeof value !== 'object') break;
    value = value[part];
  }

  if (typeof value !== 'string') {
    console.warn(`Missing i18n key: "${key}" (lang=${lang})`);
    return key;
  }

  if (vars) {
    return value.replace(/\{(\w+)\}/g, (_, k: string) => String(vars[k] ?? ''));
  }

  return value;
}

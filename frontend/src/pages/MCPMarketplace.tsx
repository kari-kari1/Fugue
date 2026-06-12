import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { apiClient } from '../api/client';
import { Activity, Terminal, Plug, Shield, Wrench } from 'lucide-react';

interface MCPPreset {
  id: string;
  name: string;
  description: string;
  category: string;
  command: string;
  args: string[];
  env: Record<string, string>;
  tools_count: number;
  star_count: number;
  verified: boolean;
  homepage: string;
  setup_instructions: string;
}

interface Category {
  id: string;
  name: string;
  count: number;
}

const CATEGORY_ICONS: Record<string, string> = {
  file: '📁',
  development: '💻',
  search: '🔍',
  database: '🗄️',
  communication: '💬',
  automation: '🤖',
  ai: '🧠',
  general: '⚙️',
};

export default function MCPMarketplace() {
  const navigate = useNavigate();
  const [presets, setPresets] = useState<MCPPreset[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedPreset, setSelectedPreset] = useState<MCPPreset | null>(null);
  const [activeTab, setActiveTab] = useState<'marketplace' | 'server'>('marketplace');

  useEffect(() => {
    loadData();
  }, [selectedCategory, searchQuery]);

  const loadData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedCategory) params.append('category', selectedCategory);
      if (searchQuery) params.append('search', searchQuery);

      // D2+D6: 使用 apiClient 统一请求（自动携带 Auth Token）
      const [presetsRes, categoriesRes] = await Promise.all([
        apiClient.get(`/mcp/marketplace/presets?${params}`),
        apiClient.get('/mcp/marketplace/categories'),
      ]);

      setPresets(presetsRes.data.presets);
      setCategories(categoriesRes.data.categories);
    } catch (error) {
      console.error('Failed to load MCP presets:', error);
      toast.error('加载MCP工具失败');
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (preset: MCPPreset) => {
    // 检查是否有需要配置的环境变量
    const hasEnvVars = Object.values(preset.env).some(v => v.startsWith('<') && v.endsWith('>'));

    if (hasEnvVars) {
      setSelectedPreset(preset);
      return;
    }

    try {
      const result = (await apiClient.post('/mcp/connect', {
          server_id: preset.id,
          command: preset.command,
          args: preset.args,
          env: preset.env,
        })).data;

      const response = { ok: true };

      if (response.ok) {
        toast.success(`已连接 ${preset.name}，发现 ${result.tools_count} 个工具`);
      } else {
        toast.error(`连接失败: ${result.detail}`);
      }
    } catch (error) {
      toast.error(`连接失败: ${error}`);
    }
  };

  return (
    <div className="min-h-screen p-6" style={{ background: 'var(--bg-page)' }}>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-4 mb-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
          >
            ← 返回
          </button>
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900">MCP</h1>
            <p className="mt-2 text-gray-600">
              一键安装MCP Server，扩展Agent能力
            </p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-gray-100 rounded-xl p-1 max-w-md">
          {[
            { key: 'marketplace' as const, label: '工具市场', icon: <Plug className="w-4 h-4" /> },
            { key: 'server' as const, label: '本机 Server', icon: <Activity className="w-4 h-4" /> },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all flex-1 justify-center ${
                activeTab === tab.key
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search — only in marketplace tab */}
        {activeTab === 'marketplace' && (
          <div className="max-w-xl mt-4">
            <input
              type="text"
              placeholder="搜索MCP工具..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        )}
      </div>

      {/* Server Tab */}
      {activeTab === 'server' && <MCPServerPanel />}

      {/* Marketplace Tab */}
      {activeTab === 'marketplace' && (<>
      <div className="flex gap-6">
        {/* Sidebar - Categories */}
        <div className="w-48 flex-shrink-0">
          <div className="bg-white rounded-xl border border-gray-200 p-4 sticky top-6">
            <h3 className="font-semibold text-gray-900 mb-3">分类</h3>
            <div className="space-y-2">
              <button
                onClick={() => setSelectedCategory(null)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                  !selectedCategory
                    ? 'bg-blue-100 text-blue-700'
                    : 'hover:bg-gray-100 text-gray-700'
                }`}
              >
                全部
              </button>
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex items-center justify-between ${
                    selectedCategory === cat.id
                      ? 'bg-blue-100 text-blue-700'
                      : 'hover:bg-gray-100 text-gray-700'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <span>{CATEGORY_ICONS[cat.id] || '📦'}</span>
                    {cat.name}
                  </span>
                  <span className="text-xs text-gray-500">{cat.count}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Main Content - Presets Grid */}
        <div className="flex-1">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : presets.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
              <div className="text-6xl mb-4">🔍</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">未找到工具</h3>
              <p className="text-gray-600">尝试其他搜索关键词或分类</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {presets.map((preset) => (
                <div
                  key={preset.id}
                  className="bg-white rounded-xl border border-gray-200 hover:shadow-lg transition-shadow"
                >
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                          {CATEGORY_ICONS[preset.category] || '📦'}
                          {preset.name}
                        </h3>
                        <p className="text-xs text-gray-500 mt-1">
                          {preset.tools_count} 个工具 · ⭐ {preset.star_count}
                        </p>
                      </div>
                      {preset.verified && (
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                          ✓ 官方认证
                        </span>
                      )}
                    </div>

                    <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                      {preset.description}
                    </p>

                    <div className="flex gap-2">
                      <button
                        onClick={() => handleConnect(preset)}
                        className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                      >
                        🔌 一键连接
                      </button>
                      {preset.homepage && (
                        <a
                          href={preset.homepage}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
                        >
                          📖
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      </>)}

      {/* Configuration Modal */}
      {selectedPreset && (
        <ConfigurationModal
          preset={selectedPreset}
          onClose={() => setSelectedPreset(null)}
          onConnect={async (env) => {
            try {
              // D2+D6: 使用 apiClient 统一请求
              const response = await apiClient.post('/mcp/connect', {
                server_id: selectedPreset.id,
                command: selectedPreset.command,
                args: selectedPreset.args,
                env,
              });

              // apiClient 返回 axios response，数据在 response.data
              const result = response.data;
              toast.success(`已连接 ${selectedPreset.name}，发现 ${result.tools_count} 个工具`);
              setSelectedPreset(null);
            } catch (error: any) {
              const detail = error.response?.data?.detail || error.message || '未知错误';
              toast.error(`连接失败: ${detail}`);
            }
          }}
        />
      )}
    </div>
  );
}

/* MCP 本机 Server 状态面板 */
function MCPServerPanel() {
  const [status, setStatus] = useState<any>(null);
  const [tools, setTools] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [testMethod, setTestMethod] = useState('tools/list');
  const [testResult, setTestResult] = useState<string>('');
  const [testLoading, setTestLoading] = useState(false);

  useEffect(() => {
    loadServerInfo();
  }, []);

  const loadServerInfo = async () => {
    setLoading(true);
    try {
      const [statusRes, toolsRes] = await Promise.all([
        apiClient.get('/mcp-server/status').catch(() => null),
        apiClient.post('/mcp-server/message', { jsonrpc: '2.0', id: 1, method: 'tools/list', params: {} }).catch(() => null),
      ]);
      if (statusRes) setStatus(statusRes.data);
      if (toolsRes?.data?.result?.tools) setTools(toolsRes.data.result.tools);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    setTestLoading(true);
    try {
      const res = await apiClient.post('/mcp-server/message', {
        jsonrpc: '2.0', id: Date.now(), method: testMethod, params: {},
      });
      setTestResult(JSON.stringify(res.data, null, 2));
    } catch (e: any) {
      setTestResult(JSON.stringify(e.response?.data || { error: e.message }, null, 2));
    } finally {
      setTestLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 状态卡片 */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className={`w-3 h-3 rounded-full ${status ? 'bg-green-500' : 'bg-red-500'}`} />
          <h2 className="text-lg font-semibold text-gray-900">MCP Server 状态</h2>
          <button onClick={loadServerInfo} className="ml-auto text-sm text-blue-600 hover:text-blue-700">刷新</button>
        </div>
        {status ? (
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-gray-900">{status.tools_count}</div>
              <div className="text-sm text-gray-500">注册工具</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-gray-900">{status.resources_count}</div>
              <div className="text-sm text-gray-500">资源端点</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-gray-900">{status.prompts_count}</div>
              <div className="text-sm text-gray-500">提示模板</div>
            </div>
          </div>
        ) : (
          <p className="text-gray-500">无法连接到 MCP Server</p>
        )}
      </div>

      {/* 工具列表 */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Wrench className="w-4 h-4" /> 已注册工具
        </h3>
        <div className="space-y-3">
          {tools.map((tool) => (
            <div key={tool.name} className="border border-gray-100 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-mono text-sm font-medium text-blue-700">{tool.name}</span>
              </div>
              <p className="text-sm text-gray-500 line-clamp-2">{tool.description?.split('\n')[0]}</p>
              {tool.inputSchema?.properties && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {Object.keys(tool.inputSchema.properties).map((param) => (
                    <span key={param} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs font-mono">
                      {param}
                      {tool.inputSchema.required?.includes(param) && <span className="text-red-500 ml-0.5">*</span>}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* JSON-RPC 测试控制台 */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Terminal className="w-4 h-4" /> JSON-RPC 测试控制台
        </h3>
        <div className="flex gap-2 mb-3">
          <select
            value={testMethod}
            onChange={(e) => setTestMethod(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm flex-1"
          >
            <option value="tools/list">tools/list</option>
            <option value="resources/list">resources/list</option>
            <option value="prompts/list">prompts/list</option>
            <option value="initialize">initialize</option>
          </select>
          <button
            onClick={handleTest}
            disabled={testLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {testLoading ? '发送中...' : '发送请求'}
          </button>
        </div>
        {testResult && (
          <pre className="bg-gray-900 text-green-400 p-4 rounded-lg text-xs overflow-auto max-h-64 font-mono">
            {testResult}
          </pre>
        )}
      </div>
    </div>
  );
}

function ConfigurationModal({
  preset,
  onClose,
  onConnect,
}: {
  preset: MCPPreset;
  onClose: () => void;
  onConnect: (env: Record<string, string>) => Promise<void>;
}) {
  const [envValues, setEnvValues] = useState<Record<string, string>>(preset.env);
  const [connecting, setConnecting] = useState(false);

  const handleConnect = async () => {
    setConnecting(true);
    await onConnect(envValues);
    setConnecting(false);
  };

  const hasEmptyVars = Object.entries(envValues).some(
    ([_key, value]) => value.startsWith('<') && value.endsWith('>')
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-6 max-w-lg w-full mx-4 max-h-[80vh] overflow-auto">
        <h2 className="text-xl font-bold text-gray-900 mb-2">
          配置 {preset.name}
        </h2>
        <p className="text-gray-600 text-sm mb-4">{preset.description}</p>

        {/* Setup Instructions */}
        {preset.setup_instructions && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <h4 className="font-medium text-blue-900 mb-2">📋 配置说明</h4>
            <div className="text-sm text-blue-800 whitespace-pre-line">
              {preset.setup_instructions}
            </div>
          </div>
        )}

        {/* Environment Variables */}
        {Object.keys(preset.env).length > 0 && (
          <div className="space-y-3 mb-6">
            <h4 className="font-medium text-gray-900">环境变量</h4>
            {Object.entries(preset.env).map(([key, defaultValue]) => (
              <div key={key}>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {key}
                </label>
                <input
                  type={defaultValue.includes('TOKEN') || defaultValue.includes('KEY') ? 'password' : 'text'}
                  value={envValues[key] || ''}
                  onChange={(e) => setEnvValues({ ...envValues, [key]: e.target.value })}
                  placeholder={defaultValue}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            ))}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleConnect}
            disabled={connecting || hasEmptyVars}
            className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {connecting ? '⏳ 连接中...' : '🔌 连接'}
          </button>
        </div>
      </div>
    </div>
  );
}

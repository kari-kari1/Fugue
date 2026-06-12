import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import {
  getPlugins,
  getTools,
  executeTool,
  reloadPlugin,
  healthCheckPlugins,
  getMarketplacePlugins,
  installMarketplacePlugin,
  type Plugin,
  type ToolInfo,
  type HealthCheckResult,
  type MarketplacePlugin,
} from '../api/plugins';
import toast from 'react-hot-toast';

const PERMISSION_COLORS = {
  safe: 'bg-green-100 text-green-800',
  caution: 'bg-yellow-100 text-yellow-800',
  dangerous: 'bg-red-100 text-red-800',
};

const CATEGORY_ICONS: Record<string, string> = {
  search: '🔍',
  file: '📁',
  data: '📊',
  code: '💻',
  text: '📝',
  math: '🔢',
  ai: '🤖',
  utility: '🛠️',
  general: '⚙️',
};

export default function Plugins() {
  const navigate = useNavigate();
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'plugins' | 'tools' | 'marketplace'>('plugins');
  const [marketplacePlugins, setMarketplacePlugins] = useState<MarketplacePlugin[]>([]);
  const [marketplaceLoading, setMarketplaceLoading] = useState(false);
  const [installingId, setInstallingId] = useState<string | null>(null);
  const [healthStatus, setHealthStatus] = useState<HealthCheckResult | null>(null);
  const [testingTool, setTestingTool] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [pluginsRes, toolsRes] = await Promise.all([
        getPlugins(),
        getTools(),
      ]);
      setPlugins(pluginsRes.plugins);
      setTools(toolsRes.tools);
    } catch (error) {
      console.error('Failed to load plugins:', error);
      toast.error('加载插件失败');
    } finally {
      setLoading(false);
    }
  };

  const loadMarketplace = async () => {
    setMarketplaceLoading(true);
    try {
      const res = await getMarketplacePlugins({ page_size: 50 });
      setMarketplacePlugins(res.plugins || []);
    } catch (error) {
      console.error('Failed to load marketplace:', error);
      toast.error('加载市场插件失败');
    } finally {
      setMarketplaceLoading(false);
    }
  };

  const handleInstall = async (pluginId: string, pluginName: string) => {
    setInstallingId(pluginId);
    try {
      await installMarketplacePlugin(pluginId);
      toast.success(`插件 "${pluginName}" 安装成功`);
      loadMarketplace();
      loadData();
    } catch (error: any) {
      toast.error(`安装失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setInstallingId(null);
    }
  };

  // 切换到市场 tab 时加载数据
  useEffect(() => {
    if (activeTab === 'marketplace' && marketplacePlugins.length === 0) {
      loadMarketplace();
    }
  }, [activeTab]);

  const handleReload = async (pluginName: string) => {
    try {
      await reloadPlugin(pluginName);
      toast.success(`插件 "${pluginName}" 已重新加载`);
      loadData();
    } catch (error) {
      toast.error(`重新加载插件失败: ${error}`);
    }
  };

  const handleHealthCheck = async () => {
    try {
      const result = await healthCheckPlugins();
      setHealthStatus(result);
      toast.success(`健康检查完成: ${result.healthy_count}/${result.total} 正常`);
    } catch (error) {
      toast.error('健康检查失败');
    }
  };

  const handleTestTool = async (toolName: string) => {
    setTestingTool(toolName);
    setTestResult(null);

    try {
      // 使用简单测试参数
      const testArgs: Record<string, any> = {};
      if (toolName === 'text_transform') {
        testArgs.text = 'Hello World';
        testArgs.operation = 'upper';
      } else if (toolName === 'calculator') {
        testArgs.expression = '2 + 2';
      } else if (toolName === 'datetime_util') {
        testArgs.operation = 'now';
      } else if (toolName === 'json_formatter') {
        testArgs.json_str = '{"name":"test","value":123}';
      } else {
        testArgs.text = 'test';
      }

      const result = await executeTool(toolName, testArgs);
      setTestResult(result.result);
      toast.success('工具测试成功');
    } catch (error) {
      toast.error(`工具测试失败: ${error}`);
      setTestResult(`错误: ${error}`);
    } finally {
      setTestingTool(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6" style={{ background: 'var(--bg-page)' }}>
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-1.5 mb-4 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors hover:bg-gray-100 text-gray-500 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>返回</span>
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">插件管理</h1>
            <p className="mt-2 text-gray-600">
              管理已安装的插件和工具，扩展Fugue的功能
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleHealthCheck}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              🏥 健康检查
            </button>
            <button
              onClick={loadData}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              🔄 刷新
            </button>
          </div>
        </div>

        {/* Health Status Banner */}
        {healthStatus && (
          <div className={`mt-4 p-4 rounded-lg ${
            healthStatus.healthy_count === healthStatus.total
              ? 'bg-green-50 border border-green-200'
              : 'bg-yellow-50 border border-yellow-200'
          }`}>
            <div className="flex items-center gap-2">
              <span className="text-lg">
                {healthStatus.healthy_count === healthStatus.total ? '✅' : '⚠️'}
              </span>
              <span className="font-medium">
                健康状态: {healthStatus.healthy_count}/{healthStatus.total} 插件正常运行
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="flex gap-8">
          <button
            onClick={() => setActiveTab('plugins')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'plugins'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            插件 ({plugins.length})
          </button>
          <button
            onClick={() => setActiveTab('tools')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'tools'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            工具 ({tools.length})
          </button>
          <button
            onClick={() => setActiveTab('marketplace')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'marketplace'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            市场
          </button>
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'plugins' ? (
        <PluginsList plugins={plugins} onReload={handleReload} />
      ) : activeTab === 'tools' ? (
        <ToolsList
          tools={tools}
          onTest={handleTestTool}
          testingTool={testingTool}
          testResult={testResult}
        />
      ) : (
        <MarketplaceList
          plugins={marketplacePlugins}
          loading={marketplaceLoading}
          installingId={installingId}
          onInstall={handleInstall}
          onRefresh={loadMarketplace}
        />
      )}

      {/* Test Result Modal */}
      {testResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">工具测试结果</h3>
              <button
                onClick={() => setTestResult(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <pre className="bg-gray-50 p-4 rounded-lg text-sm font-mono whitespace-pre-wrap overflow-auto">
              {testResult}
            </pre>
            <div className="mt-4 flex justify-end">
              <button
                onClick={() => setTestResult(null)}
                className="px-4 py-2 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function PluginsList({
  plugins,
  onReload,
}: {
  plugins: Plugin[];
  onReload: (name: string) => void;
}) {
  if (plugins.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
        <div className="text-6xl mb-4">🧩</div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">暂无插件</h3>
        <p className="text-gray-600">
          还没有加载任何插件。插件可以扩展Fugue的功能。
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {plugins.map((plugin) => (
        <div
          key={plugin.name}
          className="bg-white rounded-xl border border-gray-200 hover:shadow-lg transition-shadow"
        >
          <div className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{plugin.name}</h3>
                <p className="text-sm text-gray-500">v{plugin.version} · {plugin.author}</p>
              </div>
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                {plugin.tools_count} 工具
              </span>
            </div>

            <p className="text-gray-600 text-sm mb-4 line-clamp-2">
              {plugin.description}
            </p>

            {plugin.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {plugin.tags.slice(0, 3).map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}

            <div className="flex gap-2">
              <button
                onClick={() => onReload(plugin.name)}
                className="flex-1 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
              >
                🔄 重载
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function ToolsList({
  tools,
  onTest,
  testingTool,
  testResult: _testResult,
}: {
  tools: ToolInfo[];
  onTest: (name: string) => void;
  testingTool: string | null;
  testResult: string | null;
}) {
  if (tools.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
        <div className="text-6xl mb-4">🔧</div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">暂无工具</h3>
        <p className="text-gray-600">
          还没有可用的工具。安装插件后会自动注册工具。
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <table className="w-full">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              工具
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              分类
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              权限
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              操作
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {tools.map((tool) => (
            <tr key={tool.name} className="hover:bg-gray-50 transition-colors">
              <td className="px-6 py-4">
                <div>
                  <div className="font-medium text-gray-900 flex items-center gap-2">
                    <span>{CATEGORY_ICONS[tool.category] || '⚙️'}</span>
                    {tool.name}
                  </div>
                  <div className="text-sm text-gray-500 mt-1">{tool.description}</div>
                </div>
              </td>
              <td className="px-6 py-4">
                <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                  {tool.category}
                </span>
              </td>
              <td className="px-6 py-4">
                <span className={`px-2 py-1 rounded text-xs font-medium ${PERMISSION_COLORS[tool.permissions]}`}>
                  {tool.permissions}
                </span>
              </td>
              <td className="px-6 py-4 text-right">
                <button
                  onClick={() => onTest(tool.name)}
                  disabled={testingTool === tool.name}
                  className="px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {testingTool === tool.name ? '⏳ 测试中...' : '▶️ 测试'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MarketplaceList({
  plugins,
  loading,
  installingId,
  onInstall,
  onRefresh,
}: {
  plugins: MarketplacePlugin[];
  loading: boolean;
  installingId: string | null;
  onInstall: (id: string, name: string) => void;
  onRefresh: () => void;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (plugins.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
        <div className="text-6xl mb-4">🏪</div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">市场暂无插件</h3>
        <p className="text-gray-600 mb-4">
          还没有发布到市场的插件。发布您的插件让更多人使用！
        </p>
        <button
          onClick={onRefresh}
          className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors text-sm"
        >
          刷新
        </button>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {plugins.map((plugin) => (
        <div
          key={plugin.id}
          className="bg-white rounded-xl border border-gray-200 hover:shadow-lg transition-shadow"
        >
          <div className="p-6">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{plugin.display_name}</h3>
                <p className="text-sm text-gray-500">v{plugin.current_version} · {plugin.author}</p>
              </div>
              <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-medium">
                {plugin.category}
              </span>
            </div>

            <p className="text-sm text-gray-600 mb-4 line-clamp-2">{plugin.description}</p>

            <div className="flex items-center gap-4 mb-4 text-xs text-gray-500">
              <span>⬇️ {plugin.download_count}</span>
              <span>⭐ {plugin.average_rating?.toFixed(1) || 'N/A'}</span>
              <span>🔧 {plugin.tools_list?.length || 0} 工具</span>
            </div>

            {plugin.tags && plugin.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-4">
                {plugin.tags.slice(0, 3).map((tag) => (
                  <span key={tag} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                    {tag}
                  </span>
                ))}
              </div>
            )}

            <button
              onClick={() => onInstall(plugin.id, plugin.display_name)}
              disabled={installingId === plugin.id}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {installingId === plugin.id ? '安装中...' : '安装'}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

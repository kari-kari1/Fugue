import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { t } from '../lib/i18n';
import {
  getPlugins,
  getTools,
  executeTool,
  reloadPlugin,
  healthCheckPlugins,
  type Plugin,
  type ToolInfo,
  type HealthCheckResult,
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
  const [activeTab, setActiveTab] = useState<'plugins' | 'tools'>('plugins');
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
          <span>{t('common.back')}</span>
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{t('plugins.title')}</h1>
            <p className="mt-2 text-gray-600">
              {t('plugins.subtitle')}
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleHealthCheck}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              🏥 {t('plugins.health_check')}
            </button>
            <button
              onClick={loadData}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              🔄 {t('common.refresh')}
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
            {t('plugins.tab_plugins')} ({plugins.length})
          </button>
          <button
            onClick={() => setActiveTab('tools')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'tools'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t('plugins.tab_tools')} ({tools.length})
          </button>
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'plugins' ? (
        <PluginsList plugins={plugins} onReload={handleReload} />
      ) : (
        <ToolsList
          tools={tools}
          onTest={handleTestTool}
          testingTool={testingTool}
          testResult={testResult}
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
        <h3 className="text-lg font-semibold text-gray-900 mb-2">{t('plugins.no_plugins')}</h3>
        <p className="text-gray-600">
          {t('plugins.no_plugins_desc')}
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
        <h3 className="text-lg font-semibold text-gray-900 mb-2">{t('plugins.no_tools')}</h3>
        <p className="text-gray-600">
          {t('plugins.no_tools_desc')}
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


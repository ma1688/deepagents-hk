import { useState, useEffect } from 'react';
import {
  X,
  Key,
  Cpu,
  Thermometer,
  Hash,
  Eye,
  EyeOff,
  Check,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { useConfigStore } from '@/stores';
import { useAuthStore } from '@/stores/authStore';
import { configApi } from '@/api/client';
import { ModelOption } from '@/types';
import styles from './Config.module.css';

export function ConfigPanel() {
  const { user } = useAuthStore();
  const userId = user?.id;
  const {
    config,
    availableModels,
    isConfigPanelOpen,
    setConfig,
    setAvailableModels,
    setConfigPanelOpen,
  } = useConfigStore();

  const [provider, setProvider] = useState('siliconflow');
  const [modelName, setModelName] = useState('deepseek-chat');
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(20000);
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  // Load available models
  useEffect(() => {
    configApi.getModels()
      .then((data) => setAvailableModels(data.models))
      .catch(console.error);
  }, [setAvailableModels]);

  // Load user config
  useEffect(() => {
    if (!userId) return;
    
    configApi.getConfig(userId)
      .then((data) => {
        setConfig(data);
        setProvider(data.provider);
        setModelName(data.modelName);
        setTemperature(data.temperature);
        setMaxTokens(data.maxTokens);
      })
      .catch(console.error);
  }, [userId, setConfig]);

  // Filter models by provider
  const filteredModels = availableModels.filter((m) => m.provider === provider);

  // Get selected model info
  const selectedModel = availableModels.find(
    (m) => m.provider === provider && m.modelName === modelName
  );

  const handleProviderChange = (newProvider: string) => {
    setProvider(newProvider);
    // Select first model of new provider
    const firstModel = availableModels.find((m) => m.provider === newProvider);
    if (firstModel) {
      setModelName(firstModel.modelName);
    }
  };

  const handleSave = async () => {
    if (!userId) return;
    
    setIsSaving(true);
    setTestResult(null);
    
    try {
      const updatedConfig = await configApi.updateConfig(userId, {
        provider,
        modelName,
        apiKey: apiKey || undefined,
        temperature,
        maxTokens,
      });
      setConfig(updatedConfig);
      setApiKey(''); // Clear API key input after save
      setTestResult({ success: true, message: '配置已保存' });
    } catch (error) {
      setTestResult({ 
        success: false, 
        message: error instanceof Error ? error.message : '保存失败' 
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleTest = async () => {
    if (!userId) return;
    
    setIsTesting(true);
    setTestResult(null);
    
    try {
      const result = await configApi.testConfig(userId);
      setTestResult({ success: true, message: result.message });
    } catch (error) {
      setTestResult({ 
        success: false, 
        message: error instanceof Error ? error.message : '测试失败' 
      });
    } finally {
      setIsTesting(false);
    }
  };

  if (!isConfigPanelOpen) return null;

  return (
    <div className={styles.overlay} onClick={() => setConfigPanelOpen(false)}>
      <div className={styles.panel} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className={styles.header}>
          <h2>设置</h2>
          <button 
            className={styles.closeBtn}
            onClick={() => setConfigPanelOpen(false)}
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className={styles.content}>
          {/* Provider Selection */}
          <div className={styles.section}>
            <label className={styles.label}>
              <Cpu size={16} />
              模型提供商
            </label>
            <div className={styles.providerButtons}>
              {['siliconflow', 'openai', 'anthropic'].map((p) => (
                <button
                  key={p}
                  className={`${styles.providerBtn} ${provider === p ? styles.active : ''}`}
                  onClick={() => handleProviderChange(p)}
                >
                  {p === 'siliconflow' && '硅基流动'}
                  {p === 'openai' && 'OpenAI'}
                  {p === 'anthropic' && 'Anthropic'}
                </button>
              ))}
            </div>
          </div>

          {/* Model Selection */}
          <div className={styles.section}>
            <label className={styles.label}>
              <Cpu size={16} />
              模型
            </label>
            <select
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              className={styles.select}
            >
              {filteredModels.map((model) => (
                <option key={model.modelName} value={model.modelName}>
                  {model.displayName}
                </option>
              ))}
            </select>
            {selectedModel && (
              <div className={styles.modelInfo}>
                <span>上下文: {selectedModel.contextLimit.toLocaleString()} tokens</span>
                {selectedModel.pricePerMillion && (
                  <span>价格: ¥{selectedModel.pricePerMillion}/百万tokens</span>
                )}
              </div>
            )}
          </div>

          {/* API Key */}
          <div className={styles.section}>
            <label className={styles.label}>
              <Key size={16} />
              API 密钥
              {config?.hasApiKey && (
                <span className={styles.badge}>已配置</span>
              )}
            </label>
            <div className={styles.apiKeyInput}>
              <input
                type={showApiKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={config?.hasApiKey ? '输入新密钥以更新...' : '请输入API密钥'}
              />
              <button
                className={styles.eyeBtn}
                onClick={() => setShowApiKey(!showApiKey)}
              >
                {showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Temperature */}
          <div className={styles.section}>
            <label className={styles.label}>
              <Thermometer size={16} />
              温度 (Temperature)
              <span className={styles.value}>{temperature.toFixed(1)}</span>
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              className={styles.slider}
            />
            <div className={styles.sliderLabels}>
              <span>精确</span>
              <span>创意</span>
            </div>
          </div>

          {/* Max Tokens */}
          <div className={styles.section}>
            <label className={styles.label}>
              <Hash size={16} />
              最大输出 Tokens
            </label>
            <input
              type="number"
              value={maxTokens}
              onChange={(e) => setMaxTokens(parseInt(e.target.value) || 0)}
              min={100}
              max={200000}
              className={styles.numberInput}
            />
          </div>

          {/* Test Result */}
          {testResult && (
            <div className={`${styles.testResult} ${testResult.success ? styles.success : styles.error}`}>
              {testResult.success ? <Check size={16} /> : <AlertCircle size={16} />}
              {testResult.message}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className={styles.footer}>
          <button
            className={styles.testBtn}
            onClick={handleTest}
            disabled={isTesting || !config?.hasApiKey}
          >
            {isTesting ? <Loader2 size={16} className="animate-spin" /> : '测试连接'}
          </button>
          <button
            className={styles.saveBtn}
            onClick={handleSave}
            disabled={isSaving}
          >
            {isSaving ? <Loader2 size={16} className="animate-spin" /> : '保存配置'}
          </button>
        </div>
      </div>
    </div>
  );
}


import React, { useState, useEffect } from 'react';
import { 
  Save, 
  Download, 
  Upload, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle,
  FileText,
  Trash2
} from 'lucide-react';
import { DeviceConfig, ConnectionStatus, SafeSettings, CriticalSettings, LoRaConfig } from '../types';
import { apiService } from '../services/apiService.tsx';

interface ConfigurationTabProps {
  connectionStatus: ConnectionStatus;
  onStatusChange: (status: ConnectionStatus) => void;
}

// Max unsigned 32-bit integer (4 294 967 295)
const UINT32_MAX = 4294967295;

const ConfigurationTab: React.FC<ConfigurationTabProps> = ({ 
  connectionStatus, 
  onStatusChange 
}) => {
  /* ------------------ State ------------------ */
  const [config, setConfig] = useState<DeviceConfig>({
    safe_settings: {
      sd_filename: "gg.wp",
      sd_filename_wq: "gg.wq",
      data_period: 250,
      data_period_lnd: 250,
      press_buffer_len: 64,
      press_land_delta: 20
    },
    critical_settings: {
      start_th: 60,
      eject_th: 240
    },
    lora_config: {
      frequency: 433000000,
      bandwidth: 7,
      spreading_factor: 7,
      coding_rate: 0,
      header_mode: 0,
      crc_enabled: 1,
      low_data_rate_optimize: 0,
      preamble_length: 8,
      payload_length: 255,
      tx_power: 15,
      tx_addr: 0,
      rx_addr: 0
    }
  });

  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info', text: string } | null>(null);
  const [configFiles, setConfigFiles] = useState<any[]>([]);
  // Unified field: user can type a new name or pick an existing one for overwrite
  const [saveFileName, setSaveFileName] = useState<string>('');

  /* ------------------ Effects ------------------ */
  useEffect(() => {
    loadConfigFiles();
  }, []);

  /* ------------------ Helpers ------------------ */
  const showMessage = (type: 'success' | 'error' | 'info', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const loadConfigFiles = async () => {
    try {
      const files = await apiService.listConfigFiles();
      setConfigFiles(files);
    } catch (error) {
      console.error('Failed to load config files:', error);
    }
  };

  /* ------------------ API Calls ------------------ */
  const readFromDevice = async () => {
    if (connectionStatus.status === 'disconnected') {
      showMessage('error', 'Device not connected');
      return;
    }
    setIsLoading(true);
    try {
      const deviceConfig = await apiService.readDeviceConfig();
      setConfig(deviceConfig);
      showMessage('success', 'Configuration read from device');
    } catch (error) {
      showMessage('error', `Failed to read configuration: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  const writeToDevice = async () => {
    if (connectionStatus.status === 'disconnected') {
      showMessage('error', 'Device not connected');
      return;
    }
    setIsLoading(true);
    try {
      await apiService.writeDeviceConfig(config);
      showMessage('success', 'Configuration written to device');
    } catch (error) {
      showMessage('error', `Failed to write configuration: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Unified save: user can either type a new name or choose an existing file to overwrite
  const saveConfigFile = async () => {
    const trimmed = saveFileName.trim();
    if (!trimmed) {
      showMessage('error', 'Please enter or select a filename');
      return;
    }
    setIsLoading(true);
    try {
      await apiService.saveConfigFile(trimmed, config);
      showMessage('success', `Configuration saved as ${trimmed}.gchcfg`);
      setSaveFileName('');
      await loadConfigFiles();
    } catch (error) {
      showMessage('error', `Failed to save configuration: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  const loadConfigFile = async () => {
    if (!saveFileName.trim()) {
      showMessage('error', 'Please select or enter a filename to load');
      return;
    }
    setIsLoading(true);
    try {
      const loadedConfig = await apiService.loadConfigFile(saveFileName.trim());
      setConfig(loadedConfig);
      showMessage('success', `Configuration loaded from ${saveFileName.trim()}.gchcfg`);
    } catch (error) {
      showMessage('error', `Failed to load configuration: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  /* ------------------ Field Updaters ------------------ */
  const updateSafeSettings = (field: keyof SafeSettings, value: string | number) => {
    setConfig(prev => ({
      ...prev,
      safe_settings: { ...prev.safe_settings, [field]: value }
    }));
  };

  const updateCriticalSettings = (field: keyof CriticalSettings, value: number) => {
    setConfig(prev => ({
      ...prev,
      critical_settings: { ...prev.critical_settings, [field]: value }
    }));
  };

  const updateLoRaConfig = (field: keyof LoRaConfig, value: number) => {
    setConfig(prev => ({
      ...prev,
      lora_config: { ...prev.lora_config, [field]: value }
    }));
  };

  /* ------------------ Render ------------------ */
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Device Configuration</h2>
        <div className="flex space-x-3">
          <button
            onClick={readFromDevice}
            disabled={isLoading || connectionStatus.status === 'disconnected'}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            <span>Read from Device</span>
          </button>
          <button
            onClick={writeToDevice}
            disabled={isLoading || connectionStatus.status === 'disconnected'}
            className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded-lg transition-colors"
          >
            <Upload className="w-4 h-4" />
            <span>Write to Device</span>
          </button>
        </div>
      </div>

      {/* Status Message */}
      {message && (
        <div className={`p-4 rounded-lg flex items-center space-x-2 ${
          message.type === 'success' ? 'bg-green-900 text-green-200' :
          message.type === 'error' ? 'bg-red-900 text-red-200' :
          'bg-blue-900 text-blue-200'
        }`}>
          {message.type === 'success' && <CheckCircle className="w-5 h-5" />}
          {message.type === 'error' && <AlertTriangle className="w-5 h-5" />}
          <span>{message.text}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Safe & Critical Settings */}
        <div className="space-y-6">
          {/* Safe Settings */}
          <div className="bg-dark-800 p-6 rounded-lg">
            <h3 className="text-lg font-semibold text-green-400 mb-4 flex items-center">
              <CheckCircle className="w-5 h-5 mr-2" />
              Safe Settings
            </h3>
            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Primary SD Filename
                </label>
                <input
                  type="text"
                  value={config.safe_settings.sd_filename}
                  onChange={(e) => updateSafeSettings('sd_filename', e.target.value)}
                  className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="gg.wp"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Dump SD Filename
                </label>
                <input
                  type="text"
                  value={config.safe_settings.sd_filename_wq}
                  onChange={(e) => updateSafeSettings('sd_filename_wq', e.target.value)}
                  className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="gg.wq"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Data Period (ms) <span className="text-xs text-gray-500">[10 – {UINT32_MAX}]</span>
                  </label>
                  <input
                    type="number"
                    min={10}
                    max={UINT32_MAX}
                    value={config.safe_settings.data_period}
                    onChange={(e) => updateSafeSettings('data_period', parseInt(e.target.value, 10) || 10)}
                    className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Landing Period (ms) <span className="text-xs text-gray-500">[10 – {UINT32_MAX}]</span>
                  </label>
                  <input
                    type="number"
                    min={10}
                    max={UINT32_MAX}
                    value={config.safe_settings.data_period_lnd}
                    onChange={(e) => updateSafeSettings('data_period_lnd', parseInt(e.target.value, 10) || 10)}
                    className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Pressure Buffer Length <span className="text-xs text-gray-500">[8 – 256]</span>
                  </label>
                  <input
                    type="number"
                    min={8}
                    max={256}
                    value={config.safe_settings.press_buffer_len}
                    onChange={(e) => updateSafeSettings('press_buffer_len', parseInt(e.target.value, 10) || 64)}
                    className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Landing Delta (Pa) <span className="text-xs text-gray-500">[5 – 100]</span>
                  </label>
                  <input
                    type="number"
                    min={5}
                    max={100}
                    value={config.safe_settings.press_land_delta}
                    onChange={(e) => updateSafeSettings('press_land_delta', parseInt(e.target.value, 10) || 20)}
                    className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Critical Settings */}
          <div className="bg-dark-800 p-6 rounded-lg border border-red-600">
            <h3 className="text-lg font-semibold text-red-400 mb-4 flex items-center">
              <AlertTriangle className="w-5 h-5 mr-2" />
              Critical Settings
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Start Threshold (Pa) <span className="text-xs text-gray-500">[10 – 200]</span>
                </label>
                <input
                  type="number"
                  min={10}
                  max={200}
                  value={config.critical_settings.start_th}
                  onChange={(e) => updateCriticalSettings('start_th', parseInt(e.target.value, 10) || 60)}
                  className="w-full px-3 py-2 bg-dark-700 border border-red-600 rounded-lg text-white focus:ring-2 focus:ring-red-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Ejection Threshold <span className="text-xs text-gray-500">[100 – 255]</span>
                </label>
                <input
                  type="number"
                  min={100}
                  max={255}
                  value={config.critical_settings.eject_th}
                  onChange={(e) => updateCriticalSettings('eject_th', parseInt(e.target.value, 10) || 240)}
                  className="w-full px-3 py-2 bg-dark-700 border border-red-600 rounded-lg text-white focus:ring-2 focus:ring-red-500 focus:border-transparent"
                />
              </div>
            </div>
            <p className="text-sm text-red-300 mt-2">
              ⚠️ Critical settings affect flight safety. Modify with caution.
            </p>
          </div>
        </div>

        {/* Right Column: LoRa & File Management */}
        <div className="space-y-6">
          {/* LoRa Configuration */}
          <div className="bg-dark-800 p-6 rounded-lg">
            <h3 className="text-lg font-semibold text-blue-400 mb-4">LoRa Configuration</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Frequency (Hz) <span className="text-xs text-gray-500">[1 – {UINT32_MAX}]</span>
                </label>
                <input
                  type="number"
                  min={1}
                  max={UINT32_MAX}
                  value={config.lora_config.frequency}
                  onChange={(e) => updateLoRaConfig('frequency', parseInt(e.target.value, 10) || 433000000)}
                  className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Bandwidth <span className="text-xs text-gray-500">[0 – 9]</span>
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={9}
                    value={config.lora_config.bandwidth}
                    onChange={(e) => updateLoRaConfig('bandwidth', parseInt(e.target.value, 10) || 7)}
                    className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    SF <span className="text-xs text-gray-500">[6 – 12]</span>
                  </label>
                  <input
                    type="number"
                    min={6}
                    max={12}
                    value={config.lora_config.spreading_factor}
                    onChange={(e) => updateLoRaConfig('spreading_factor', parseInt(e.target.value, 10) || 7)}
                    className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    TX Power <span className="text-xs text-gray-500">[0 – 15]</span>
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={15}
                    value={config.lora_config.tx_power}
                    onChange={(e) => updateLoRaConfig('tx_power', parseInt(e.target.value, 10) || 15)}
                    className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Coding Rate <span className="text-xs text-gray-500">[0 – 3]</span>
                  </label>
                  <select
                    value={config.lora_config.coding_rate}
                    onChange={(e) => updateLoRaConfig('coding_rate', parseInt(e.target.value, 10))}
                    className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value={0}>4/5</option>
                    <option value={1}>4/6</option>
                    <option value={2}>4/7</option>
                    <option value={3}>4/8</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Payload Length <span className="text-xs text-gray-500">[1 – 255]</span>
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={255}
                    value={config.lora_config.payload_length}
                    onChange={(e) => updateLoRaConfig('payload_length', parseInt(e.target.value, 10) || 255)}
                    className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>
          </div>

		{/* Unified File Management */}
<div className="bg-dark-800 p-6 rounded-lg">
  <h3 className="text-lg font-semibold text-gray-300 mb-4 flex items-center">
    <FileText className="w-5 h-5 mr-2" />
    Configuration Files
  </h3>

  <label className="block text-sm font-medium text-gray-300 mb-1">
    Filename (type new or select existing)
  </label>
  <div className="flex space-x-2 mb-3">
    {/* Editable select – dropdown + free text */}
    <input
      type="text"
      value={saveFileName}
      onChange={(e) => setSaveFileName(e.target.value)}
      placeholder="Enter new or choose existing name"
      className="flex-1 px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
      list="configFilesDatalist"
    />
    <datalist id="configFilesDatalist">
      {configFiles.map(f => (
        <option key={f.name} value={f.name}>{f.name}.gchcfg</option>
      ))}
    </datalist>

    <button
      onClick={saveConfigFile}
      disabled={isLoading || !saveFileName.trim()}
      className="flex items-center space-x-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-600 rounded-lg transition-colors"
    >
      <Save className="w-4 h-4" />
      <span>Save</span>
    </button>

    <button
      onClick={loadConfigFile}
      disabled={isLoading || !saveFileName.trim()}
      className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg transition-colors"
    >
      <Upload className="w-4 h-4" />
      <span>Load</span>
    </button>

    <button
      onClick={loadConfigFiles}
      disabled={isLoading}
      className="flex items-center px-3 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-700 rounded-lg transition-colors"
    >
      <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
    </button>
  </div>
</div>
        </div>
      </div>
    </div>
  );
};

export default ConfigurationTab;
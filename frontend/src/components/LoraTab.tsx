import React, { useState, useEffect } from 'react';
import { 
  Radio, 
  Send, 
  Download, 
  RefreshCw,
  Terminal,
  Satellite
} from 'lucide-react';
import { ConnectionStatus } from '../types';
import { apiService } from '../services/apiService.tsx';

interface LoRaTabProps {
  connectionStatus: ConnectionStatus;
  onStatusChange: (status: ConnectionStatus) => void;
}

const LoRaTab: React.FC<LoRaTabProps> = ({ 
  connectionStatus, 
  onStatusChange 
}) => {
  const [terminalInput, setTerminalInput] = useState('');
  const [terminalHistory, setTerminalHistory] = useState<string[]>([
    'LoRa Link Terminal - Ready',
    'Type commands and press Enter to send...'
  ]);
  const [availablePorts, setAvailablePorts] = useState<string[]>([]);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isBinding, setIsBinding] = useState(false);

  useEffect(() => {
    scanForDevices();
  }, []);

  const scanForDevices = async () => {
    try {
      const devices = await apiService.scanDevices();
      setAvailablePorts(devices.lora_link || []);
    } catch (error) {
      console.error('Failed to scan for devices:', error);
    }
  };

  const connectToLoRa = async (port?: string) => {
    setIsConnecting(true);
    try {
      await apiService.connectDevice('lora_link', port);
      const status = await apiService.getDeviceStatus();
      onStatusChange(status);
      
      setTerminalHistory(prev => [...prev, `Connected to LoRa Link on ${port || 'auto-detected port'}`]);
    } catch (error) {
      setTerminalHistory(prev => [...prev, `Connection failed: ${error}`]);
    } finally {
      setIsConnecting(false);
    }
  };

  const disconnectLoRa = async () => {
    try {
      await apiService.disconnectDevice('lora_link');
      const status = await apiService.getDeviceStatus();
      onStatusChange(status);
      
      setTerminalHistory(prev => [...prev, 'Disconnected from LoRa Link']);
    } catch (error) {
      setTerminalHistory(prev => [...prev, `Disconnect failed: ${error}`]);
    }
  };

  const sendCommand = async () => {
    if (!terminalInput.trim()) return;

    const command = terminalInput.trim();
    setTerminalHistory(prev => [...prev, `> ${command}`]);
    setTerminalInput('');

    try {
      const response = await apiService.sendCommand(command, true);
      setTerminalHistory(prev => [...prev, response.response || 'No response']);
    } catch (error) {
      setTerminalHistory(prev => [...prev, `Error: ${error}`]);
    }
  };

  const bindSatellite = async () => {
    setIsBinding(true);
    setTerminalHistory(prev => [...prev, 'Binding satellite...']);
    
    try {
      const result = await apiService.bindLoRaSatellite();
      setTerminalHistory(prev => [...prev, 
        result.success ? 'Satellite bound successfully' : 'Binding failed'
      ]);
    } catch (error) {
      setTerminalHistory(prev => [...prev, `Binding error: ${error}`]);
    } finally {
      setIsBinding(false);
    }
  };

  const readBlackbox = async () => {
    setTerminalHistory(prev => [...prev, 'Reading blackbox data...']);
    
    try {
      const result = await apiService.readBlackboxViaLoRa();
      setTerminalHistory(prev => [...prev, 
        `Blackbox read successfully: ${result.data_size} bytes saved to ${result.file_path}`
      ]);
    } catch (error) {
      setTerminalHistory(prev => [...prev, `Blackbox read failed: ${error}`]);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">LoRa Link Interface</h2>
        <button
          onClick={scanForDevices}
          className="flex items-center space-x-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Scan Devices</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Connection Panel */}
        <div className="card">
          <h3 className="text-lg font-semibold text-blue-400 mb-4 flex items-center">
            <Radio className="w-5 h-5 mr-2" />
            Connection
          </h3>
          
          {availablePorts.length === 0 ? (
            <div className="text-yellow-400 mb-4">
              ⚠️ No LoRa Link devices found. Make sure device is connected via USB.
            </div>
          ) : (
            <div className="mb-4">
              <p className="text-gray-300 mb-2">Available LoRa Link devices:</p>
              <ul className="space-y-1">
                {availablePorts.map(port => (
                  <li key={port} className="text-green-400 font-mono text-sm">• {port}</li>
                ))}
              </ul>
            </div>
          )}

          {connectionStatus.device_type !== 'lora_link' ? (
            <button
              onClick={() => connectToLoRa()}
              disabled={isConnecting || availablePorts.length === 0}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg transition-colors"
            >
              <Radio className={`w-4 h-4 ${isConnecting ? 'animate-spin' : ''}`} />
              <span>{isConnecting ? 'Connecting...' : 'Connect to LoRa Link'}</span>
            </button>
          ) : (
            <button
              onClick={disconnectLoRa}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
            >
              <Radio className="w-4 h-4" />
              <span>Disconnect</span>
            </button>
          )}

          {/* Quick Actions */}
          <div className="mt-4 space-y-2">
            <button
              onClick={bindSatellite}
              disabled={connectionStatus.device_type !== 'lora_link' || isBinding}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 rounded-lg transition-colors"
            >
              <Satellite className={`w-4 h-4 ${isBinding ? 'animate-spin' : ''}`} />
              <span>{isBinding ? 'Binding...' : 'Bind Satellite'}</span>
            </button>

            <button
              onClick={readBlackbox}
              disabled={connectionStatus.device_type !== 'lora_link'}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-600 rounded-lg transition-colors"
            >
              <Download className="w-4 h-4" />
              <span>Read Blackbox</span>
            </button>
          </div>
        </div>

        {/* Terminal */}
        <div className="card">
          <h3 className="text-lg font-semibold text-green-400 mb-4 flex items-center">
            <Terminal className="w-5 h-5 mr-2" />
            Terminal
          </h3>
          
          {/* Terminal Display */}
          <div className="terminal h-64 mb-4">
            {terminalHistory.map((line, index) => (
              <div key={index} className="mb-1">
                {line}
              </div>
            ))}
          </div>

          {/* Terminal Input */}
          <div className="flex space-x-2">
            <span className="text-green-400 font-mono">$</span>
            <input
              type="text"
              value={terminalInput}
              onChange={(e) => setTerminalInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendCommand()}
              disabled={connectionStatus.device_type !== 'lora_link'}
              placeholder="Enter command..."
              className="flex-1 terminal-input"
            />
            <button
              onClick={sendCommand}
              disabled={connectionStatus.device_type !== 'lora_link' || !terminalInput.trim()}
              className="flex items-center space-x-2 px-3 py-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          
          <p className="text-xs text-gray-400 mt-2">
            {connectionStatus.device_type === 'lora_link' 
              ? 'Terminal connected - ready for commands'
              : 'Connect to LoRa Link to use terminal'
            }
          </p>
        </div>
      </div>

      {/* LoRa Settings Panel (Placeholder) */}
      <div className="card">
        <h3 className="text-lg font-semibold text-yellow-400 mb-4">LoRa Link Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Frequency (MHz)
            </label>
            <input
              type="number"
              defaultValue="433"
              className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              disabled
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Device Address
            </label>
            <input
              type="text"
              defaultValue="0x01"
              className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              disabled
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Encryption Key
            </label>
            <input
              type="text"
              defaultValue="************"
              className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              disabled
            />
          </div>
        </div>
        <p className="text-sm text-gray-400 mt-4">
          ℹ️ LoRa Link settings configuration will be implemented in a future version.
        </p>
      </div>
    </div>
  );
};

export default LoRaTab;
import React, { useState, useEffect } from 'react';
import {
  Settings,
  Plane,
  TestTube2,
  Radio,
  BarChart3,
  Wifi,
  WifiOff,
  Battery,
  Signal
} from 'lucide-react';

import ConfigurationTab from './components/ConfigurationTab.tsx';
import FlightTab from './components/FlightTab.tsx';
import TestsTab from './components/TestsTab.tsx';
import LoRaTab from './components/LoraTab.tsx';
import AnalysisTab from './components/AnalysisTab.tsx';
import StatusBar from './components/StatusBar.tsx';
import { ConnectionStatus, TelemetryData } from './types';
import { apiService } from './services/apiService.tsx';
import './App.css';

type Tab = 'configuration' | 'flight' | 'tests' | 'lora' | 'analysis';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('configuration');
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    status: 'disconnected',
    port: null,
    device_type: null,
    last_seen: null,
    signal_strength: null
  });
  const [telemetryData, setTelemetryData] = useState<TelemetryData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Poll connection status
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const status = await apiService.getDeviceStatus();
        setConnectionStatus(status);
      } catch (error) {
        console.error('Failed to get device status:', error);
        setConnectionStatus({
          status: 'error',
          port: null,
          device_type: null,
          last_seen: null,
          signal_strength: null
        });
      }
    };

    // Check status immediately and then every 5 seconds
    checkStatus();
    const interval = setInterval(checkStatus, 5000);

    return () => clearInterval(interval);
  }, []);

  const tabs = [
    { id: 'configuration', label: 'Configuration', icon: Settings },
    { id: 'flight', label: 'Flight', icon: Plane },
    { id: 'tests', label: 'Tests', icon: TestTube2 },
    { id: 'lora', label: 'LoRa Link', icon: Radio },
    { id: 'analysis', label: 'Analysis', icon: BarChart3 },
  ];

  const getConnectionIcon = () => {
    switch (connectionStatus.status) {
      case 'connected_usb':
        return <Wifi className="w-4 h-4 text-green-500" />;
      case 'connected_lora':
        return <Radio className="w-4 h-4 text-blue-500" />;
      case 'error':
        return <WifiOff className="w-4 h-4 text-red-500" />;
      default:
        return <WifiOff className="w-4 h-4 text-gray-400" />;
    }
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'configuration':
        return (
          <ConfigurationTab
            connectionStatus={connectionStatus}
            onStatusChange={setConnectionStatus}
          />
        );
      case 'flight':
        return (
          <FlightTab
            connectionStatus={connectionStatus}
            telemetryData={telemetryData}
            onTelemetryData={setTelemetryData}
          />
        );
      case 'tests':
        return (
          <TestsTab
            connectionStatus={connectionStatus}
          />
        );
      case 'lora':
        return (
          <LoRaTab
            connectionStatus={connectionStatus}
            onStatusChange={setConnectionStatus}
          />
        );
      case 'analysis':
        return (
          <AnalysisTab />
        );
      default:
        return <div>Tab not implemented</div>;
    }
  };

  return (
    <div className="min-h-screen bg-dark-900 text-white flex flex-col">
      {/* Header */}
      <header className="bg-dark-800 border-b border-dark-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-primary-400">
              Ground Control Hub
            </h1>
            <div className="flex items-center space-x-2 text-sm text-gray-400">
              {getConnectionIcon()}
              <span>
                {connectionStatus.status === 'connected_usb' && 'USB Connected'}
                {connectionStatus.status === 'connected_lora' && 'LoRa Connected'}
                {connectionStatus.status === 'disconnected' && 'Disconnected'}
                {connectionStatus.status === 'error' && 'Connection Error'}
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4 text-sm">
            {telemetryData?.battery_voltage && (
              <div className="flex items-center space-x-2">
                <Battery className="w-4 h-4" />
                <span>{telemetryData.battery_voltage.toFixed(1)}V</span>
              </div>
            )}
            {telemetryData?.rssi && (
              <div className="flex items-center space-x-2">
                <Signal className="w-4 h-4" />
                <span>{telemetryData.rssi} dBm</span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="bg-dark-800 border-b border-dark-700">
        <div className="px-6">
          <div className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as Tab)}
                  className={`
                    flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm
                    ${activeTab === tab.id
                      ? 'border-primary-500 text-primary-400'
                      : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                    }
                  `}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 p-6">
        {renderTabContent()}
      </main>

      {/* Status Bar */}
      <StatusBar
        connectionStatus={connectionStatus}
        telemetryData={telemetryData}
        isLoading={isLoading}
      />
    </div>
  );
};

export default App;
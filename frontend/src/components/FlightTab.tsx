import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Square, 
  Send, 
  Activity, 
  Gauge, 
  Navigation,
  Battery,
  Radio,
  MapPin,
  Thermometer
} from 'lucide-react';
import { ConnectionStatus, TelemetryData } from '../types';
import { apiService } from '../services/apiService.tsx';

interface FlightTabProps {
  connectionStatus: ConnectionStatus;
  telemetryData: TelemetryData | null;
  onTelemetryData: (data: TelemetryData) => void;
}

const FlightTab: React.FC<FlightTabProps> = ({ 
  connectionStatus, 
  telemetryData,
  onTelemetryData 
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [command, setCommand] = useState('');
  const [commandHistory, setCommandHistory] = useState<any[]>([]);
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // WebSocket connection for real-time telemetry
  useEffect(() => {
    if (connectionStatus.status !== 'disconnected') {
      const ws = apiService.createTelemetryWebSocket(
        (data: TelemetryData) => {
          onTelemetryData(data);
        },
        (error) => {
          console.error('WebSocket error:', error);
        }
      );
      
      setWebsocket(ws);
      
      return () => {
        ws.close();
      };
    }
  }, [connectionStatus, onTelemetryData]);

  const handleStartRecording = () => {
    setIsRecording(true);
    console.log('Started recording telemetry');
  };

  const handleStopRecording = () => {
    setIsRecording(false);
    console.log('Stopped recording telemetry');
  };

  const handleSendCommand = async () => {
    if (!command.trim()) return;

    setIsLoading(true);
    try {
      const useLora = connectionStatus.status === 'connected_lora';
      const response = await apiService.sendCommand(command.trim(), useLora);
      
      setCommandHistory(prev => [...prev, response]);
      setCommand('');
    } catch (error) {
      console.error('Failed to send command:', error);
      setCommandHistory(prev => [...prev, {
        command: command.trim(),
        response: `Error: ${error}`,
        timestamp: new Date().toISOString(),
        via_lora: connectionStatus.status === 'connected_lora'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePing = async () => {
    setIsLoading(true);
    try {
      const useLora = connectionStatus.status === 'connected_lora';
      const result = await apiService.pingDevice(useLora);
      
      setCommandHistory(prev => [...prev, {
        command: 'PING',
        response: result.success ? 'PONG' : 'No response',
        timestamp: result.timestamp,
        via_lora: useLora
      }]);
    } catch (error) {
      console.error('Ping failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getTelemetryCard = (
    title: string, 
    value: number | undefined, 
    unit: string, 
    icon: React.ReactNode,
    colorClass: string = 'border-l-blue-500'
  ) => (
    <div className={`telemetry-card ${colorClass}`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-300">{title}</h3>
        {icon}
      </div>
      <div className="flex items-baseline">
        <span className="telemetry-value text-white">
          {value !== undefined ? value.toFixed(value < 10 ? 1 : 0) : '--'}
        </span>
        <span className="telemetry-unit">{unit}</span>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Real-time Flight Data</h2>
        <div className="flex space-x-3">
          {!isRecording ? (
            <button
              onClick={handleStartRecording}
              disabled={connectionStatus.status === 'disconnected'}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded-lg transition-colors"
            >
              <Play className="w-4 h-4" />
              <span>Start Recording</span>
            </button>
          ) : (
            <button
              onClick={handleStopRecording}
              className="flex items-center space-x-2 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
            >
              <Square className="w-4 h-4" />
              <span>Stop Recording</span>
            </button>
          )}
          
          <button
            onClick={handlePing}
            disabled={isLoading || connectionStatus.status === 'disconnected'}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg transition-colors"
          >
            <Activity className={`w-4 h-4 ${isLoading ? 'animate-pulse' : ''}`} />
            <span>Ping</span>
          </button>
        </div>
      </div>

      {/* Connection Status Alert */}
      {connectionStatus.status === 'disconnected' && (
        <div className="bg-yellow-900 border border-yellow-600 text-yellow-200 px-4 py-3 rounded-lg">
          <p>⚠️ Device not connected. Please connect via USB or LoRa Link to view telemetry data.</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Telemetry Dashboard */}
        <div className="space-y-6">
          <h3 className="text-lg font-semibold text-gray-300">Telemetry Data</h3>
          
          {/* Primary telemetry cards */}
          <div className="grid grid-cols-2 gap-4">
            {getTelemetryCard(
              'Altitude', 
              telemetryData?.altitude, 
              'm', 
              <Gauge className="w-5 h-5 text-blue-400" />,
              'altitude'
            )}
            {getTelemetryCard(
              'Velocity', 
              telemetryData?.velocity, 
              'm/s', 
              <Activity className="w-5 h-5 text-green-400" />,
              'velocity'
            )}
            {getTelemetryCard(
              'Battery', 
              telemetryData?.battery_voltage, 
              'V', 
              <Battery className="w-5 h-5 text-yellow-400" />,
              'battery'
            )}
            {getTelemetryCard(
              'RSSI', 
              telemetryData?.rssi, 
              'dBm', 
              <Radio className="w-5 h-5 text-purple-400" />,
              'signal'
            )}
          </div>

          {/* Recording Status */}
          {isRecording && (
            <div className="bg-green-900 border border-green-600 text-green-200 px-4 py-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                <span>Recording telemetry data...</span>
              </div>
              <p className="text-sm text-green-300 mt-1">
                Data is being logged to ~/GCH/logs/flight_{new Date().toISOString().split('T')[0]}.log
              </p>
            </div>
          )}

          {/* IMU Data */}
          {(telemetryData?.acceleration_x || telemetryData?.gyro_x) && (
            <div className="bg-dark-800 p-4 rounded-lg">
              <h4 className="text-md font-medium text-gray-300 mb-3">IMU Data</h4>
              <div className="space-y-3">
                {/* Acceleration */}
                {telemetryData?.acceleration_x !== undefined && (
                  <div>
                    <div className="text-sm text-gray-400 mb-1">Acceleration (m/s²)</div>
                    <div className="grid grid-cols-3 gap-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-red-400">X:</span>
                        <span className="font-mono text-white">
                          {telemetryData.acceleration_x.toFixed(2)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-green-400">Y:</span>
                        <span className="font-mono text-white">
                          {telemetryData.acceleration_y?.toFixed(2) || '--'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-blue-400">Z:</span>
                        <span className="font-mono text-white">
                          {telemetryData.acceleration_z?.toFixed(2) || '--'}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Gyroscope */}
                {telemetryData?.gyro_x !== undefined && (
                  <div>
                    <div className="text-sm text-gray-400 mb-1">Gyroscope (rad/s)</div>
                    <div className="grid grid-cols-3 gap-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-red-400">X:</span>
                        <span className="font-mono text-white">
                          {telemetryData.gyro_x.toFixed(3)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-green-400">Y:</span>
                        <span className="font-mono text-white">
                          {telemetryData.gyro_y?.toFixed(3) || '--'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-blue-400">Z:</span>
                        <span className="font-mono text-white">
                          {telemetryData.gyro_z?.toFixed(3) || '--'}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Secondary telemetry data */}
          <div className="bg-dark-800 p-4 rounded-lg">
            <h4 className="text-md font-medium text-gray-300 mb-3">Environmental Data</h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Thermometer className="w-4 h-4 text-orange-400" />
                  <span className="text-sm text-gray-300">Temperature</span>
                </div>
                <span className="font-mono text-white">
                  {telemetryData?.temperature !== undefined ? 
                    `${telemetryData.temperature.toFixed(1)}°C` : '--°C'
                  }
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Gauge className="w-4 h-4 text-cyan-400" />
                  <span className="text-sm text-gray-300">Pressure</span>
                </div>
                <span className="font-mono text-white">
                  {telemetryData?.pressure !== undefined ? 
                    `${telemetryData.pressure.toFixed(0)} Pa` : '-- Pa'
                  }
                </span>
              </div>
            </div>
          </div>

          {/* GPS Coordinates */}
          {(telemetryData?.latitude || telemetryData?.longitude) && (
            <div className="bg-dark-800 p-4 rounded-lg">
              <h4 className="text-md font-medium text-gray-300 mb-3 flex items-center">
                <MapPin className="w-4 h-4 mr-2" />
                GPS Coordinates
              </h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">Latitude</span>
                  <span className="font-mono text-white">
                    {telemetryData?.latitude !== undefined ? 
                      telemetryData.latitude.toFixed(6) : '--'
                    }°
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">Longitude</span>
                  <span className="font-mono text-white">
                    {telemetryData?.longitude !== undefined ? 
                      telemetryData.longitude.toFixed(6) : '--'
                    }°
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Command Interface */}
        <div className="space-y-6">
          <h3 className="text-lg font-semibold text-gray-300">Command Interface</h3>
          
          {/* Command Input */}
          <div className="bg-dark-800 p-4 rounded-lg">
            <h4 className="text-md font-medium text-gray-300 mb-3">Send Command</h4>
            <div className="flex space-x-2">
              <input
                type="text"
                value={command}
                onChange={(e) => setCommand(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendCommand()}
                placeholder="Enter command..."
                className="flex-1 px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <button
                onClick={handleSendCommand}
                disabled={isLoading || !command.trim() || connectionStatus.status === 'disconnected'}
                className="flex items-center space-x-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-600 rounded-lg transition-colors"
              >
                <Send className="w-4 h-4" />
                <span>Send</span>
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-2">
              Commands will be sent via {connectionStatus.status === 'connected_lora' ? 'LoRa Link' : 'USB'} connection
            </p>
          </div>

          {/* Command History */}
          <div className="bg-dark-800 p-4 rounded-lg">
            <h4 className="text-md font-medium text-gray-300 mb-3">Command History</h4>
            <div className="terminal max-h-64 overflow-y-auto">
              {commandHistory.length === 0 ? (
                <p className="text-gray-500 text-sm">No commands sent yet...</p>
              ) : (
                commandHistory.map((entry, index) => (
                  <div key={index} className="mb-2 text-sm">
                    <div className="text-gray-400">
                      [{new Date(entry.timestamp).toLocaleTimeString()}] 
                      {entry.via_lora ? ' [LoRa]' : ' [USB]'}
                    </div>
                    <div className="text-green-400">$ {entry.command}</div>
                    <div className="text-white ml-2">{entry.response || 'No response'}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FlightTab;
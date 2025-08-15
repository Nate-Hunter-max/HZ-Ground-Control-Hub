import React from 'react';
import { 
  Wifi, 
  WifiOff, 
  Radio, 
  Battery, 
  Signal, 
  Activity,
  Clock,
  AlertCircle
} from 'lucide-react';
import { ConnectionStatus, TelemetryData } from '../types';

interface StatusBarProps {
  connectionStatus: ConnectionStatus;
  telemetryData: TelemetryData | null;
  isLoading: boolean;
}

const StatusBar: React.FC<StatusBarProps> = ({ 
  connectionStatus, 
  telemetryData, 
  isLoading 
}) => {
  const formatTime = (dateString: string | null) => {
    if (!dateString) return '--:--:--';
    return new Date(dateString).toLocaleTimeString();
  };

  const getBatteryColor = (voltage?: number) => {
    if (!voltage) return 'text-gray-400';
    if (voltage > 3.7) return 'text-green-400';
    if (voltage > 3.3) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getSignalColor = (rssi?: number) => {
    if (!rssi) return 'text-gray-400';
    if (rssi > -70) return 'text-green-400';
    if (rssi > -85) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getConnectionStatusText = () => {
    switch (connectionStatus.status) {
      case 'connected_usb':
        return `USB Connected (${connectionStatus.port})`;
      case 'connected_lora':
        return `LoRa Connected (${connectionStatus.port})`;
      case 'disconnected':
        return 'Disconnected';
      case 'error':
        return 'Connection Error';
      default:
        return 'Unknown Status';
    }
  };

  const getConnectionIcon = () => {
    switch (connectionStatus.status) {
      case 'connected_usb':
        return <Wifi className="w-4 h-4 text-green-400" />;
      case 'connected_lora':
        return <Radio className="w-4 h-4 text-blue-400" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-400" />;
      default:
        return <WifiOff className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="bg-dark-800 border-t border-dark-700 px-6 py-3">
      <div className="flex items-center justify-between text-sm">
        {/* Left section - Connection status */}
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            {getConnectionIcon()}
            <span className="text-gray-300">{getConnectionStatusText()}</span>
            {isLoading && (
              <Activity className="w-4 h-4 text-blue-400 animate-pulse" />
            )}
          </div>
          
          {connectionStatus.last_seen && (
            <div className="flex items-center space-x-2 text-gray-400">
              <Clock className="w-4 h-4" />
              <span>Last seen: {formatTime(connectionStatus.last_seen)}</span>
            </div>
          )}
        </div>

        {/* Right section - Telemetry data */}
        <div className="flex items-center space-x-6">
          {/* Battery voltage */}
          <div className="flex items-center space-x-2">
            <Battery className={`w-4 h-4 ${getBatteryColor(telemetryData?.battery_voltage)}`} />
            <span className={getBatteryColor(telemetryData?.battery_voltage)}>
              {telemetryData?.battery_voltage ? 
                `${telemetryData.battery_voltage.toFixed(1)}V` : 
                '--.-V'
              }
            </span>
          </div>

          {/* RSSI */}
          <div className="flex items-center space-x-2">
            <Signal className={`w-4 h-4 ${getSignalColor(telemetryData?.rssi)}`} />
            <span className={getSignalColor(telemetryData?.rssi)}>
              {telemetryData?.rssi ? 
                `${telemetryData.rssi} dBm` : 
                '-- dBm'
              }
            </span>
          </div>

          {/* Altitude */}
          {telemetryData?.altitude !== undefined && (
            <div className="flex items-center space-x-2 text-blue-400">
              <span className="font-mono">
                ALT: {telemetryData.altitude.toFixed(0)}m
              </span>
            </div>
          )}

          {/* Velocity */}
          {telemetryData?.velocity !== undefined && (
            <div className="flex items-center space-x-2 text-green-400">
              <span className="font-mono">
                VEL: {telemetryData.velocity.toFixed(1)}m/s
              </span>
            </div>
          )}

          {/* Temperature */}
          {telemetryData?.temperature !== undefined && (
            <div className="flex items-center space-x-2 text-orange-400">
              <span className="font-mono">
                TEMP: {telemetryData.temperature.toFixed(1)}°C
              </span>
            </div>
          )}

          {/* Data timestamp */}
          {telemetryData?.timestamp && (
            <div className="flex items-center space-x-2 text-gray-400">
              <Clock className="w-4 h-4" />
              <span>Data: {formatTime(telemetryData.timestamp)}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StatusBar;
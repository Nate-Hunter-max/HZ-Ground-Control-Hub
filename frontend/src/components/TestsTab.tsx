import React, { useState } from 'react';
import { 
  Play, 
  TestTube2, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Activity
} from 'lucide-react';
import { ConnectionStatus, TestResult, SensorReading } from '../types';
import { apiService } from '../services/apiService.tsx';

interface TestsTabProps {
  connectionStatus: ConnectionStatus;
}

const TestsTab: React.FC<TestsTabProps> = ({ connectionStatus }) => {
  const [takeoffResult, setTakeoffResult] = useState<TestResult | null>(null);
  const [sensorReadings, setSensorReadings] = useState<SensorReading[]>([]);
  const [isRunningTest, setIsRunningTest] = useState<string | null>(null);

  const runTakeoffTest = async () => {
    setIsRunningTest('takeoff');
    try {
      const result = await apiService.testTakeoff();
      setTakeoffResult(result);
    } catch (error) {
      setTakeoffResult({
        test_name: 'takeoff',
        status: 'ERROR',
        message: `Test failed: ${error}`,
        timestamp: new Date().toISOString()
      });
    } finally {
      setIsRunningTest(null);
    }
  };

  const runPreflightTest = async () => {
    setIsRunningTest('preflight');
    try {
      const readings = await apiService.testPreflight();
      setSensorReadings(readings);
    } catch (error) {
      console.error('Pre-flight test failed:', error);
      setSensorReadings([]);
    } finally {
      setIsRunningTest(null);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'OK':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'FAIL':
        return <XCircle className="w-5 h-5 text-red-400" />;
      case 'ERROR':
        return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
      default:
        return <Activity className="w-5 h-5 text-gray-400" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Device Testing</h2>
      </div>

      {connectionStatus.status === 'disconnected' && (
        <div className="bg-yellow-900 border border-yellow-600 text-yellow-200 px-4 py-3 rounded-lg">
          <p>⚠️ Device not connected. Please connect via USB to run tests.</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Takeoff Test */}
        <div className="card">
          <h3 className="text-lg font-semibold text-blue-400 mb-4 flex items-center">
            <TestTube2 className="w-5 h-5 mr-2" />
            Takeoff Test
          </h3>
          <p className="text-gray-300 mb-4">
            Simulates pressure sensor changes to test launch detection system.
          </p>
          
          <button
            onClick={runTakeoffTest}
            disabled={connectionStatus.status === 'disconnected' || isRunningTest !== null}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg transition-colors mb-4"
          >
            <Play className={`w-4 h-4 ${isRunningTest === 'takeoff' ? 'animate-spin' : ''}`} />
            <span>{isRunningTest === 'takeoff' ? 'Running...' : 'Run Takeoff Test'}</span>
          </button>

          {takeoffResult && (
            <div className={`p-4 rounded-lg flex items-start space-x-3 ${
              takeoffResult.status === 'OK' ? 'bg-green-900 bg-opacity-50' :
              takeoffResult.status === 'FAIL' ? 'bg-red-900 bg-opacity-50' :
              'bg-yellow-900 bg-opacity-50'
            }`}>
              {getStatusIcon(takeoffResult.status)}
              <div>
                <div className="font-medium text-white">{takeoffResult.status}</div>
                <div className="text-sm text-gray-300">{takeoffResult.message}</div>
                <div className="text-xs text-gray-400">
                  {new Date(takeoffResult.timestamp).toLocaleString()}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Pre-flight Test */}
        <div className="card">
          <h3 className="text-lg font-semibold text-green-400 mb-4 flex items-center">
            <CheckCircle className="w-5 h-5 mr-2" />
            Pre-flight Test
          </h3>
          <p className="text-gray-300 mb-4">
            Comprehensive check of all sensors and systems before launch.
          </p>
          
          <button
            onClick={runPreflightTest}
            disabled={connectionStatus.status === 'disconnected' || isRunningTest !== null}
            className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded-lg transition-colors mb-4"
          >
            <Activity className={`w-4 h-4 ${isRunningTest === 'preflight' ? 'animate-spin' : ''}`} />
            <span>{isRunningTest === 'preflight' ? 'Testing...' : 'Run Pre-flight Test'}</span>
          </button>

          {sensorReadings.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium text-gray-300 mb-2">Sensor Status</h4>
              {sensorReadings.map((reading, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-dark-700 rounded">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(reading.status)}
                    <span className="text-white">{reading.sensor_name}</span>
                  </div>
                  <div className="text-right">
                    {reading.value !== null && (
                      <span className="text-gray-300 font-mono">
                        {reading.value} {reading.unit}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TestsTab;
import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  Plus, 
  FileText, 
  Download, 
  Upload,
  Trash2,
  Settings
} from 'lucide-react';
import { LogFile } from '../types';
import { apiService } from '../services/apiService.tsx';

const AnalysisTab: React.FC = () => {
  const [logFiles, setLogFiles] = useState<LogFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [charts, setCharts] = useState<any[]>([]);

  useEffect(() => {
    loadLogFiles();
  }, []);

  const loadLogFiles = async () => {
    try {
      const files = await apiService.listLogFiles();
      setLogFiles(files);
    } catch (error) {
      console.error('Failed to load log files:', error);
    }
  };

  const addChart = () => {
    const newChart = {
      id: `chart_${Date.now()}`,
      title: `Chart ${charts.length + 1}`,
      x_axis: 'timestamp',
      y1_axis: 'altitude',
      y2_axis: null,
      events: []
    };
    setCharts([...charts, newChart]);
  };

  const removeChart = (id: string) => {
    setCharts(charts.filter(chart => chart.id !== id));
  };

  const updateChart = (id: string, updates: any) => {
    setCharts(charts.map(chart => 
      chart.id === id ? { ...chart, ...updates } : chart
    ));
  };

  const availableFields = [
    'timestamp',
    'altitude',
    'velocity', 
    'battery_voltage',
    'rssi',
    'latitude',
    'longitude',
    'pressure',
    'temperature',
    'acceleration_x',
    'acceleration_y',
    'acceleration_z',
    'gyro_x',
    'gyro_y',
    'gyro_z'
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Data Analysis</h2>
        <div className="flex space-x-3">
          <button
            onClick={loadLogFiles}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <Upload className="w-4 h-4" />
            <span>Refresh Files</span>
          </button>
          
          <button
            onClick={addChart}
            className="flex items-center space-x-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Add Chart</span>
          </button>
        </div>
      </div>

      {/* Data Source Selection */}
      <div className="card">
        <h3 className="text-lg font-semibold text-blue-400 mb-4 flex items-center">
          <FileText className="w-5 h-5 mr-2" />
          Data Source
        </h3>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* File Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Select Log File
            </label>
            <select
              value={selectedFile}
              onChange={(e) => setSelectedFile(e.target.value)}
              className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">Select a log file...</option>
              {logFiles.map((file) => (
                <option key={file.path} value={file.path}>
                  {file.name} ({file.type.toUpperCase()}) - {(file.size / 1024).toFixed(1)} KB
                </option>
              ))}
            </select>
            
            {logFiles.length === 0 && (
              <p className="text-yellow-400 text-sm mt-2">
                No log files found. Check ~/GCH/logs/ directory.
              </p>
            )}
          </div>

          {/* Live Data Option */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Real-time Data
            </label>
            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="live-data"
                className="w-4 h-4 text-primary-600 bg-dark-700 border-dark-600 rounded focus:ring-primary-500"
              />
              <label htmlFor="live-data" className="text-gray-300">
                Use live telemetry data from connected device
              </label>
            </div>
            <p className="text-sm text-gray-400 mt-1">
              Charts will update in real-time when device is connected
            </p>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="space-y-6">
        {charts.length === 0 ? (
          <div className="card text-center py-12">
            <BarChart3 className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-400 mb-2">No Charts Created</h3>
            <p className="text-gray-500 mb-6">
              Create your first chart to start analyzing flight data
            </p>
            <button
              onClick={addChart}
              className="inline-flex items-center space-x-2 px-6 py-3 bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
            >
              <Plus className="w-5 h-5" />
              <span>Create Chart</span>
            </button>
          </div>
        ) : (
          charts.map((chart) => (
            <div key={chart.id} className="card">
              <div className="flex items-center justify-between mb-4">
                <input
                  type="text"
                  value={chart.title}
                  onChange={(e) => updateChart(chart.id, { title: e.target.value })}
                  className="text-lg font-semibold bg-transparent border-none text-white focus:outline-none focus:ring-2 focus:ring-primary-500 rounded px-2"
                  placeholder="Chart Title"
                />
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => {/* TODO: Export chart */}}
                    className="p-2 text-gray-400 hover:text-white transition-colors"
                    title="Export Chart"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => removeChart(chart.id)}
                    className="p-2 text-gray-400 hover:text-red-400 transition-colors"
                    title="Remove Chart"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Chart Configuration */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    X-Axis
                  </label>
                  <select
                    value={chart.x_axis}
                    onChange={(e) => updateChart(chart.id, { x_axis: e.target.value })}
                    className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    {availableFields.map(field => (
                      <option key={field} value={field}>{field}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Y1-Axis (Primary)
                  </label>
                  <select
                    value={chart.y1_axis}
                    onChange={(e) => updateChart(chart.id, { y1_axis: e.target.value })}
                    className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    {availableFields.map(field => (
                      <option key={field} value={field}>{field}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Y2-Axis (Secondary)
                  </label>
                  <select
                    value={chart.y2_axis || ''}
                    onChange={(e) => updateChart(chart.id, { y2_axis: e.target.value || null })}
                    className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="">None</option>
                    {availableFields.map(field => (
                      <option key={field} value={field}>{field}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Chart Display Area */}
              <div className="chart-container">
                <div className="flex items-center justify-center h-64 text-gray-400">
                  <div className="text-center">
                    <BarChart3 className="w-12 h-12 mx-auto mb-2" />
                    <p>Chart visualization will be implemented here</p>
                    <p className="text-sm">
                      {chart.x_axis} vs {chart.y1_axis}
                      {chart.y2_axis && ` & ${chart.y2_axis}`}
                    </p>
                  </div>
                </div>
              </div>

              {/* Events/Flags Section */}
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Event Flags
                </label>
                <div className="flex flex-wrap gap-2">
                  {chart.events?.map((event: string, index: number) => (
                    <span 
                      key={index}
                      className="px-3 py-1 bg-yellow-600 bg-opacity-20 text-yellow-400 rounded-full text-sm"
                    >
                      {event}
                    </span>
                  )) || (
                    <span className="text-gray-500 text-sm">No event flags defined</span>
                  )}
                </div>
                <button
                  onClick={() => {/* TODO: Add event flag */}}
                  className="mt-2 text-sm text-primary-400 hover:text-primary-300"
                >
                  + Add Event Flag
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Export Options */}
      {charts.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-green-400 mb-4">Export Options</h3>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => {/* TODO: Export as PNG */}}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              <Download className="w-4 h-4" />
              <span>Export as PNG</span>
            </button>
            
            <button
              onClick={() => {/* TODO: Export as SVG */}}
              className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
            >
              <Download className="w-4 h-4" />
              <span>Export as SVG</span>
            </button>
            
            <button
              onClick={() => {/* TODO: Export data as CSV */}}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
            >
              <FileText className="w-4 h-4" />
              <span>Export Data (CSV)</span>
            </button>

            <button
              onClick={() => {/* TODO: Save plot configuration */}}
              className="flex items-center space-x-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 rounded-lg transition-colors"
            >
              <Settings className="w-4 h-4" />
              <span>Save Plot Config</span>
            </button>
          </div>
          
          <p className="text-sm text-gray-400 mt-3">
            ℹ️ Export functionality will be implemented in a future version. 
            Files will be saved to ~/GCH/exports/
          </p>
        </div>
      )}
    </div>
  );
};

export default AnalysisTab;
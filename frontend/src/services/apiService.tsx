/**
 * API service for communicating with the Ground Control Hub backend
 */

import axios, { AxiosResponse } from 'axios';
import {
  DeviceConfig,
  ConnectionStatus,
  TestResult,
  SensorReading,
  CommandResponse,
  LogFile,
  ConfigFile,
  LoRaConfig
} from '../types';

const API_BASE_URL = process.env.NODE_ENV === 'production' ? '' : 'http://127.0.0.1:8000';

class ApiService {
  private baseURL = `${API_BASE_URL}/api`;

  constructor() {
    // Configure axios defaults
    axios.defaults.timeout = 10000; // 10 second timeout
    axios.defaults.headers.common['Content-Type'] = 'application/json';
  }

  // Device management
  async scanDevices(): Promise<{ device: string[], lora_link: string[] }> {
    const response = await axios.get(`${this.baseURL}/devices/scan`);
    return response.data;
  }

  async connectDevice(deviceType: 'device' | 'lora_link', port?: string): Promise<any> {
    const response = await axios.post(`${this.baseURL}/devices/connect`, null, {
      params: { device_type: deviceType, port }
    });
    return response.data;
  }

  async disconnectDevice(deviceType: 'device' | 'lora_link'): Promise<any> {
    const response = await axios.post(`${this.baseURL}/devices/disconnect`, null, {
      params: { device_type: deviceType }
    });
    return response.data;
  }

  async getDeviceStatus(): Promise<ConnectionStatus> {
    const response = await axios.get(`${this.baseURL}/devices/status`);
    return response.data;
  }

  async pingDevice(useLora: boolean = false): Promise<{ success: boolean, timestamp: string }> {
    const response = await axios.post(`${this.baseURL}/devices/ping`, null, {
      params: { use_lora: useLora }
    });
    return response.data;
  }

  // Configuration management
  async readDeviceConfig(): Promise<DeviceConfig> {
    const response = await axios.get(`${this.baseURL}/config/read`);
    return response.data;
  }

  async writeDeviceConfig(config: DeviceConfig): Promise<{ status: string, message: string }> {
    const response = await axios.post(`${this.baseURL}/config/write`, config);
    return response.data;
  }

  async loadConfigFile(filename: string): Promise<DeviceConfig> {
    const response = await axios.get(`${this.baseURL}/config/load/${filename}`);
    return response.data;
  }

  async saveConfigFile(filename: string, config: DeviceConfig): Promise<{ status: string, path: string }> {
    const response = await axios.post(`${this.baseURL}/config/save/${filename}`, config);
    return response.data;
  }

  async listConfigFiles(): Promise<ConfigFile[]> {
    const response = await axios.get(`${this.baseURL}/config/list`);
    return response.data;
  }

  // Testing
  async testTakeoff(): Promise<TestResult> {
    const response = await axios.post(`${this.baseURL}/tests/takeoff`);
    return response.data;
  }

  async testPreflight(): Promise<SensorReading[]> {
    const response = await axios.post(`${this.baseURL}/tests/preflight`);
    return response.data;
  }

  // Commands
  async sendCommand(command: string, useLora: boolean = false): Promise<CommandResponse> {
    const response = await axios.post(`${this.baseURL}/commands/send`, null, {
      params: { command, use_lora: useLora }
    });
    return response.data;
  }

  // LoRa Link specific
  async bindLoRaSatellite(): Promise<{ success: boolean, response?: string, timestamp: string }> {
    const response = await axios.post(`${this.baseURL}/lora/bind`);
    return response.data;
  }

  async readBlackboxViaLoRa(): Promise<{ success: boolean, data_size: number, file_path: string, timestamp: string }> {
    const response = await axios.post(`${this.baseURL}/lora/blackbox`);
    return response.data;
  }

  // File management
  async listLogFiles(): Promise<LogFile[]> {
    const response = await axios.get(`${this.baseURL}/files/logs`);
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{ status: string, timestamp: string, version: string }> {
    const response = await axios.get(`${this.baseURL}/health`);
    return response.data;
  }

  // WebSocket connection for real-time telemetry
  createTelemetryWebSocket(onMessage: (data: any) => void, onError?: (error: Event) => void): WebSocket {
    const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/api/ws/telemetry`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (onError) onError(error);
    };

    ws.onclose = () => {
      console.log('WebSocket connection closed');
    };

    return ws;
  }

  // Error handling helper
  private handleError(error: any): never {
    if (error.response) {
      // Server responded with error status
      throw new Error(`API Error: ${error.response.status} - ${error.response.data.detail || error.response.statusText}`);
    } else if (error.request) {
      // Request made but no response received
      throw new Error('Network Error: No response from server');
    } else {
      // Something else happened
      throw new Error(`Request Error: ${error.message}`);
    }
  }
}

export const apiService = new ApiService();
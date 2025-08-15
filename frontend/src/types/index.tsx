// TypeScript type definitions for Ground Control Hub

export interface LoRaConfig {
  frequency: number;
  bandwidth: number;
  spreading_factor: number;
  coding_rate: number;
  header_mode: number;
  crc_enabled: number;
  low_data_rate_optimize: number;
  preamble_length: number;
  payload_length: number;
  tx_power: number;
  tx_addr: number;
  rx_addr: number;
}

export interface SafeSettings {
  sd_filename: string;
  sd_filename_wq: string;
  data_period: number;
  data_period_lnd: number;
  press_buffer_len: number;
  press_land_delta: number;
}

export interface CriticalSettings {
  start_th: number;
  eject_th: number;
}

export interface DeviceConfig {
  safe_settings: SafeSettings;
  critical_settings: CriticalSettings;
  lora_config: LoRaConfig;
  created_at?: string;
  modified_at?: string;
  device_id?: string;
  firmware_version?: string;
}

export interface TelemetryData {
  timestamp: string;
  altitude?: number;
  velocity?: number;
  battery_voltage?: number;
  rssi?: number;
  latitude?: number;
  longitude?: number;
  pressure?: number;
  temperature?: number;
  acceleration_x?: number;
  acceleration_y?: number;
  acceleration_z?: number;
  gyro_x?: number;
  gyro_y?: number;
  gyro_z?: number;
}

export type DeviceStatus = 'disconnected' | 'connected_usb' | 'connected_lora' | 'error';

export interface ConnectionStatus {
  status: DeviceStatus;
  port: string | null;
  device_type: string | null;
  last_seen: string | null;
  signal_strength: number | null;
}

export interface TestResult {
  test_name: string;
  status: 'OK' | 'FAIL' | 'ERROR';
  message?: string;
  details?: Record<string, any>;
  timestamp: string;
}

export interface SensorReading {
  sensor_name: string;
  status: 'OK' | 'FAIL' | 'NO_DATA';
  value?: number;
  unit?: string;
  timestamp: string;
}

export interface CommandResponse {
  command: string;
  response?: string;
  timestamp: string;
  via_lora: boolean;
}

export interface LogFile {
  name: string;
  path: string;
  modified: number;
  size: number;
  type: string;
}

export interface ConfigFile {
  name: string;
  path: string;
  modified: number;
  size: number;
}

export interface PlotConfiguration {
  id: string;
  title: string;
  x_axis: string;
  y1_axis: string;
  y2_axis?: string;
  events?: string[];
  created_at: string;
}

export interface ApiResponse<T = any> {
  status: string;
  data?: T;
  message?: string;
  error?: string;
}

// WebSocket message types
export interface WebSocketMessage {
  type: 'telemetry' | 'status' | 'error';
  data: any;
  timestamp: string;
}

// Chart data types
export interface ChartDataPoint {
  timestamp: number;
  [key: string]: number | string;
}

export interface ChartSeries {
  name: string;
  data: ChartDataPoint[];
  color?: string;
  unit?: string;
}
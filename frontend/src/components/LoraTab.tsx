import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Radio,
  Send,
  Download,
  RefreshCw,
  Terminal,
  Satellite,
  ArrowDown,
  ArrowUp,
  Scroll,
  ScrollText,
  Circle,
  ChevronDown,
  Loader2
} from 'lucide-react';
import { ConnectionStatus } from '../types';
import { apiService } from '../services/apiService.tsx';

interface LoRaTabProps {
  connectionStatus: ConnectionStatus;
  onStatusChange: (status: ConnectionStatus) => void;
}

interface TerminalMessage {
  id: string;
  timestamp: Date;
  content: string;
  type: 'info' | 'command' | 'response' | 'error' | 'status';
}

interface WebSocketMessage {
  type: 'terminal_output' | 'command_response' | 'error' | 'status' | 'command_sent' | 'pong';
  content?: string;
  response?: string;
  message?: string;
  command?: string;
  timestamp: string;
}

interface LoRaDevice {
  port: string;
  name: string;
  version: string;
  displayName: string;
  isDetecting?: boolean;
}

const LoRaTab: React.FC<LoRaTabProps> = ({
  connectionStatus,
  onStatusChange
}) => {
  const [terminalInput, setTerminalInput] = useState('');
  const [terminalMessages, setTerminalMessages] = useState<TerminalMessage[]>([
    {
      id: '1',
      timestamp: new Date(),
      content: 'LoRa Link Terminal - Ready',
      type: 'info'
    },
    {
      id: '2',
      timestamp: new Date(),
      content: 'Type commands and press Enter to send...',
      type: 'info'
    }
  ]);
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [availablePorts, setAvailablePorts] = useState<string[]>([]);
  const [availableDevices, setAvailableDevices] = useState<LoRaDevice[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<LoRaDevice | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isBinding, setIsBinding] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [isReceivingData, setIsReceivingData] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [isScanningDevices, setIsScanningDevices] = useState(false);
  const [showDeviceDropdown, setShowDeviceDropdown] = useState(false);

  // Refs for terminal management
  const terminalEndRef = useRef<HTMLDivElement>(null);
  const terminalContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isReceivingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (autoScroll && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [terminalMessages, autoScroll]);

  // Initialize WebSocket connection for real-time data
  useEffect(() => {
    if (connectionStatus.device_type === 'lora_link') {
      initializeWebSocket();
    } else {
      closeWebSocket();
    }

    return () => closeWebSocket();
  }, [connectionStatus.device_type]);

  // Initial device scan
  useEffect(() => {
    scanForDevices();
  }, []);

  // Focus input when connected
  useEffect(() => {
    if (connectionStatus.device_type === 'lora_link' && inputRef.current) {
      inputRef.current.focus();
    }
  }, [connectionStatus.device_type]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDeviceDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Initialize WebSocket for real-time terminal updates
  const initializeWebSocket = useCallback(() => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    setWsStatus('connecting');

    try {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${process.env.REACT_APP_WS_PROTOCOL}://${process.env.REACT_APP_API_HOST}/api/ws/lora-terminal`;

      websocketRef.current = new WebSocket(wsUrl);
      websocketRef.current.onopen = () => {
        setWsConnected(true);
        setWsStatus('connected');
        reconnectAttemptsRef.current = 0;

        // Start ping interval
        startPingInterval();
      };

      websocketRef.current.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.warn('Failed to parse WebSocket message:', error);
          // Handle plain text messages as fallback
          addTerminalMessage(event.data, 'response');
        }
      };

      websocketRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsConnected(false);
        setWsStatus('error');
        addTerminalMessage('WebSocket connection error', 'error');
      };

      websocketRef.current.onclose = (event) => {
        setWsConnected(false);
        setWsStatus('disconnected');
        stopPingInterval();

        if (event.code === 1000) {
          addTerminalMessage('WebSocket disconnected', 'info');
        } else {
          addTerminalMessage(`WebSocket disconnected unexpectedly (code: ${event.code})`, 'error');

          // Attempt to reconnect if connection was not closed intentionally
          if (connectionStatus.device_type === 'lora_link') {
            attemptReconnect();
          }
        }
      };
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
      setWsStatus('error');
      addTerminalMessage(`WebSocket initialization failed: ${error}`, 'error');
    }
  }, [connectionStatus.device_type]);

  // Start ping interval to keep connection alive
  const startPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }

    pingIntervalRef.current = setInterval(() => {
      if (websocketRef.current?.readyState === WebSocket.OPEN) {
        websocketRef.current.send(JSON.stringify({
          type: 'ping',
          timestamp: new Date().toISOString()
        }));
      }
    }, 30000); // Ping every 30 seconds
  }, []);

  // Stop ping interval
  const stopPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

  // Attempt to reconnect WebSocket
  const attemptReconnect = useCallback(() => {
    if (reconnectAttemptsRef.current >= 5) {
      addTerminalMessage('Max reconnection attempts reached. Please reconnect manually.', 'error');
      setWsStatus('error');
      return;
    }

    const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
    reconnectAttemptsRef.current++;

    addTerminalMessage(`Reconnecting in ${delay/1000}s (attempt ${reconnectAttemptsRef.current}/5)...`, 'info');

    reconnectTimeoutRef.current = setTimeout(() => {
      if (connectionStatus.device_type === 'lora_link') {
        initializeWebSocket();
      }
    }, delay);
  }, [connectionStatus.device_type, initializeWebSocket]);

  // Close WebSocket connection
  const closeWebSocket = useCallback(() => {
    stopPingInterval();

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (websocketRef.current && websocketRef.current.readyState !== WebSocket.CLOSED) {
      websocketRef.current.close(1000, 'Component unmounting');
    }

    websocketRef.current = null;
    setWsConnected(false);
    setWsStatus('disconnected');
  }, [stopPingInterval]);

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = useCallback((data: WebSocketMessage) => {
    // Set receiving indicator
    setIsReceivingData(true);

    // Clear any existing timeout
    if (isReceivingTimeoutRef.current) {
      clearTimeout(isReceivingTimeoutRef.current);
    }

    // Handle different message types
    switch (data.type) {
      case 'terminal_output':
        if (data.content && data.content.trim()) {
          addTerminalMessage(data.content, 'response');
        }
        break;

      case 'command_response':
        if (data.response && data.response.trim()) {
          addTerminalMessage(data.response, 'response');
        }
        break;

      case 'command_sent':
        if (data.command) {
          addTerminalMessage(`> ${data.command}`, 'command');
        }
        break;

      case 'error':
        if (data.message) {
          addTerminalMessage(data.message, 'error');
        }
        break;

      case 'status':
        if (data.message) {
          addTerminalMessage(data.message, 'status');
        }
        break;

      case 'pong':
        // Silent handling of pong responses
        console.debug('Received pong from server');
        break;

      default:
        console.warn('Unknown WebSocket message type:', data.type);
        addTerminalMessage(JSON.stringify(data), 'response');
    }

    // Reset receiving indicator after a short delay
    isReceivingTimeoutRef.current = setTimeout(() => {
      setIsReceivingData(false);
    }, 1000);
  }, []);

  // Add new message to terminal
  const addTerminalMessage = useCallback((content: string, type: TerminalMessage['type'] = 'info') => {
    if (!content || !content.trim()) return;

    const newMessage: TerminalMessage = {
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      timestamp: new Date(),
      content: content.trim(),
      type
    };

    setTerminalMessages(prev => {
      // Keep terminal history manageable (max 1000 messages)
      const updated = [...prev, newMessage];
      return updated.length > 1000 ? updated.slice(-1000) : updated;
    });
  }, []);

  // Get device name by sending '4\n' command
  const getDeviceName = async (port: string): Promise<{ name: string; version: string } | null> => {
    try {
      const response = await apiService.getDeviceInfo(port);

      // Parse response like 'v1.0.0 Name\n'
      const match = response.match(/^v(\d+\.\d+\.\d+)\s+(.+)$/);
      if (match) {
        return {
          version: match[1],
          name: match[2].trim()
        };
      }

      // Fallback for unknown format
      return {
        version: '0.0.0',
        name: `Unknown`
      };
    } catch (error) {
      addTerminalMessage(`Failed to get device info for ${port}: ${error}`, 'error');
      return {
        version: '0.0.0',
        name: `Unknown`
      };
    }
  };

  // Scan for available LoRa devices and get their names
  const scanForDevices = async () => {
    setIsScanningDevices(true);
    addTerminalMessage('Scanning for LoRa Link devices...', 'info');

    try {
      const devices = await apiService.scanDevices();
      const ports = devices.lora_link || [];
      setAvailablePorts(ports);

      if (ports.length === 0) {
        setAvailableDevices([]);
        addTerminalMessage('No LoRa Link devices found', 'info');
        return;
      }

      addTerminalMessage(`Found ${ports.length} device(s), detecting names...`, 'info');

      // Create initial device objects
      const initialDevices: LoRaDevice[] = ports.map(port => ({
        port,
        name: '',
        version: '',
        displayName: `Detecting... (${port})`,
        isDetecting: true
      }));

      setAvailableDevices(initialDevices);

      // Get device names in parallel
      const devicePromises = ports.map(async (port, index) => {
        try {
          const deviceInfo = await getDeviceName(port);
          const device: LoRaDevice = {
            port,
            name: deviceInfo?.name || `LoRa Link ${port}`,
            version: deviceInfo?.version || '1.0.0',
            displayName: `v${deviceInfo?.version || '1.0.0'} ${deviceInfo?.name || 'LoRa Link'} (${port})`,
            isDetecting: false
          };

          // Update specific device in the array
          setAvailableDevices(prev => {
            const updated = [...prev];
            updated[index] = device;
            return updated;
          });

          return device;
        } catch (error) {
          console.warn(`Failed to detect device ${port}:`, error);
          const device: LoRaDevice = {
            port,
            name: `LoRa Link ${port}`,
            version: '1.0.0',
            displayName: `v1.0.0 LoRa Link (${port})`,
            isDetecting: false
          };

          setAvailableDevices(prev => {
            const updated = [...prev];
            updated[index] = device;
            return updated;
          });

          return device;
        }
      });

      await Promise.all(devicePromises);
      addTerminalMessage(`Device detection completed`, 'status');

    } catch (error) {
      console.error('Failed to scan for devices:', error);
      addTerminalMessage(`Device scan failed: ${error}`, 'error');
      setAvailableDevices([]);
    } finally {
      setIsScanningDevices(false);
    }
  };

  // Connect to selected LoRa Link device
  const connectToLoRa = async (device?: LoRaDevice) => {
    const targetDevice = device || selectedDevice;
    if (!targetDevice) {
      addTerminalMessage('Please select a device first', 'error');
      return;
    }

    setIsConnecting(true);
    try {
      await apiService.connectDevice('lora_link', targetDevice.port);
      const status = await apiService.getDeviceStatus();
      onStatusChange(status);

      addTerminalMessage(`Connected to ${targetDevice.displayName}`, 'status');
    } catch (error) {
      addTerminalMessage(`Connection failed: ${error}`, 'error');
    } finally {
      setIsConnecting(false);
    }
  };

  // Disconnect from LoRa Link
  const disconnectLoRa = async () => {
    try {
      await apiService.disconnectDevice('lora_link');
      const status = await apiService.getDeviceStatus();
      onStatusChange(status);

      addTerminalMessage('Disconnected from LoRa Link', 'status');
      setSelectedDevice(null);
    } catch (error) {
      addTerminalMessage(`Disconnect failed: ${error}`, 'error');
    }
  };

  // Send command to LoRa Link
  const sendCommand = async () => {
    if (!terminalInput.trim()) return;

    const command = terminalInput.trim();

    // Add to command history
    setCommandHistory(prev => {
      const newHistory = [command, ...prev.filter(cmd => cmd !== command)];
      return newHistory.slice(0, 50); // Keep last 50 commands
    });

    // Reset history index
    setHistoryIndex(-1);

    // Clear input immediately
    setTerminalInput('');

    try {
      // Send via WebSocket if connected, otherwise use HTTP API
      if (wsConnected && websocketRef.current?.readyState === WebSocket.OPEN) {
        websocketRef.current.send(JSON.stringify({
          type: 'command',
          command: command,
          timestamp: new Date().toISOString()
        }));
      } else {
        // Fallback to HTTP API
        addTerminalMessage(`> ${command}`, 'command');
        const response = await apiService.sendCommand(command, true);

        if (response.response) {
          addTerminalMessage(response.response, 'response');
        }
      }
    } catch (error) {
      addTerminalMessage(`Error: ${error}`, 'error');
    }
  };

  // Handle keyboard navigation for command history
  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      sendCommand();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (commandHistory.length > 0) {
        const newIndex = Math.min(historyIndex + 1, commandHistory.length - 1);
        setHistoryIndex(newIndex);
        setTerminalInput(commandHistory[newIndex]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1;
        setHistoryIndex(newIndex);
        setTerminalInput(commandHistory[newIndex]);
      } else if (historyIndex === 0) {
        setHistoryIndex(-1);
        setTerminalInput('');
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setTerminalInput('');
      setHistoryIndex(-1);
    }
  }, [historyIndex, commandHistory, sendCommand]);

  // Handle device selection
  const handleDeviceSelect = (device: LoRaDevice) => {
    setSelectedDevice(device);
    setShowDeviceDropdown(false);
  };

  // Bind satellite command
  const bindSatellite = async () => {
    setIsBinding(true);
    addTerminalMessage('Binding satellite...', 'info');

    try {
      const result = await apiService.bindLoRaSatellite();
      addTerminalMessage(
        result.success ? 'Satellite bound successfully' : 'Binding failed',
        result.success ? 'status' : 'error'
      );
    } catch (error) {
      addTerminalMessage(`Binding error: ${error}`, 'error');
    } finally {
      setIsBinding(false);
    }
  };

  // Read blackbox data
  const readBlackbox = async () => {
    addTerminalMessage('Reading blackbox data...', 'info');

    try {
      const result = await apiService.readBlackboxViaLoRa();
      addTerminalMessage(
        `Blackbox read successfully: ${result.data_size} bytes saved to ${result.file_path}`,
        'status'
      );
    } catch (error) {
      addTerminalMessage(`Blackbox read failed: ${error}`, 'error');
    }
  };

  // Toggle auto-scroll
  const toggleAutoScroll = () => {
    setAutoScroll(prev => !prev);
  };

  // Clear terminal
  const clearTerminal = () => {
    setTerminalMessages([{
      id: Date.now().toString(),
      timestamp: new Date(),
      content: 'Terminal cleared',
      type: 'info'
    }]);
  };

  // Get message style based on type
  const getMessageStyle = (type: TerminalMessage['type']) => {
    switch (type) {
      case 'command':
        return 'text-cyan-400 font-semibold';
      case 'response':
        return 'text-green-300';
      case 'error':
        return 'text-red-400';
      case 'status':
        return 'text-blue-400';
      case 'info':
      default:
        return 'text-gray-300';
    }
  };

  // Get WebSocket status indicator
  const getWsStatusIndicator = () => {
    switch (wsStatus) {
      case 'connected':
        return <Circle className="w-3 h-3 text-green-500 fill-current" />;
      case 'connecting':
        return <Circle className="w-3 h-3 text-yellow-500 fill-current animate-pulse" />;
      case 'error':
        return <Circle className="w-3 h-3 text-red-500 fill-current" />;
      default:
        return <Circle className="w-3 h-3 text-gray-500 fill-current" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">LoRa Link Interface</h2>
        <button
          onClick={scanForDevices}
          disabled={isScanningDevices}
          className="flex items-center space-x-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-500 rounded-lg transition-colors"
        >
          {isScanningDevices ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
          <span>{isScanningDevices ? 'Scanning...' : 'Scan Devices'}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Connection Panel */}
        <div className="card">
          <h3 className="text-lg font-semibold text-blue-400 mb-4 flex items-center">
            <Radio className="w-5 h-5 mr-2" />
            Connection
            <div className="ml-auto flex items-center space-x-2">
              {wsConnected && (
                <span className="px-2 py-1 bg-green-600 text-xs rounded">
                  WS
                </span>
              )}
              {getWsStatusIndicator()}
            </div>
          </h3>

          {/* Device Selection Dropdown */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Select LoRa Link Device:
            </label>

            {availableDevices.length === 0 && !isScanningDevices ? (
              <div className="text-yellow-400 mb-4 p-3 bg-yellow-900/20 border border-yellow-700 rounded-lg">
                ⚠️ No LoRa Link devices found. Make sure device is connected via USB.
              </div>
            ) : (
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setShowDeviceDropdown(!showDeviceDropdown)}
                  disabled={availableDevices.length === 0 || connectionStatus.device_type === 'lora_link'}
                  className="w-full flex items-center justify-between px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white hover:bg-dark-600 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
                >
                  <span className="truncate">
                    {selectedDevice?.displayName || 'Select a device...'}
                  </span>
                  <ChevronDown className={`w-4 h-4 transition-transform ${showDeviceDropdown ? 'rotate-180' : ''}`} />
                </button>

                {showDeviceDropdown && (
                  <div className="absolute z-10 w-full mt-1 bg-dark-700 border border-dark-600 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {availableDevices.map((device, index) => (
                      <button
                        key={device.port}
                        onClick={() => handleDeviceSelect(device)}
                        disabled={device.isDetecting}
                        className="w-full px-3 py-2 text-left hover:bg-dark-600 disabled:cursor-not-allowed flex items-center justify-between group transition-colors"
                      >
                        <span className={`truncate ${device.isDetecting ? 'text-gray-400' : 'text-white'}`}>
                          {device.displayName}
                        </span>
                        {device.isDetecting && (
                          <Loader2 className="w-4 h-4 animate-spin text-blue-400 flex-shrink-0 ml-2" />
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Device Info */}
            {selectedDevice && !selectedDevice.isDetecting && (
              <div className="mt-2 p-2 bg-dark-700 rounded border border-dark-600">
                <div className="text-sm text-gray-300">
                  <div><strong>Name:</strong> {selectedDevice.name}</div>
                  <div><strong>Version:</strong> v{selectedDevice.version}</div>
                  <div><strong>Port:</strong> {selectedDevice.port}</div>
                </div>
              </div>
            )}
          </div>

          {connectionStatus.device_type !== 'lora_link' ? (
            <button
              onClick={() => connectToLoRa()}
              disabled={isConnecting || !selectedDevice || selectedDevice.isDetecting}
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

        {/* Enhanced Terminal */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-green-400 flex items-center">
              <Terminal className="w-5 h-5 mr-2" />
              Terminal
              {isReceivingData && (
                <span className="ml-2 px-2 py-1 bg-green-600 text-xs rounded animate-pulse">
                  RX
                </span>
              )}
            </h3>

            {/* Terminal Controls */}
            <div className="flex space-x-2">
              <button
                onClick={toggleAutoScroll}
                className={`p-2 rounded ${autoScroll
                  ? 'bg-green-600 hover:bg-green-700'
                  : 'bg-gray-600 hover:bg-gray-700'
                } transition-colors`}
                title={autoScroll ? 'Disable auto-scroll' : 'Enable auto-scroll'}
              >
                {autoScroll ? <Scroll className="w-4 h-4" /> : <ScrollText className="w-4 h-4" />}
              </button>

              <button
                onClick={clearTerminal}
                className="p-2 bg-red-600 hover:bg-red-700 rounded transition-colors"
                title="Clear terminal"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Terminal Display */}
          <div
            ref={terminalContainerRef}
            className="terminal h-64 mb-4 overflow-y-auto"
          >
            {terminalMessages.map((message) => (
              <div key={message.id} className="mb-1 flex">
                <span className="text-gray-500 text-xs mr-2 mt-0.5 min-w-max">
                  {message.timestamp.toLocaleTimeString()}
                </span>
                <span className={getMessageStyle(message.type)}>
                  {message.content}
                </span>
              </div>
            ))}
            <div ref={terminalEndRef} />
          </div>

          {/* Terminal Input */}
          <div className="space-y-2">
            <div className="flex space-x-2">
              <span className="text-green-400 font-mono">$</span>
              <input
                ref={inputRef}
                type="text"
                value={terminalInput}
                onChange={(e) => setTerminalInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={connectionStatus.device_type !== 'lora_link'}
                placeholder="Enter command... (↑↓ for history, ESC to clear)"
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

            {/* Status and Help */}
            <div className="flex justify-between text-xs text-gray-400">
              <span>
                {connectionStatus.device_type === 'lora_link'
                  ? `Terminal connected${wsConnected ? ' (WebSocket)' : ' (HTTP)'} - ready for commands`
                  : 'Connect to LoRa Link to use terminal'
                }
              </span>
              <span>
                History: {commandHistory.length} | Auto-scroll: {autoScroll ? 'ON' : 'OFF'} | WS: {wsStatus}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* LoRa Settings Panel */}
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
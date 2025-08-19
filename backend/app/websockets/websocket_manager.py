"""
WebSocket manager for handling real-time LoRa Link communications
"""

import asyncio
import concurrent.futures
import json
import logging
import time
from datetime import datetime
from threading import Thread, Event
from typing import Set, Dict, Any, Optional

from fastapi import WebSocket, WebSocketDisconnect

from ..services.serial_service import serial_service

logger = logging.getLogger(__name__)


class LoRaWebSocketManager:
    """Manager for LoRa Link WebSocket connections and real-time data streaming"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.is_streaming = False
        self.stream_thread: Optional[Thread] = None
        self.stop_event = Event()
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)

        # Store the main event loop
        if self._main_loop is None:
            self._main_loop = asyncio.get_event_loop()

        # Send connection confirmation
        await self.send_to_client(websocket, {
            "type": "status",
            "message": "LoRa terminal WebSocket connected",
            "timestamp": datetime.now().isoformat(),
            "connection_count": len(self.active_connections)
        })

        # Start streaming if this is the first connection
        if len(self.active_connections) == 1:
            self.start_streaming()

        logger.info(f"LoRa WebSocket client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        self.active_connections.discard(websocket)
        logger.info(f"LoRa WebSocket client disconnected. Remaining: {len(self.active_connections)}")

        # Stop streaming if no connections remain
        if len(self.active_connections) == 0:
            self.stop_streaming()

    def start_streaming(self):
        """Start the data streaming thread"""
        if self.is_streaming:
            return

        self.is_streaming = True
        self.stop_event.clear()

        self.stream_thread = Thread(
            target=self._streaming_worker,
            daemon=True,
            name="LoRaWebSocketStreamer"
        )
        self.stream_thread.start()

        logger.info("Started LoRa WebSocket streaming")

    def stop_streaming(self):
        """Stop the data streaming thread"""
        if not self.is_streaming:
            return

        self.is_streaming = False
        self.stop_event.set()

        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2.0)

        logger.info("Stopped LoRa WebSocket streaming")

    def _streaming_worker(self):
        """Worker thread that polls for LoRa data and sends to clients"""
        logger.info("LoRa streaming worker started")

        while self.is_streaming and not self.stop_event.is_set():
            try:
                # Check for LoRa data using the queue-based approach
                if serial_service.has_lora_data():
                    lora_data = serial_service.get_lora_data()
                    if lora_data and self.active_connections:
                        logger.debug(f"Broadcasting LoRa data: {lora_data}")
                        # Schedule the broadcast in the main event loop
                        if self._main_loop and not self._main_loop.is_closed():
                            future = asyncio.run_coroutine_threadsafe(
                                self.broadcast(lora_data),
                                self._main_loop
                            )
                            try:
                                # Wait for the broadcast to complete with timeout
                                future.result(timeout=1.0)
                            except Exception as e:
                                logger.error(f"Error broadcasting LoRa data: {e}")

                # Small delay to prevent excessive CPU usage
                time.sleep(0.01)  # Reduced delay for more responsive updates

            except Exception as e:
                logger.error(f"Error in LoRa streaming worker: {e}")
                time.sleep(1.0)

        logger.info("LoRa streaming worker stopped")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            logger.debug("No active connections to broadcast to")
            return

        message_text = json.dumps(message)
        disconnected = set()

        logger.debug(f"Broadcasting to {len(self.active_connections)} clients: {message}")

        # Send to all clients
        for websocket in self.active_connections.copy():
            try:
                await websocket.send_text(message_text)
                logger.debug(f"Successfully sent message to WebSocket client")
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket client: {e}")
                disconnected.add(websocket)

        # Remove disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)

    async def send_to_client(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific client"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning(f"Failed to send to specific WebSocket client: {e}")
            self.disconnect(websocket)

    async def send_command_notification(self, command: str):
        """Notify all clients about a command being sent"""
        await self.broadcast({
            "type": "command_sent",
            "command": command,
            "timestamp": datetime.now().isoformat()
        })

    async def send_status_update(self, message: str, status_type: str = "info"):
        """Send status update to all clients"""
        await self.broadcast({
            "type": "status",
            "message": message,
            "status_type": status_type,
            "timestamp": datetime.now().isoformat()
        })

    async def send_error(self, error_message: str):
        """Send error message to all clients"""
        await self.broadcast({
            "type": "error",
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        })

    async def handle_client_message(self, websocket: WebSocket, data: str):
        """Handle incoming message from client"""
        try:
            message = json.loads(data)
            message_type = message.get("type", "unknown")

            if message_type == "ping":
                # Respond to ping
                await self.send_to_client(websocket, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

            elif message_type == "get_status":
                # Send current status
                connection_info = serial_service.get_connection_status()
                await self.send_to_client(websocket, {
                    "type": "status_response",
                    "connection_status": {
                        "device_type": connection_info.device_type,
                        "port": connection_info.port,
                        "status": connection_info.status.value,
                        "last_seen": connection_info.last_seen.isoformat() if connection_info.last_seen else None
                    },
                    "timestamp": datetime.now().isoformat()
                })

            elif message_type == "command":
                # Handle command from client
                command = message.get("command", "").strip()
                if command:
                    # Send command via serial service
                    response = serial_service.send_command(command, use_lora=True)

                    # Notify all clients about the command
                    await self.send_command_notification(command)

                    # Send response if available immediately
                    if response:
                        await self.broadcast({
                            "type": "command_response",
                            "command": command,
                            "response": response,
                            "timestamp": datetime.now().isoformat()
                        })

            else:
                logger.warning(f"Unknown message type from client: {message_type}")

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from WebSocket client: {data}")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)

    def is_active(self) -> bool:
        """Check if manager has active connections"""
        return len(self.active_connections) > 0

    def __del__(self):
        """Cleanup on destruction"""
        self.stop_streaming()
        if self._executor:
            self._executor.shutdown(wait=False)


# Global WebSocket manager instance
lora_websocket_manager = LoRaWebSocketManager()


# Enhanced WebSocket endpoint
async def websocket_lora_terminal_enhanced(websocket: WebSocket):
    """Enhanced WebSocket endpoint for LoRa terminal with full bidirectional communication"""
    try:
        # Connect client
        await lora_websocket_manager.connect(websocket)

        # Handle messages from client
        while True:
            try:
                # Wait for message from client with timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=35.0)
                await lora_websocket_manager.handle_client_message(websocket, data)

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({
                    "type": "info",
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        logger.info("LoRa WebSocket client disconnected normally")
    except Exception as e:
        logger.error(f"LoRa WebSocket error: {e}")
    finally:
        # Always clean up the connection
        lora_websocket_manager.disconnect(websocket)

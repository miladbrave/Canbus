"""
CAN Bus Reader - OOP Implementation
Project: CAN Bus Communication Library
"""

import time
import threading
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

try:
    import can
    from can import Message, Bus, Notifier
    from can.interfaces.socketcan import SocketcanBus
    CAN_AVAILABLE = True
except ImportError:
    CAN_AVAILABLE = False


class CANMessageType(Enum):
    """Enumeration for CAN message types."""
    STANDARD = "standard"
    EXTENDED = "extended"
    REMOTE = "remote"
    ERROR = "error"
    OVERLOAD = "overload"


@dataclass
class CANMessage:
    """Data class for CAN message configuration."""
    can_id: int
    data: List[int]
    message_type: CANMessageType
    name: str
    description: str
    dlc: int = 8
    is_rx: bool = True
    is_tx: bool = False
    timestamp: Optional[float] = None
    channel: str = "can0"


@dataclass
class CANFilter:
    """Data class for CAN message filter configuration."""
    can_id: int
    can_mask: int
    extended: bool = False


class SimpleLogger:
    """Simple logger for CAN bus reader."""
    
    def __init__(self, log_level: int = 0):
        """
        Initialize logger.
        
        Args:
            log_level: Log level (0=info, 1=warning, 2=error)
        """
        self.log_level = log_level
    
    def log(self, data: Any, log_type: int = 0, visibility: str = "TD", tag: str = "CANBusReader") -> None:
        """
        Log a message.
        
        Args:
            data: Data to log
            log_type: Type of log (0=info, 1=warning, 2=error)
            visibility: Visibility level
            tag: Tag for the log
        """
        if log_type >= self.log_level:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            level_str = {0: "INFO", 1: "WARNING", 2: "ERROR"}.get(log_type, "INFO")
            print(f"[{timestamp}] [{level_str}] [{tag}] {data}")


class CANBusReader:
    """
    OOP wrapper for CAN bus communication.
    
    This class provides a clean, object-oriented interface for CAN bus
    communication with message reading, writing, and monitoring capabilities.
    """
    
    def __init__(
        self,
        interface: str = "socketcan",
        channel: str = "can0",
        bitrate: int = 500000,
        timeout: float = 1.0,
        fd: bool = False,
        data_bitrate: int = 2000000,
        app_name: str = "canbus_reader",
        serial: Optional[str] = None,
        hw_type: Optional[str] = None,
        rx_own_msgs: bool = False,
        fd_data_bitrate: Optional[int] = None,
        log_errors: bool = True,
        error_filters: Optional[List[Dict[str, Any]]] = None,
        serial_number: Optional[str] = None,
        can_filters: Optional[List[Dict[str, Any]]] = None,
        logger: Optional[SimpleLogger] = None,
        **kwargs
    ):
        """
        Initialize CAN Bus Reader.
        
        Args:
            interface: CAN interface type (socketcan, pcan, vector, etc.)
            channel: CAN channel name
            bitrate: CAN bus bitrate in bits per second
            timeout: Read timeout in seconds
            fd: Enable CAN FD support
            data_bitrate: CAN FD data bitrate
            app_name: Application name
            serial: Serial number for USB adapters
            hw_type: Hardware type
            rx_own_msgs: Receive own messages
            fd_data_bitrate: CAN FD data bitrate
            log_errors: Log error messages
            error_filters: Error message filters
            serial_number: Serial number
            can_filters: CAN message filters
            logger: Logger instance
            **kwargs: Additional interface-specific parameters
        """
        if not CAN_AVAILABLE:
            raise ImportError("CAN library (python-can) is not available. Install with: pip install python-can")
        
        self.interface = interface
        self.channel = channel
        self.bitrate = bitrate
        self.timeout = timeout
        self.fd = fd
        self.data_bitrate = data_bitrate
        self.app_name = app_name
        self.serial = serial
        self.hw_type = hw_type
        self.rx_own_msgs = rx_own_msgs
        self.fd_data_bitrate = fd_data_bitrate
        self.log_errors = log_errors
        self.error_filters = error_filters or []
        self.serial_number = serial_number
        self.can_filters = can_filters or []
        
        self.logger = logger or SimpleLogger()
        
        # CAN bus objects
        self.bus: Optional[Bus] = None
        self.notifier: Optional[Notifier] = None
        self.is_connected = False
        self.last_read_time: Optional[float] = None
        
        # Message configuration
        self.messages: Dict[str, CANMessage] = {}
        self.message_queue: List[Message] = []
        
        # Filter configuration
        self.filters: List[CANFilter] = []
        
        # Statistics
        self.stats = {
            "total_messages": 0,
            "received_messages": 0,
            "transmitted_messages": 0,
            "error_messages": 0,
            "filtered_messages": 0,
            "connection_errors": 0,
            "last_error": None
        }
        
        # Health monitoring
        self.last_health_check: Optional[float] = None
        self.health_status = "unknown"
        self.health_monitor_thread: Optional[threading.Thread] = None
        self.health_monitor_running = False
        
        # Message monitoring
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitor_running = False
        self.monitor_callback: Optional[callable] = None
        
        # Start health monitoring
        self._start_health_monitor()
    
    def add_message(self, can_message: CANMessage) -> None:
        """
        Add a CAN message configuration.
        
        Args:
            can_message: CAN message configuration
        """
        self.messages[can_message.name] = can_message
        
        self.logger.log(
            data=f"Added CAN message: {can_message.name} (ID: 0x{can_message.can_id:X})",
            log_type=0,
            visibility="TD",
            tag="CANBusReader"
        )
    
    def add_messages(self, can_messages: List[CANMessage]) -> None:
        """
        Add multiple CAN message configurations.
        
        Args:
            can_messages: List of CAN message configurations
        """
        for can_message in can_messages:
            self.add_message(can_message)
    
    def add_filter(self, can_id: int, can_mask: int, extended: bool = False) -> None:
        """
        Add a CAN message filter.
        
        Args:
            can_id: CAN identifier
            can_mask: CAN mask
            extended: Whether this is an extended ID filter
        """
        filter_obj = CANFilter(can_id, can_mask, extended)
        self.filters.append(filter_obj)
        
        self.logger.log(
            data=f"Added filter: ID=0x{can_id:X}, Mask=0x{can_mask:X}, Extended={extended}",
            log_type=0,
            visibility="TD",
            tag="CANBusReader"
        )
    
    def remove_filter(self, can_id: int, can_mask: int, extended: bool = False) -> None:
        """
        Remove a CAN message filter.
        
        Args:
            can_id: CAN identifier
            can_mask: CAN mask
            extended: Whether this is an extended ID filter
        """
        self.filters = [f for f in self.filters 
                       if not (f.can_id == can_id and f.can_mask == can_mask and f.extended == extended)]
        
        self.logger.log(
            data=f"Removed filter: ID=0x{can_id:X}, Mask=0x{can_mask:X}, Extended={extended}",
            log_type=0,
            visibility="TD",
            tag="CANBusReader"
        )
    
    def clear_filters(self) -> None:
        """Clear all CAN message filters."""
        self.filters.clear()
        
        self.logger.log(
            data="Cleared all CAN filters",
            log_type=0,
            visibility="TD",
            tag="CANBusReader"
        )
    
    def connect(self) -> bool:
        """
        Establish connection to the CAN bus.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self.is_connected:
                return True
            
            # Prepare bus configuration
            bus_config = {
                'interface': self.interface,
                'channel': self.channel,
                'bitrate': self.bitrate,
                'timeout': self.timeout,
                'fd': self.fd,
                'data_bitrate': self.data_bitrate,
                'app_name': self.app_name,
                'serial': self.serial,
                'hw_type': self.hw_type,
                'rx_own_msgs': self.rx_own_msgs,
                'fd_data_bitrate': self.fd_data_bitrate,
                'log_errors': self.log_errors,
                'error_filters': self.error_filters,
                'serial_number': self.serial_number,
                'can_filters': self.can_filters
            }
            
            # Remove None values
            bus_config = {k: v for k, v in bus_config.items() if v is not None}
            
            # Create CAN bus
            self.bus = can.interface.Bus(**bus_config)
            
            # Apply filters if any
            if self.filters:
                can_filters = []
                for filter_obj in self.filters:
                    can_filters.append({
                        'can_id': filter_obj.can_id,
                        'can_mask': filter_obj.can_mask,
                        'extended': filter_obj.extended
                    })
                self.bus.set_filters(can_filters)
            
            self.is_connected = True
            self.stats["connection_errors"] = 0
            self.stats["last_error"] = None
            
            self.logger.log(
                data=f"Connected to CAN bus: {self.interface}:{self.channel} at {self.bitrate} bps",
                log_type=0,
                visibility="TD",
                tag="CANBusReader"
            )
            return True
            
        except Exception as e:
            self.is_connected = False
            self.stats["connection_errors"] += 1
            self.stats["last_error"] = str(e)
            
            self.logger.log(
                data=f"Failed to connect to CAN bus: {str(e)}",
                log_type=2,
                visibility="TD",
                tag="CANBusReader"
            )
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the CAN bus."""
        try:
            # Stop monitoring
            self.stop_monitoring()
            
            # Stop notifier
            if self.notifier:
                self.notifier.stop()
                self.notifier = None
            
            # Close bus
            if self.bus:
                self.bus.shutdown()
                self.bus = None
            
            self.is_connected = False
            
            self.logger.log(
                data=f"Disconnected from CAN bus",
                log_type=0,
                visibility="TD",
                tag="CANBusReader"
            )
        except Exception as e:
            self.logger.log(
                data=f"Error during disconnect: {str(e)}",
                log_type=2,
                visibility="TD",
                tag="CANBusReader"
            )
    
    def send_message(self, can_message: CANMessage) -> bool:
        """
        Send a CAN message.
        
        Args:
            can_message: CAN message to send
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected and not self.connect():
            return False
        
        try:
            # Create CAN message
            message = Message(
                arbitration_id=can_message.can_id,
                data=can_message.data,
                is_extended_id=(can_message.message_type == CANMessageType.EXTENDED),
                is_remote_frame=(can_message.message_type == CANMessageType.REMOTE),
                dlc=can_message.dlc,
                channel=can_message.channel
            )
            
            # Send message
            self.bus.send(message)
            
            self.stats["transmitted_messages"] += 1
            self.stats["total_messages"] += 1
            
            self.logger.log(
                data=f"Sent message: {can_message.name} (ID: 0x{can_message.can_id:X})",
                log_type=0,
                visibility="TD",
                tag="CANBusReader"
            )
            return True
            
        except Exception as e:
            self.stats["last_error"] = str(e)
            
            self.logger.log(
                data=f"Failed to send message {can_message.name}: {str(e)}",
                log_type=2,
                visibility="TD",
                tag="CANBusReader"
            )
            return False
    
    def read_messages(self, timeout: Optional[float] = None) -> List[CANMessage]:
        """
        Read messages from the CAN bus.
        
        Args:
            timeout: Read timeout (uses default if None)
            
        Returns:
            List of received CAN messages
        """
        if not self.is_connected and not self.connect():
            return []
        
        if timeout is None:
            timeout = self.timeout
        
        try:
            messages = []
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    message = self.bus.recv(timeout=0.1)
                    if message is not None:
                        # Convert to our CANMessage format
                        can_msg = CANMessage(
                            can_id=message.arbitration_id,
                            data=list(message.data),
                            message_type=CANMessageType.EXTENDED if message.is_extended_id else CANMessageType.STANDARD,
                            name=f"msg_{message.arbitration_id:X}",
                            description=f"Received message ID 0x{message.arbitration_id:X}",
                            dlc=message.dlc,
                            is_rx=True,
                            is_tx=False,
                            timestamp=message.timestamp,
                            channel=message.channel or self.channel
                        )
                        
                        messages.append(can_msg)
                        self.stats["received_messages"] += 1
                        self.stats["total_messages"] += 1
                        
                        # Check if this matches any configured message
                        for msg_name, configured_msg in self.messages.items():
                            if configured_msg.can_id == message.arbitration_id:
                                can_msg.name = configured_msg.name
                                can_msg.description = configured_msg.description
                                break
                        
                        self.last_read_time = time.time()
                        
                except can.CanTimeoutError:
                    # Timeout is expected, continue
                    continue
                except Exception as e:
                    self.logger.log(
                        data=f"Error reading message: {str(e)}",
                        log_type=2,
                        visibility="TD",
                        tag="CANBusReader"
                    )
                    break
            
            return messages
            
        except Exception as e:
            self.stats["last_error"] = str(e)
            
            self.logger.log(
                data=f"Failed to read messages: {str(e)}",
                log_type=2,
                visibility="TD",
                tag="CANBusReader"
            )
            return []
    
    def start_monitoring(self, callback: Optional[callable] = None) -> None:
        """
        Start monitoring CAN bus messages.
        
        Args:
            callback: Optional callback function for received messages
        """
        if self.monitor_running:
            return
        
        self.monitor_callback = callback
        self.monitor_running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
        self.logger.log(
            data="Started CAN bus monitoring",
            log_type=0,
            visibility="TD",
            tag="CANBusReader"
        )
    
    def stop_monitoring(self) -> None:
        """Stop monitoring CAN bus messages."""
        self.monitor_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
            self.monitor_thread = None
        
        self.logger.log(
            data="Stopped CAN bus monitoring",
            log_type=0,
            visibility="TD",
            tag="CANBusReader"
        )
    
    def _monitor_loop(self) -> None:
        """Message monitoring loop."""
        while self.monitor_running:
            try:
                messages = self.read_messages(timeout=0.1)
                
                for message in messages:
                    if self.monitor_callback:
                        self.monitor_callback(message)
                    else:
                        self.logger.log(
                            data=f"Monitored: {message.name} (ID: 0x{message.can_id:X}) = {message.data}",
                            log_type=0,
                            visibility="TD",
                            tag="CANBusReader"
                        )
                
            except Exception as e:
                self.logger.log(
                    data=f"Monitor error: {str(e)}",
                    log_type=2,
                    visibility="TD",
                    tag="CANBusReader"
                )
                time.sleep(1.0)
    
    def read_data(self) -> Dict[str, Any]:
        """
        Read data from the device.
        
        Returns:
            Dictionary containing device data
        """
        messages = self.read_messages()
        data = {}
        
        for message in messages:
            data[message.name] = {
                "value": message.data,
                "can_id": message.can_id,
                "timestamp": message.timestamp,
                "description": message.description,
                "quality": "good"
            }
        
        return data
    
    def save_data(self, data: Dict[str, Any]) -> bool:
        """
        Save data (placeholder method).
        
        Args:
            data: Data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # This would typically save to the database
            # For now, just log the data
            self.logger.log(
                data=data,
                log_type=0,
                visibility="TD",
                tag="CANBusReader"
            )
            return True
        except Exception as e:
            self.logger.log(
                data=f"Failed to save data: {str(e)}",
                log_type=2,
                visibility="TD",
                tag="CANBusReader"
            )
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get device status information.
        
        Returns:
            Dictionary containing device status
        """
        return {
            "interface": self.interface,
            "channel": self.channel,
            "bitrate": self.bitrate,
            "timeout": self.timeout,
            "fd": self.fd,
            "is_connected": self.is_connected,
            "health_status": self.health_status,
            "last_read_time": self.last_read_time,
            "last_health_check": self.last_health_check,
            "message_count": len(self.messages),
            "filter_count": len(self.filters),
            "monitor_running": self.monitor_running,
            "stats": self.stats.copy()
        }
    
    def check_health(self) -> bool:
        """
        Check the health of the CAN bus connection.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self.is_connected:
                return False
            
            # Try to read a message to test connection
            test_message = self.read_messages(timeout=0.1)
            
            # Connection is healthy if we can read (even if no messages)
            self.health_status = "healthy"
            self.last_health_check = time.time()
            return True
            
        except Exception as e:
            self.health_status = "unhealthy"
            self.last_health_check = time.time()
            self.logger.log(
                data=f"Health check failed: {str(e)}",
                log_type=2,
                visibility="TD",
                tag="CANBusReader"
            )
            return False
    
    def _start_health_monitor(self) -> None:
        """Start the health monitoring thread."""
        if not self.health_monitor_running:
            self.health_monitor_running = True
            self.health_monitor_thread = threading.Thread(
                target=self._health_monitor_loop,
                daemon=True
            )
            self.health_monitor_thread.start()
    
    def _health_monitor_loop(self) -> None:
        """Health monitoring loop."""
        while self.health_monitor_running:
            try:
                self.check_health()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                self.logger.log(
                    data=f"Health monitor error: {str(e)}",
                    log_type=2,
                    visibility="TD",
                    tag="CANBusReader"
                )
                time.sleep(30)
    
    def close(self) -> None:
        """Close the CAN bus reader and clean up resources."""
        self.health_monitor_running = False
        if self.health_monitor_thread:
            self.health_monitor_thread.join(timeout=5.0)
        
        self.stop_monitoring()
        self.disconnect()
        
        self.logger.log(
            data=f"Closed CAN bus reader: {self.interface}:{self.channel}",
            log_type=0,
            visibility="TD",
            tag="CANBusReader"
        )
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Factory functions and backward compatibility
def create_canbus_reader(
    interface: str = "socketcan",
    channel: str = "can0",
    bitrate: int = 500000,
    **kwargs
) -> CANBusReader:
    """
    Factory function to create a CAN bus reader.
    
    Args:
        interface: CAN interface type
        channel: CAN channel
        bitrate: CAN bus bitrate
        **kwargs: Additional arguments
        
    Returns:
        Configured CANBusReader instance
    """
    return CANBusReader(interface, channel, bitrate, **kwargs)


def send_can_message(
    interface: str,
    channel: str,
    can_id: int,
    data: List[int],
    **kwargs
) -> bool:
    """
    Send a single CAN message (backward compatibility function).
    
    Args:
        interface: CAN interface type
        channel: CAN channel
        can_id: CAN identifier
        data: Message data
        **kwargs: Additional arguments
        
    Returns:
        True if successful, False otherwise
    """
    reader = CANBusReader(interface, channel, **kwargs)
    
    with reader:
        message = CANMessage(
            can_id=can_id,
            data=data,
            message_type=CANMessageType.STANDARD,
            name=f"msg_{can_id:X}",
            description=f"Message ID 0x{can_id:X}"
        )
        return reader.send_message(message)


def read_can_messages(
    interface: str,
    channel: str,
    timeout: float = 1.0,
    **kwargs
) -> List[CANMessage]:
    """
    Read CAN messages (backward compatibility function).
    
    Args:
        interface: CAN interface type
        channel: CAN channel
        timeout: Read timeout
        **kwargs: Additional arguments
        
    Returns:
        List of received CAN messages
    """
    reader = CANBusReader(interface, channel, timeout=timeout, **kwargs)
    
    with reader:
        return reader.read_messages() 
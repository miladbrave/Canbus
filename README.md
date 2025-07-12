# CAN Bus Communication Library

A standalone Python library for CAN (Controller Area Network) bus communication. This library provides clean, object-oriented interfaces for CAN bus device communication including message reading, writing, and monitoring without external framework dependencies.

## Overview

The CAN bus library provides functionality to:
- Connect to CAN bus devices and networks
- Send and receive CAN messages
- Monitor CAN bus traffic
- Handle different CAN message formats (Standard, Extended)
- Support multiple CAN interfaces (SocketCAN, USB adapters)
- Implement CAN message filtering and routing
- Provide real-time message monitoring

## Features

- **Standalone Implementation**: No external framework dependencies
- **Multiple Interface Support**: SocketCAN, USB adapters, virtual interfaces
- **Message Types**: Standard (11-bit) and Extended (29-bit) CAN IDs
- **Message Filtering**: Advanced filtering capabilities
- **Real-time Monitoring**: Live CAN bus traffic monitoring
- **Message Queuing**: Asynchronous message handling
- **Error Handling**: Comprehensive error detection and recovery
- **Statistics Tracking**: Detailed performance and usage statistics
- **Thread Safety**: Thread-safe operations for concurrent access
- **Context Manager Support**: Safe resource management with `with` statements

## Installation

### Prerequisites

```bash
# For CAN bus communication
pip install python-can

# For SocketCAN support (Linux)
sudo apt-get install can-utils

# For Windows
# Install appropriate CAN adapter drivers
```

### Usage

Simply copy the `canbus_reader.py` file into your project and import it:

```python
from canbus_reader import CANBusReader, CANMessage, CANMessageType
```

## Quick Start

```python
from canbus_reader import CANBusReader, CANMessage, CANMessageType

# Create CAN bus reader
reader = CANBusReader(
    interface="socketcan",
    channel="can0",
    bitrate=500000,
    timeout=1.0
)

# Create CAN message
message = CANMessage(
    can_id=0x123,
    data=[0x01, 0x02, 0x03, 0x04],
    message_type=CANMessageType.STANDARD,
    name="engine_speed",
    description="Engine speed message"
)

# Send message
reader.send_message(message)

# Read messages
messages = reader.read_messages()
print(messages)
```

## CAN Message Types

### Supported Message Types

- **STANDARD**: Standard CAN messages (11-bit ID)
- **EXTENDED**: Extended CAN messages (29-bit ID)
- **REMOTE**: Remote transmission requests
- **ERROR**: Error frames
- **OVERLOAD**: Overload frames

### Message Properties

Common CAN message properties:
- **can_id**: CAN identifier (11 or 29 bits)
- **data**: Message data payload (0-8 bytes)
- **dlc**: Data length code
- **is_rx**: Whether message was received
- **is_tx**: Whether message was transmitted
- **timestamp**: Message timestamp
- **channel**: CAN channel identifier

## Examples

### Basic CAN Communication

```python
from canbus_reader import CANBusReader, CANMessage, CANMessageType
import time

# Create reader
reader = CANBusReader(
    interface="socketcan",
    channel="can0",
    bitrate=500000,
    timeout=1.0
)

# Define messages
messages = [
    CANMessage(0x100, [0x01, 0x02], CANMessageType.STANDARD, "status", "System status"),
    CANMessage(0x200, [0x03, 0x04], CANMessageType.STANDARD, "data", "Sensor data"),
    CANMessage(0x300, [0x05, 0x06], CANMessageType.STANDARD, "control", "Control command")
]

# Send messages
with reader:
    for message in messages:
        reader.send_message(message)
        time.sleep(0.1)
    
    # Read received messages
    received = reader.read_messages()
    for msg in received:
        print(f"Received: {msg}")
```

### Automotive Example

```python
from canbus_reader import CANBusReader, CANMessage, CANMessageType
import time

# Create reader for automotive CAN bus
reader = CANBusReader(
    interface="socketcan",
    channel="can0",
    bitrate=500000,
    timeout=1.0
)

# Automotive CAN messages
automotive_messages = [
    # Engine data
    CANMessage(0x0C1, [0x00, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "engine_speed", "Engine RPM"),
    CANMessage(0x0C2, [0x00, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "engine_temp", "Engine Temperature"),
    CANMessage(0x0C3, [0x00, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "fuel_level", "Fuel Level"),
    
    # Vehicle data
    CANMessage(0x0D1, [0x00, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "vehicle_speed", "Vehicle Speed"),
    CANMessage(0x0D2, [0x00, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "odometer", "Odometer"),
    CANMessage(0x0D3, [0x00, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "trip_meter", "Trip Meter"),
    
    # Control messages
    CANMessage(0x0E1, [0x00, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "brake_status", "Brake Status"),
    CANMessage(0x0E2, [0x00, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "throttle_position", "Throttle Position"),
    CANMessage(0x0E3, [0x00, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "steering_angle", "Steering Angle")
]

# Add message filters
reader.add_filter(0x0C0, 0x0FF)  # Engine messages
reader.add_filter(0x0D0, 0x0FF)  # Vehicle messages
reader.add_filter(0x0E0, 0x0FF)  # Control messages

# Monitor automotive data
with reader:
    while True:
        try:
            messages = reader.read_messages()
            
            for msg in messages:
                if msg.name == "engine_speed":
                    rpm = int.from_bytes(msg.data[0:2], byteorder='big')
                    print(f"Engine RPM: {rpm}")
                
                elif msg.name == "vehicle_speed":
                    speed = int.from_bytes(msg.data[0:2], byteorder='big') / 100.0
                    print(f"Vehicle Speed: {speed} km/h")
                
                elif msg.name == "fuel_level":
                    fuel = msg.data[0] / 255.0 * 100
                    print(f"Fuel Level: {fuel:.1f}%")
                
                elif msg.name == "engine_temp":
                    temp = msg.data[0] - 40
                    print(f"Engine Temperature: {temp}°C")
            
            time.sleep(0.1)  # Read every 100ms
            
        except KeyboardInterrupt:
            print("Monitoring stopped by user")
            break
```

### Industrial Automation Example

```python
from canbus_reader import CANBusReader, CANMessage, CANMessageType
import time

# Create reader for industrial CAN bus
reader = CANBusReader(
    interface="socketcan",
    channel="can1",
    bitrate=250000,
    timeout=1.0
)

# Industrial automation messages
industrial_messages = [
    # Sensor data
    CANMessage(0x100, [0x00, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "pressure_sensor", "Pressure Sensor"),
    CANMessage(0x101, [0x00, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "temperature_sensor", "Temperature Sensor"),
    CANMessage(0x102, [0x00, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "flow_sensor", "Flow Sensor"),
    CANMessage(0x103, [0x00, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "level_sensor", "Level Sensor"),
    
    # Actuator control
    CANMessage(0x200, [0x00, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "valve_control", "Valve Control"),
    CANMessage(0x201, [0x00, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "pump_control", "Pump Control"),
    CANMessage(0x202, [0x00, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "motor_control", "Motor Control"),
    CANMessage(0x203, [0x00, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "heater_control", "Heater Control"),
    
    # System status
    CANMessage(0x300, [0x00, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "system_status", "System Status"),
    CANMessage(0x301, [0x00, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "alarm_status", "Alarm Status"),
    CANMessage(0x302, [0x00, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "maintenance_status", "Maintenance Status")
]

# Add filters for different message types
reader.add_filter(0x100, 0x1FF)  # Sensor messages
reader.add_filter(0x200, 0x2FF)  # Control messages
reader.add_filter(0x300, 0x3FF)  # Status messages

# Industrial monitoring and control
with reader:
    while True:
        try:
            messages = reader.read_messages()
            
            for msg in messages:
                if msg.name == "pressure_sensor":
                    pressure = int.from_bytes(msg.data[0:2], byteorder='big') / 100.0
                    print(f"Pressure: {pressure} bar")
                    
                    # Control valve based on pressure
                    if pressure > 10.0:
                        valve_msg = CANMessage(0x200, [0x01, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "valve_open", "Open Valve")
                        reader.send_message(valve_msg)
                
                elif msg.name == "temperature_sensor":
                    temp = int.from_bytes(msg.data[0:2], byteorder='big') / 10.0
                    print(f"Temperature: {temp}°C")
                    
                    # Control heater based on temperature
                    if temp < 20.0:
                        heater_msg = CANMessage(0x203, [0x01, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "heater_on", "Turn On Heater")
                        reader.send_message(heater_msg)
                
                elif msg.name == "alarm_status":
                    alarm_code = msg.data[0]
                    if alarm_code != 0:
                        print(f"ALARM: Code {alarm_code}")
                        # Trigger emergency shutdown
                        shutdown_msg = CANMessage(0x300, [0xFF, 0x00, 0x00, 0x00], CANMessageType.STANDARD, "emergency_shutdown", "Emergency Shutdown")
                        reader.send_message(shutdown_msg)
            
            time.sleep(0.05)  # Read every 50ms
            
        except KeyboardInterrupt:
            print("Industrial monitoring stopped")
            break
```

### Message Filtering and Routing

```python
from canbus_reader import CANBusReader, CANMessage, CANMessageType

# Create reader with advanced filtering
reader = CANBusReader(
    interface="socketcan",
    channel="can0",
    bitrate=500000
)

# Add specific message filters
reader.add_filter(0x100, 0x1FF)  # Accept messages with ID 0x100-0x1FF
reader.add_filter(0x200, 0x2FF)  # Accept messages with ID 0x200-0x2FF
reader.add_filter(0x300, 0x3FF)  # Accept messages with ID 0x300-0x3FF

# Remove specific filters
reader.remove_filter(0x200, 0x2FF)  # Remove filter for 0x200-0x2FF

# Clear all filters
reader.clear_filters()

# Add extended ID filter
reader.add_filter(0x18FF0000, 0x18FFFFFF, extended=True)  # Extended ID filter

# Monitor with filtering
with reader:
    while True:
        messages = reader.read_messages()
        
        for msg in messages:
            print(f"Filtered message: {msg}")
        
        time.sleep(0.1)
```

## Configuration

### Interface Settings

```python
reader = CANBusReader(
    interface="socketcan",        # Interface type (socketcan, pcan, vector, etc.)
    channel="can0",               # CAN channel
    bitrate=500000,               # Bitrate in bits per second
    timeout=1.0,                  # Read timeout
    fd=False,                     # CAN FD support
    data_bitrate=2000000,         # CAN FD data bitrate
    app_name="my_can_app",        # Application name
    serial=None,                  # Serial number for USB adapters
    hw_type=None,                 # Hardware type
    rx_own_msgs=False,            # Receive own messages
    fd_data_bitrate=None,         # CAN FD data bitrate
    log_errors=True,              # Log errors
    error_filters=None,           # Error filters
    serial_number=None,           # Serial number
    can_filters=None,             # CAN filters
    **kwargs                      # Additional interface-specific parameters
)
```

### Message Configuration

```python
message = CANMessage(
    can_id=0x123,                 # CAN identifier
    data=[0x01, 0x02, 0x03],     # Message data
    message_type=CANMessageType.STANDARD,  # Message type
    name="my_message",            # Message name
    description="My CAN message", # Description
    dlc=8,                        # Data length code
    is_rx=True,                   # Is received message
    is_tx=False,                  # Is transmitted message
    timestamp=time.time(),        # Timestamp
    channel="can0"                # Channel
)
```

### Logging

```python
from canbus_reader import SimpleLogger

# Create custom logger
logger = SimpleLogger(log_level=1)  # 0=info, 1=warning, 2=error

# Use with CAN bus reader
reader = CANBusReader(interface="socketcan", channel="can0", logger=logger)
```

## Error Handling

The library includes comprehensive error handling:

- **Interface Errors**: CAN interface connection issues
- **Message Errors**: Invalid message format or data
- **Filter Errors**: Invalid filter configuration
- **Timeout Errors**: Message timeout handling
- **Logging**: Detailed error logging with different levels

## Performance Considerations

- **Message Frequency**: Adjust read intervals based on message frequency
- **Filter Usage**: Use filters to reduce processing load
- **Buffer Size**: Configure appropriate buffer sizes
- **Thread Safety**: Use thread-safe operations for concurrent access

## Troubleshooting

### Common Issues

1. **Interface Connection Failures**
   - Check CAN interface availability
   - Verify interface permissions
   - Ensure CAN interface is configured

2. **Message Transmission Errors**
   - Check CAN bus termination
   - Verify bitrate configuration
   - Ensure proper message format

3. **Filter Issues**
   - Verify filter configuration
   - Check message ID ranges
   - Ensure proper filter syntax

### Debug Mode

Enable debug logging by setting log level to 0:

```python
logger = SimpleLogger(log_level=0)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the examples
3. Create an issue with detailed information

## Version History

- **v1.0.0**: Initial release with CAN bus support
- Standalone implementation without external framework dependencies
- Comprehensive message reading and writing
- Advanced filtering and routing
- Real-time monitoring capabilities
- Automotive and industrial examples

## References

- CAN Bus Standard: ISO 11898
- SocketCAN Documentation
- Python-CAN Library
- Automotive CAN Protocols
- Industrial CAN Applications 
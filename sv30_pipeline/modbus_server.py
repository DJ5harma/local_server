"""
Modbus TCP Server for SV30 System (v4.0 - Fixed Import)
Compatible with pymodbus 2.x and 3.x
"""

import threading
import time

# Try importing for pymodbus 3.x first, then fall back to 2.x
try:
    # pymodbus 3.x
    from pymodbus.server import StartAsyncTcpServer
    from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
    from pymodbus.datastore import ModbusSequentialDataBlock
    PYMODBUS_VERSION = 3
except ImportError:
    try:
        # pymodbus 2.x
        from pymodbus.server.sync import StartTcpServer
        from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
        from pymodbus.datastore import ModbusSequentialDataBlock
        PYMODBUS_VERSION = 2
    except ImportError:
        print("[MODBUS ERROR] pymodbus not installed!")
        print("Install: pip install pymodbus --break-system-packages")
        PYMODBUS_VERSION = None

from sv30config import MODBUS_HOST, MODBUS_PORT

# Global server context
_server_context = None
_server_thread = None

def create_datastore():
    """
    Create Modbus datastore with holding registers
    
    Register Map (Holding Registers):
    40001: SV30_VALUE (% × 100)
    40002: SETTLING_VELOCITY (%/sec × 10,000)
    40003: TEST_DURATION (minutes)
    40004: TEST_END_EPOCH_HI (MSB of epoch)
    40005: TEST_END_EPOCH_LO (LSB of epoch)
    """
    # Initialize with zeros
    # Modbus uses 0-based indexing internally
    store = ModbusSlaveContext(
        hr=ModbusSequentialDataBlock(0, [0]*100)  # 100 holding registers
    )
    
    context = ModbusServerContext(slaves=store, single=True)
    return context

def write_register(address, value):
    """
    Write value to Modbus holding register
    
    Args:
        address: Register address (e.g., 40001)
        value: 16-bit value to write (0-65535)
    """
    global _server_context
    
    if _server_context is None:
        print(f"[MODBUS ERROR] Server not running, cannot write register {address}")
        return False
    
    try:
        # Convert Modbus address to 0-based index
        # 40001 -> index 0, 40002 -> index 1, etc.
        index = address - 40001
        
        if index < 0 or index >= 100:
            print(f"[MODBUS ERROR] Invalid address: {address}")
            return False
        
        # Ensure value is 16-bit
        value = int(value) & 0xFFFF
        
        # Write to holding register
        slave = _server_context[0]
        slave.setValues(3, index, [value])  # Function code 3 = holding registers
        
        return True
    
    except Exception as e:
        print(f"[MODBUS ERROR] Failed to write register {address}: {e}")
        return False

def run_server_v2():
    """Run Modbus TCP server (pymodbus 2.x)"""
    global _server_context
    
    print(f"[MODBUS] Starting server v2.x at {MODBUS_HOST}:{MODBUS_PORT}")
    
    _server_context = create_datastore()
    
    try:
        StartTcpServer(
            context=_server_context,
            address=(MODBUS_HOST, MODBUS_PORT)
        )
    except Exception as e:
        print(f"[MODBUS ERROR] Server failed: {e}")

def run_server_v3():
    """Run Modbus TCP server (pymodbus 3.x)"""
    import asyncio
    
    global _server_context
    
    print(f"[MODBUS] Starting server v3.x at {MODBUS_HOST}:{MODBUS_PORT}")
    
    _server_context = create_datastore()
    
    async def start_async_server():
        try:
            await StartAsyncTcpServer(
                context=_server_context,
                address=(MODBUS_HOST, MODBUS_PORT)
            )
        except Exception as e:
            print(f"[MODBUS ERROR] Server failed: {e}")
    
    # Run async server
    try:
        asyncio.run(start_async_server())
    except Exception as e:
        print(f"[MODBUS ERROR] Async runtime failed: {e}")

def start_in_thread():
    """Start Modbus server in background thread"""
    global _server_thread
    
    if PYMODBUS_VERSION is None:
        print("[MODBUS] Pymodbus not installed - server disabled")
        return False
    
    if _server_thread and _server_thread.is_alive():
        print("[MODBUS] Server already running")
        return True
    
    try:
        if PYMODBUS_VERSION == 3:
            _server_thread = threading.Thread(target=run_server_v3, daemon=True)
        else:
            _server_thread = threading.Thread(target=run_server_v2, daemon=True)
        
        _server_thread.start()
        time.sleep(1)  # Give server time to start
        
        print(f"[MODBUS] Server started successfully (v{PYMODBUS_VERSION}.x)")
        return True
    
    except Exception as e:
        print(f"[MODBUS ERROR] Failed to start server: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("  MODBUS TCP SERVER TEST")
    print("="*60)
    print(f"Version: pymodbus {PYMODBUS_VERSION}.x" if PYMODBUS_VERSION else "pymodbus NOT INSTALLED")
    print(f"Host: {MODBUS_HOST}")
    print(f"Port: {MODBUS_PORT}")
    print("="*60 + "\n")
    
    if PYMODBUS_VERSION is None:
        print("Install pymodbus:")
        print("  pip install pymodbus --break-system-packages")
        exit(1)
    
    # Start server
    start_in_thread()
    
    # Test writing registers
    print("\nTesting register writes...")
    
    test_values = [
        (40001, 1234),   # SV30
        (40002, 5678),   # Velocity
        (40003, 35),     # Duration (35 minutes now!)
        (40004, 0x1234), # Epoch HI
        (40005, 0x5678), # Epoch LO
    ]
    
    time.sleep(2)  # Wait for server to fully start
    
    for addr, val in test_values:
        success = write_register(addr, val)
        if success:
            print(f"  ✅ Register {addr} = {val}")
        else:
            print(f"  ❌ Failed to write register {addr}")
    
    print("\n" + "="*60)
    print("  SERVER RUNNING - Press Ctrl+C to stop")
    print("="*60)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n[MODBUS] Server stopped")

#!/usr/bin/env python3
"""
SainyaSecure Demo Startup Script
Starts the battlefield communication demo server and opens the web interface
"""

import os
import sys
import subprocess
import time
import webbrowser
import threading
import signal
from pathlib import Path

def start_demo_server():
    """Start the battlefield communication server"""
    try:
        # Get the directory containing this script
        demo_dir = Path(__file__).parent
        server_script = demo_dir / 'battlefield_server.py'
        
        print("🚀 Starting SainyaSecure Battlefield Communication Demo...")
        print("=" * 60)
        print("🔧 Server: Starting WebSocket server on localhost:8765")
        
        # Start the server
        server_process = subprocess.Popen([
            sys.executable, str(server_script)
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        return server_process
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return None

def open_demo_website():
    """Open the demo website in the default browser"""
    try:
        demo_dir = Path(__file__).parent
        html_file = demo_dir / 'index.html'
        
        if html_file.exists():
            print("🌐 Opening demo website...")
            file_url = f"file://{html_file.absolute()}"
            webbrowser.open(file_url)
            return True
        else:
            print(f"❌ Demo HTML file not found: {html_file}")
            return False
            
    except Exception as e:
        print(f"❌ Error opening website: {e}")
        return False

def install_dependencies():
    """Install required Python dependencies"""
    try:
        print("📦 Installing required dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'websockets'], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("Please manually install: pip install websockets")
        return False

def print_demo_info():
    """Print demo information and instructions"""
    print("🎯 SAINYA SECURE - MILITARY COMMUNICATION DEMO")
    print("=" * 60)
    print("This demo showcases a secure military communication system with:")
    print("• 🔄 P2P fallback when central server fails")
    print("• 🛡️  End-to-end encryption and digital signatures")
    print("• ⏰ Lamport clock synchronization for message ordering")
    print("• 🔗 Blockchain-based message integrity")
    print("• 📡 Battlefield network simulation")
    print()
    print("Demo Features:")
    print("• Real-time tactical map with node positions")
    print("• Server failure simulation with automatic P2P fallback")
    print("• Node dropout and recovery scenarios")
    print("• Message routing visualization")
    print("• Network synchronization conflicts resolution")
    print()
    print("How to Use:")
    print("1. Select a battlefield node from the left panel")
    print("2. Send messages using the right panel")
    print("3. Use scenario buttons to simulate battlefield conditions")
    print("4. Watch the tactical map for real-time network status")
    print("5. Monitor blockchain for message integrity")
    print()

def main():
    """Main demo startup function"""
    print_demo_info()
    
    # Check for dependencies
    try:
        import websockets
    except ImportError:
        if not install_dependencies():
            print("❌ Cannot continue without websockets. Please install manually:")
            print("   pip install websockets")
            sys.exit(1)
    
    # Start the server
    server_process = start_demo_server()
    if not server_process:
        print("❌ Failed to start server")
        sys.exit(1)
    
    # Wait a moment for server to start
    print("⏳ Waiting for server to initialize...")
    time.sleep(2)
    
    # Open the website
    if open_demo_website():
        print("✅ Demo started successfully!")
        print()
        print("📋 Demo Controls:")
        print("• Server Failure: Simulates central server going down")
        print("• Node Dropout: Randomly takes a battlefield node offline")
        print("• Force Sync: Manually synchronizes all nodes")
        print("• Demo Scenarios: Run pre-configured battlefield simulations")
        print()
        print("🔧 Technical Details:")
        print("• WebSocket Server: ws://localhost:8765")
        print("• Frontend: Static HTML/CSS/JavaScript")
        print("• Backend: Python WebSocket server")
        print()
        print("Press Ctrl+C to stop the demo server...")
        print("=" * 60)
    else:
        print("❌ Failed to open demo website")
        server_process.terminate()
        sys.exit(1)
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down demo server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("✅ Demo server stopped")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Keep the main process running and monitor server
        while True:
            if server_process.poll() is not None:
                # Server process has ended
                return_code = server_process.returncode
                if return_code != 0:
                    print(f"❌ Server process ended with error code: {return_code}")
                else:
                    print("✅ Server process ended normally")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()
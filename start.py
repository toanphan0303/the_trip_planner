#!/usr/bin/env python3
"""
Trip Planner - LangGraph Studio Startup Script
This script starts LangGraph Studio for testing the trip planner workflow
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_banner():
    """Print startup banner"""
    print("🌍" + "="*60 + "🌍")
    print("    TRIP PLANNER - LANGGRAPH STUDIO TESTING")
    print("    LangGraph Studio (In-Memory Mode)")
    print("    (Process will be stopped when you exit)")
    print("="*64)
    print("🚀 Starting LangGraph Studio...")
    print()

def check_dependencies():
    """Check if required dependencies are installed"""
    print("📋 Checking dependencies...")
    
    # Check if we're in the right directory
    if not os.path.exists("server"):
        print("❌ Error: Please run this script from the project root directory")
        print("   Expected structure: ./server/")
        sys.exit(1)
    
    # Check if requirements.txt exists
    if not os.path.exists("server/requirements.txt"):
        print("❌ Error: server/requirements.txt not found")
        sys.exit(1)
    
    # Check if .env file exists
    if not os.path.exists("server/.env"):
        print("⚠️  Warning: server/.env file not found")
        print("   Please copy server/env_template.txt to server/.env and configure it")
        print("   Continuing with default environment...")
    
    print("✅ Dependencies check passed")

def setup_virtual_environment():
    """Create and activate virtual environment"""
    print("🐍 Setting up virtual environment...")
    
    # Use absolute paths
    script_dir = Path(__file__).parent.absolute()
    venv_path = script_dir / "venv"
    venv_python = get_venv_python()
    
    # Check if virtual environment already exists and is valid
    if venv_path.exists() and Path(venv_python).exists():
        print("✅ Virtual environment already exists")
        return venv_python
    
    # Remove incomplete venv if it exists
    if venv_path.exists():
        print("🧹 Removing incomplete virtual environment...")
        import shutil
        shutil.rmtree(venv_path)
    
    try:
        # Create virtual environment
        print("📦 Creating virtual environment...")
        result = subprocess.run([
            sys.executable, "-m", "venv", "venv"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Error creating virtual environment: {result.stderr}")
            print("💡 Tip: Make sure you have Python 3.3+ with venv module")
            print("   Try: python3 -m venv venv")
            sys.exit(1)
        
        # Verify the virtual environment was created properly
        if not Path(venv_python).exists():
            print(f"❌ Virtual environment creation failed - {venv_python} not found")
            sys.exit(1)
        
        print("✅ Virtual environment created successfully")
        return venv_python
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def get_venv_python():
    """Get the path to the virtual environment Python executable"""
    # Use absolute path to avoid issues
    script_dir = Path(__file__).parent.absolute()
    return str(script_dir / "venv" / "bin" / "python")

def install_requirements(venv_python):
    """Install Python requirements in virtual environment"""
    print("📦 Installing Python requirements in virtual environment...")
    
    try:
        # Change to server directory
        os.chdir("server")
        
        # Upgrade pip first
        print("🔄 Upgrading pip...")
        subprocess.run([
            venv_python, "-m", "pip", "install", "--upgrade", "pip"
        ], capture_output=True, text=True)
        
        # Install requirements (LangGraph-compatible versions)
        print("📥 Installing packages...")
        result = subprocess.run([
            venv_python, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Error installing requirements: {result.stderr}")
            sys.exit(1)
        
        print("✅ Requirements installed successfully in virtual environment")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def kill_port_process(port):
    """Kill any process using the specified port, but preserve Docker containers"""
    try:
        result = subprocess.run([
            "lsof", "-ti", f":{port}"
        ], capture_output=True, text=True)
        
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            killed_count = 0
            for pid in pids:
                if pid:
                    # Check if this is a Docker container process
                    try:
                        cmd_result = subprocess.run([
                            "ps", "-p", pid, "-o", "comm="
                        ], capture_output=True, text=True)
                        process_name = cmd_result.stdout.strip()
                        
                        # Don't kill Docker-related processes
                        if "docker" not in process_name.lower() and "com.docker" not in process_name:
                            subprocess.run(["kill", "-9", pid], capture_output=True)
                            killed_count += 1
                    except:
                        # If we can't check the process name, skip it
                        pass
            
            if killed_count > 0:
                print(f"🧹 Killed {killed_count} non-Docker process(es) on port {port}")
            else:
                print(f"🔒 Preserved Docker containers on port {port}")
    except Exception:
        pass  # No process to kill or lsof not available

def check_langgraph_cli():
    """Check if LangGraph CLI is installed in virtual environment"""
    try:
        # Check in virtual environment
        script_dir = Path(__file__).parent.absolute()
        langgraph_cmd = script_dir / "venv" / "bin" / "langgraph"
        
        if langgraph_cmd.exists():
            result = subprocess.run([str(langgraph_cmd), "--version"], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        return False
    except Exception:
        return False

def install_langgraph_cli(venv_python):
    """Install LangGraph CLI in virtual environment"""
    print("📦 Installing LangGraph CLI...")
    
    try:
        result = subprocess.run([
            venv_python, "-m", "pip", "install", "langgraph-cli"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"⚠️  Warning: Could not install LangGraph CLI: {result.stderr}")
            return False
        
        print("✅ LangGraph CLI installed successfully")
        return True
        
    except Exception as e:
        print(f"⚠️  Warning: Error installing LangGraph CLI: {e}")
        return False



def start_langgraph_studio(venv_python, enable_debug=False):
    """Start LangGraph Studio using virtual environment"""
    print("🎨 Starting LangGraph Studio...")
    
    try:
        # Set up environment variables for LangGraph Studio
        env = os.environ.copy()
        env["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "your-langsmith-api-key-here")
        env["LANGCHAIN_TRACING_V2"] = "true"
        env["LANGCHAIN_PROJECT"] = "trip-planner"
        env["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
        
        # Enable debugging if requested
        if enable_debug:
            env["ENABLE_REMOTE_DEBUG"] = "true"
            env["DEBUG_PORT"] = "5678"
            print("🐛 Remote debugging enabled on port 5678")
            print("   Connect your debugger to localhost:5678")
        
        # No Docker environment variables needed for in-memory mode
        
        # Using in-memory LangGraph Studio (no Docker required)
        print("✅ Using in-memory LangGraph Studio (no Docker required)")
        
        # Kill any existing process on port 2024 (langgraph dev uses this port)
        kill_port_process(2024)
        
        # Get the virtual environment's langgraph command
        script_dir = Path(__file__).parent.absolute()
        langgraph_cmd = script_dir / "venv" / "bin" / "langgraph"
        
        print(f"🔍 Looking for LangGraph CLI at: {langgraph_cmd}")
        
        # Check if langgraph command exists in venv
        if not langgraph_cmd.exists():
            print("⚠️  LangGraph CLI not found in virtual environment")
            print("💡 Try running: pip install langgraph-cli")
            return None
        
        # Change to server directory for langgraph (use absolute path)
        original_dir = os.getcwd()
        script_dir = Path(__file__).parent.absolute()
        server_dir = script_dir / "server"
        
        if not server_dir.exists():
            print(f"⚠️  Server directory not found: {server_dir}")
            return None
            
        os.chdir(str(server_dir))
        
        # Start LangGraph Studio in foreground to show real-time output
        print(f"🔧 Starting LangGraph Studio in development mode...")
        print("📋 LangGraph Studio logs will appear below:")
        print("=" * 60)
        
        # Start LangGraph Studio in foreground to show real-time output
        process = subprocess.Popen([
            str(langgraph_cmd), "dev", "--config", "langgraph.json"
        ], stdout=None, stderr=None, env=env)  # stdout=None, stderr=None means inherit parent's stdout/stderr
        
        # Return to original directory
        os.chdir(original_dir)
        
        # Since we're running in foreground, the process will block here
        # The logs will be displayed in real-time
        print("✅ LangGraph Studio process started")
        print("📋 You should see LangGraph Studio logs above")
        print("🎨 Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024")
        
        # Return the process (it will be running in foreground)
        return process
            
    except Exception as e:
        print(f"⚠️  Warning: Could not start LangGraph Studio: {e}")
        return None

def print_summary(studio_process):
    """Print summary of running services"""
    print()
    print("🎉" + "="*60 + "🎉")
    print("    LANGGRAPH STUDIO STARTED SUCCESSFULLY!")
    print("="*64)
    print()
    print("📍 Access Points:")
    print("   🎨 LangGraph Studio:   http://localhost:2024")
    print("   🎨 Studio UI:          https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024")
    print("   📋 Logs:               Displayed in real-time below")
    
    print()
    print("🐛 Debugging:")
    print("   🔌 Remote Debug Port: 5678")
    print("   🔧 VS Code Config:    'Attach to LangSmith Studio'")
    print("   📍 Connect to:        localhost:5678")
    print("   💡 Set breakpoints in your code, then attach debugger")
    
    print()
    print("🐍 Virtual Environment:")
    print("   📁 Location:          ./venv/")
    print("   🔧 Activate:          source venv/bin/activate")
    print("   📦 Packages:          Isolated in virtual environment")
    print()
    print("🛠️  Available Workflows:")
    print("   • LangGraph Multi-step Workflow (Trip Planning)")
    print()
    print("📊 Data Collection:")
    print("   • LangSmith integration for monitoring")
    print("   • Workflow execution traces")
    print("   • Performance metrics")
    print()
    print("🛑 To stop LangGraph Studio: Press Ctrl+C")
    print("="*64)

def main():
    """Main startup function"""
    print_banner()
    
    # Enable debugging by default
    enable_debug = True
    print("🐛 Debug mode enabled by default")
    
    # Store original directory
    original_dir = os.getcwd()
    
    try:
        # Check dependencies
        check_dependencies()
        
        # Setup virtual environment
        try:
            venv_python = setup_virtual_environment()
            use_venv = True
        except Exception as e:
            print(f"⚠️  Virtual environment setup failed: {e}")
            print("🔄 Falling back to system Python...")
            venv_python = sys.executable
            use_venv = False
        
        # Install requirements
        if use_venv:
            install_requirements(venv_python)
        else:
            print("❌ Cannot continue without virtual environment")
            sys.exit(1)
        
        # Check and install LangGraph CLI if needed
        if not check_langgraph_cli():
            if not install_langgraph_cli(venv_python):
                print("❌ Cannot continue without LangGraph CLI")
                sys.exit(1)
        
        # Start LangGraph Studio
        studio_process = start_langgraph_studio(venv_python, enable_debug=enable_debug)
        
        if not studio_process:
            print("❌ Cannot continue without LangGraph Studio")
            sys.exit(1)
        

        
        # Print summary
        print_summary(studio_process)
        
        # Since LangGraph Studio is running in foreground, we just wait for it
        # The process will handle its own output and termination
        try:
            # Wait for the LangGraph Studio process to complete
            studio_process.wait()
            print("✅ LangGraph Studio process completed")
        except KeyboardInterrupt:
            print("\n🛑 Shutting down services...")
            
            # Since LangGraph Studio is running in foreground, Ctrl+C will stop it directly
            print("🛑 LangGraph Studio process terminated by user")
            print("👋 All services stopped. Goodbye!")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
    
    finally:
        # Return to original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    main()

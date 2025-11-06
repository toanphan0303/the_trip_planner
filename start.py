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
import json

def print_banner():
    """Print startup banner"""
    print("🌍" + "="*60 + "🌍")
    print("    TRIP PLANNER - LANGGRAPH STUDIO")
    print("    LangGraph Studio + MongoDB Cache + Auto State Persistence")
    print("    (Process will be stopped when you exit)")
    print("="*64)
    print("🚀 Starting services...")
    print()

def check_docker():
    """Check if Docker is installed and running"""
    print("🐳 Checking Docker...")
    
    try:
        # Check if Docker is installed
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Docker is not installed or not in PATH")
            print("   Please install Docker Desktop from https://www.docker.com/products/docker-desktop")
            return False
        
        # Check if Docker daemon is running
        result = subprocess.run(["docker", "info"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Docker daemon is not running")
            print("   Please start Docker Desktop")
            return False
        
        print("✅ Docker is installed and running")
        return True
        
    except FileNotFoundError:
        print("❌ Docker command not found")
        print("   Please install Docker Desktop from https://www.docker.com/products/docker-desktop")
        return False

def check_docker_compose():
    """Check if docker-compose.yml exists"""
    if not os.path.exists("docker-compose.yml"):
        print("❌ docker-compose.yml not found in project root")
        print("   Please ensure docker-compose.yml exists")
        return False
    
    print("✅ docker-compose.yml found")
    return True

def start_mongodb():
    """Start MongoDB container using Docker Compose"""
    print("🍃 Starting MongoDB container...")
    
    try:
        # Check if container is already running
        result = subprocess.run([
            "docker", "ps", "--filter", "name=trip_planner_mongodb", "--format", "{{.Names}}"
        ], capture_output=True, text=True)
        
        if "trip_planner_mongodb" in result.stdout:
            print("✅ MongoDB container is already running")
            return True
        
        # Start MongoDB container
        result = subprocess.run([
            "docker-compose", "up", "-d", "mongodb"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Failed to start MongoDB container: {result.stderr}")
            return False
        
        # Wait for MongoDB to be ready
        print("⏳ Waiting for MongoDB to be ready...")
        max_attempts = 30
        for attempt in range(max_attempts):
            result = subprocess.run([
                "docker-compose", "exec", "-T", "mongodb", 
                "mongosh", "--eval", "db.runCommand('ping')", "--quiet"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ MongoDB is ready!")
                return True
            
            time.sleep(2)
        
        print("❌ MongoDB failed to start within 60 seconds")
        return False
        
    except Exception as e:
        print(f"❌ Error starting MongoDB: {e}")
        return False

def start_redis():
    """Start Redis container using Docker Compose"""
    print("🔴 Starting Redis container...")
    
    try:
        # Check if container is already running
        result = subprocess.run([
            "docker", "ps", "--filter", "name=trip_planner_redis", "--format", "{{.Names}}"
        ], capture_output=True, text=True)
        
        if "trip_planner_redis" in result.stdout:
            print("✅ Redis container is already running")
            return True
        
        # Start Redis container
        result = subprocess.run([
            "docker-compose", "up", "-d", "redis"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Failed to start Redis container: {result.stderr}")
            return False
        
        # Wait for Redis to be ready
        print("⏳ Waiting for Redis to be ready...")
        max_attempts = 15
        for attempt in range(max_attempts):
            result = subprocess.run([
                "docker-compose", "exec", "-T", "redis", 
                "redis-cli", "ping"
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and "PONG" in result.stdout:
                print("✅ Redis is ready!")
                return True
            
            time.sleep(2)
        
        print("❌ Redis failed to start within 30 seconds")
        return False
        
    except Exception as e:
        print(f"❌ Error starting Redis: {e}")
        return False

def stop_mongodb():
    """Stop MongoDB container"""
    print("🛑 Stopping MongoDB container...")
    
    try:
        result = subprocess.run([
            "docker-compose", "stop", "mongodb"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Failed to stop MongoDB container: {result.stderr}")
            return False
        
        print("✅ MongoDB container stopped")
        return True
        
    except Exception as e:
        print(f"❌ Error stopping MongoDB: {e}")
        return False

def stop_redis():
    """Stop Redis container"""
    print("🛑 Stopping Redis container...")
    
    try:
        result = subprocess.run([
            "docker-compose", "stop", "redis"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Failed to stop Redis container: {result.stderr}")
            return False
        
        print("✅ Redis container stopped")
        return True
        
    except Exception as e:
        print(f"❌ Error stopping Redis: {e}")
        return False

def get_mongodb_status():
    """Get MongoDB container status"""
    try:
        result = subprocess.run([
            "docker-compose", "ps", "mongodb"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return result.stdout.strip()
        return "Unknown"
        
    except Exception:
        return "Unknown"

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
        
        # Set MongoDB connection string
        env["MONGODB_URI"] = "mongodb://admin:trip_planner_pass@localhost:27017/"
        
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
    print("    ALL SERVICES STARTED SUCCESSFULLY!")
    print("="*64)
    print()
    print("📍 Access Points:")
    print("   🎨 LangGraph Studio:   http://localhost:2024")
    print("   🎨 Studio UI:          https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024")
    print("   🍃 MongoDB:            mongodb://admin:trip_planner_pass@localhost:27017/")
    print("   📋 Logs:               Displayed in real-time below")
    print()
    print("📊 Available Graphs:")
    print("   • trip_planner:    Main trip planning graph")
    print("   • travel_planner:  Travel planner with preference detection (auto-persisted)")
    
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
    print("🍃 MongoDB Cache:")
    print("   🐳 Container:         trip_planner_mongodb")
    print("   💾 Data Volume:       mongodb_data (persistent)")
    print("   🔗 Connection:        mongodb://admin:trip_planner_pass@localhost:27017/")
    print("   📊 Database:          trip_planner_cache")
    print()
    print("💾 State Persistence:")
    print("   🎨 LangGraph Studio provides automatic state persistence")
    print("   📊 All graph state is auto-saved between conversation turns")
    
    print()
    print("🛠️  Available Workflows:")
    print("   • LangGraph Multi-step Workflow (Trip Planning)")
    print("   • MongoDB-cached API calls (Google, Yelp, Foursquare)")
    print()
    print("📊 Data Collection:")
    print("   • LangSmith integration for monitoring")
    print("   • Workflow execution traces")
    print("   • Performance metrics")
    print("   • Persistent API response caching")
    print()
    print("🛑 To stop all services: Press Ctrl+C")
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
        
        # Check Docker and Docker Compose
        if not check_docker():
            print("❌ Cannot continue without Docker")
            sys.exit(1)
        
        if not check_docker_compose():
            print("❌ Cannot continue without docker-compose.yml")
            sys.exit(1)
        
        # Start MongoDB
        if not start_mongodb():
            print("❌ Cannot continue without MongoDB")
            sys.exit(1)
        
        # Redis is optional - LangGraph Studio provides automatic persistence
        # Uncomment below if you need Redis for other purposes
        # if not start_redis():
        #     print("⚠️  Redis failed to start (optional)")
        print("ℹ️  Redis skipped - LangGraph Studio provides automatic persistence")
        
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
            
            # Stop MongoDB container
            stop_mongodb()
            
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

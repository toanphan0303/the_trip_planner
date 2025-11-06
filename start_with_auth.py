#!/usr/bin/env python3
"""
Trip Planner with Authentication - Startup Script
This script starts both LangGraph Studio and FastAPI authentication server
"""

import os
import sys
import subprocess
import time
import threading
from pathlib import Path
import json
import signal

def print_banner():
    """Print startup banner"""
    print("🌍" + "="*70 + "🌍")
    print("    TRIP PLANNER WITH FACEBOOK AUTHENTICATION")
    print("    LangGraph Studio + FastAPI + MongoDB + Facebook Auth")
    print("    (Process will be stopped when you exit)")
    print("="*74)
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

def start_fastapi_server(venv_python):
    """Start FastAPI authentication server"""
    print("🔐 Starting FastAPI authentication server...")
    
    try:
        # Set up environment variables for FastAPI
        env = os.environ.copy()
        env["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "your-langsmith-api-key-here")
        env["LANGCHAIN_TRACING_V2"] = "true"
        env["LANGCHAIN_PROJECT"] = "trip-planner"
        env["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
        
        # Set MongoDB connection string
        env["MONGODB_URI"] = "mongodb://admin:trip_planner_pass@localhost:27017/"
        
        # Kill any existing process on port 8000
        kill_port_process(8000)
        
        # Change to server directory
        original_dir = os.getcwd()
        script_dir = Path(__file__).parent.absolute()
        server_dir = script_dir / "server"
        os.chdir(str(server_dir))
        
        # Start FastAPI server
        print("🚀 Starting FastAPI server on port 8000...")
        process = subprocess.Popen([
            venv_python, "-m", "uvicorn", "app:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], stdout=None, stderr=None, env=env)
        
        # Return to original directory
        os.chdir(original_dir)
        
        print("✅ FastAPI server started")
        return process
        
    except Exception as e:
        print(f"⚠️  Warning: Could not start FastAPI server: {e}")
        return None

def start_langgraph_studio(venv_python):
    """Start LangGraph Studio"""
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
        
        # Kill any existing process on port 2024
        kill_port_process(2024)
        
        # Get the virtual environment's langgraph command
        script_dir = Path(__file__).parent.absolute()
        langgraph_cmd = script_dir / "venv" / "bin" / "langgraph"
        
        if not langgraph_cmd.exists():
            print("⚠️  LangGraph CLI not found in virtual environment")
            print("💡 Try running: pip install langgraph-cli")
            return None
        
        # Change to server directory for langgraph
        original_dir = os.getcwd()
        script_dir = Path(__file__).parent.absolute()
        server_dir = script_dir / "server"
        os.chdir(str(server_dir))
        
        # Start LangGraph Studio
        print("🎨 Starting LangGraph Studio on port 2024...")
        process = subprocess.Popen([
            str(langgraph_cmd), "dev", "--config", "langgraph.json"
        ], stdout=None, stderr=None, env=env)
        
        # Return to original directory
        os.chdir(original_dir)
        
        print("✅ LangGraph Studio started")
        return process
        
    except Exception as e:
        print(f"⚠️  Warning: Could not start LangGraph Studio: {e}")
        return None

def print_summary(fastapi_process, studio_process):
    """Print summary of running services"""
    print()
    print("🎉" + "="*70 + "🎉")
    print("    ALL SERVICES STARTED SUCCESSFULLY!")
    print("="*74)
    print()
    print("📍 Access Points:")
    print("   🔐 FastAPI Auth API:     http://localhost:8000")
    print("   📚 API Documentation:    http://localhost:8000/docs")
    print("   🎨 LangGraph Studio:     http://localhost:2024")
    print("   🎨 Studio UI:            https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024")
    print("   🍃 MongoDB:              mongodb://admin:trip_planner_pass@localhost:27017/")
    
    print()
    print("🔐 Authentication:")
    print("   📱 Facebook Login:       http://localhost:8000/auth/facebook/login")
    print("   🔑 Login Endpoint:       http://localhost:8000/auth/login")
    print("   👤 User Profile:         http://localhost:8000/auth/me")
    print("   📋 Auth Status:          http://localhost:8000/auth/status")
    
    print()
    print("🎯 Trip Planning:")
    print("   🗺️  Plan Trip:           http://localhost:8000/plan-trip")
    print("   💾 Save Trip:            http://localhost:8000/save-trip")
    print("   📚 User Trips:           http://localhost:8000/user-trips")
    
    print()
    print("🐍 Virtual Environment:")
    print("   📁 Location:             ./venv/")
    print("   🔧 Activate:             source venv/bin/activate")
    print("   📦 Packages:             Isolated in virtual environment")
    
    print()
    print("🍃 MongoDB Cache:")
    print("   🐳 Container:            trip_planner_mongodb")
    print("   💾 Data Volume:          mongodb_data (persistent)")
    print("   🔗 Connection:           mongodb://admin:trip_planner_pass@localhost:27017/")
    print("   📊 Databases:            trip_planner_cache, trip_planner_auth")
    
    print()
    print("🛠️  Available Services:")
    print("   • FastAPI REST API with Facebook Authentication")
    print("   • LangGraph Multi-step Workflow (Trip Planning)")
    print("   • MongoDB-cached API calls (Google, Yelp, Foursquare)")
    print("   • User management and preferences")
    print()
    print("🛑 To stop all services: Press Ctrl+C")
    print("="*74)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 Shutting down services...")
    
    # Stop MongoDB container
    stop_mongodb()
    
    print("👋 All services stopped. Goodbye!")
    sys.exit(0)

def main():
    """Main startup function"""
    print_banner()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
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
        
        # Start FastAPI server
        fastapi_process = start_fastapi_server(venv_python)
        if not fastapi_process:
            print("❌ Cannot continue without FastAPI server")
            sys.exit(1)
        
        # Wait a moment for FastAPI to start
        time.sleep(3)
        
        # Start LangGraph Studio
        studio_process = start_langgraph_studio(venv_python)
        if not studio_process:
            print("⚠️  LangGraph Studio failed to start, but FastAPI is running")
        
        # Print summary
        print_summary(fastapi_process, studio_process)
        
        # Wait for processes
        try:
            # Wait for either process to complete
            while True:
                if fastapi_process.poll() is not None:
                    print("🛑 FastAPI server stopped")
                    break
                if studio_process and studio_process.poll() is not None:
                    print("🛑 LangGraph Studio stopped")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down services...")
            
            # Stop processes
            if fastapi_process:
                fastapi_process.terminate()
            if studio_process:
                studio_process.terminate()
            
            # Stop MongoDB container
            stop_mongodb()
            
            print("👋 All services stopped. Goodbye!")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
    
    finally:
        # Return to original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    main()

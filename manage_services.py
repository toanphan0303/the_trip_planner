#!/usr/bin/env python3
"""
Service Management Script for Trip Planner
Manage Docker containers: MongoDB, Redis, and future services
"""

import sys
import subprocess
import time

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"✅ {description} successful")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} error: {e}")
        return False

def start_mongodb():
    """Start MongoDB container"""
    print("🍃 Starting MongoDB container...")
    
    # Check if already running
    result = subprocess.run([
        "docker", "ps", "--filter", "name=trip_planner_mongodb", "--format", "{{.Names}}"
    ], capture_output=True, text=True)
    
    if "trip_planner_mongodb" in result.stdout:
        print("✅ MongoDB container is already running")
        return True
    
    # Start container
    if run_command("docker-compose up -d mongodb", "Starting MongoDB container"):
        # Wait for MongoDB to be ready
        print("⏳ Waiting for MongoDB to be ready...")
        for attempt in range(30):
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
    
    return False

def stop_mongodb():
    """Stop MongoDB container"""
    print("🛑 Stopping MongoDB container...")
    return run_command("docker-compose stop mongodb", "Stopping MongoDB container")

def restart_mongodb():
    """Restart MongoDB container"""
    print("🔄 Restarting MongoDB container...")
    if stop_mongodb():
        time.sleep(2)
        return start_mongodb()
    return False

def status_mongodb():
    """Show MongoDB container status"""
    print("📊 MongoDB container status:")
    run_command("docker-compose ps mongodb", "Getting container status")

def logs_mongodb():
    """Show MongoDB container logs"""
    print("📋 MongoDB container logs:")
    run_command("docker-compose logs --tail=20 mongodb", "Getting container logs")

def clean_mongodb():
    """Remove MongoDB container and volume (WARNING: destroys data)"""
    print("⚠️  WARNING: This will destroy all MongoDB data!")
    response = input("Are you sure? Type 'yes' to continue: ")
    
    if response.lower() == 'yes':
        print("🧹 Cleaning MongoDB container and data...")
        run_command("docker-compose down -v mongodb", "Removing container and volume")
        print("✅ MongoDB container and data removed")
    else:
        print("❌ Operation cancelled")

# ============================================================================
# Redis Management Functions
# ============================================================================

def start_redis():
    """Start Redis container"""
    print("🔴 Starting Redis container...")
    
    # Check if already running
    result = subprocess.run([
        "docker", "ps", "--filter", "name=trip_planner_redis", "--format", "{{.Names}}"
    ], capture_output=True, text=True)
    
    if "trip_planner_redis" in result.stdout:
        print("✅ Redis container is already running")
        return True
    
    # Start container
    if run_command("docker-compose up -d redis", "Starting Redis container"):
        # Wait for Redis to be ready
        print("⏳ Waiting for Redis to be ready...")
        for attempt in range(15):
            result = subprocess.run([
                "docker-compose", "exec", "-T", "redis", 
                "redis-cli", "ping"
            ], capture_output=True, text=True)
            
            if "PONG" in result.stdout:
                print("✅ Redis is ready!")
                return True
            
            time.sleep(1)
        
        print("❌ Redis failed to start within 15 seconds")
        return False
    
    return False

def stop_redis():
    """Stop Redis container"""
    print("🛑 Stopping Redis container...")
    return run_command("docker-compose stop redis", "Stopping Redis container")

def restart_redis():
    """Restart Redis container"""
    print("🔄 Restarting Redis container...")
    if stop_redis():
        time.sleep(1)
        return start_redis()
    return False

def status_redis():
    """Show Redis container status"""
    print("📊 Redis container status:")
    run_command("docker-compose ps redis", "Getting container status")

def logs_redis():
    """Show Redis container logs"""
    print("📋 Redis container logs:")
    run_command("docker-compose logs --tail=20 redis", "Getting container logs")

def clean_redis():
    """Remove Redis container and volume (WARNING: destroys data)"""
    print("⚠️  WARNING: This will destroy all Redis data (ephemeral overlays)!")
    response = input("Are you sure? Type 'yes' to continue: ")
    
    if response.lower() == 'yes':
        print("🧹 Cleaning Redis container and data...")
        run_command("docker-compose down redis", "Removing Redis container")
        run_command("docker volume rm the_trip_planner_redis_data", "Removing Redis volume")
        print("✅ Redis container and data removed")
    else:
        print("❌ Operation cancelled")

# ============================================================================
# Combined Management Functions
# ============================================================================

def start_all():
    """Start both MongoDB and Redis containers"""
    print("🚀 Starting all database containers...")
    success = True
    success &= start_mongodb()
    success &= start_redis()
    if success:
        print("\n✅ All containers started successfully!")
    return success

def stop_all():
    """Stop both containers"""
    print("🛑 Stopping all database containers...")
    stop_mongodb()
    stop_redis()
    print("✅ All containers stopped")

def status_all():
    """Show status of all containers"""
    print("📊 Database Services Status:")
    print("=" * 60)
    run_command("docker-compose ps mongodb redis", "Getting all container status")

def logs_all():
    """Show logs from all containers"""
    print("📋 All Container Logs:")
    print("=" * 60)
    run_command("docker-compose logs --tail=20 mongodb redis", "Getting all logs")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("🐳 Service Management Script")
        print("Manage Docker containers for Trip Planner")
        print()
        print("Manage All Services:")
        print("  python manage_services.py start     - Start all containers")
        print("  python manage_services.py stop      - Stop all containers")
        print("  python manage_services.py status    - Show status of all")
        print("  python manage_services.py logs      - Show logs from all")
        print()
        print("Manage Individual Services:")
        print("  MongoDB (Permanent Data):")
        print("    python manage_services.py mongodb:start")
        print("    python manage_services.py mongodb:stop")
        print("    python manage_services.py mongodb:restart")
        print("    python manage_services.py mongodb:status")
        print("    python manage_services.py mongodb:logs")
        print("    python manage_services.py mongodb:clean    - ⚠️  Destroys data!")
        print()
        print("  Redis (Ephemeral Data):")
        print("    python manage_services.py redis:start")
        print("    python manage_services.py redis:stop")
        print("    python manage_services.py redis:restart")
        print("    python manage_services.py redis:status")
        print("    python manage_services.py redis:logs")
        print("    python manage_services.py redis:clean      - ⚠️  Destroys data!")
        print()
        print("Examples:")
        print("  python manage_services.py start            # Start everything")
        print("  python manage_services.py mongodb:status   # Check MongoDB only")
        print("  python manage_services.py redis:logs       # View Redis logs")
        return
    
    command = sys.argv[1].lower()
    
    # Handle service-specific commands (mongodb:start, redis:stop, etc.)
    if ":" in command:
        service, action = command.split(":", 1)
        
        if service == "mongodb":
            if action == "start":
                start_mongodb()
            elif action == "stop":
                stop_mongodb()
            elif action == "restart":
                restart_mongodb()
            elif action == "status":
                status_mongodb()
            elif action == "logs":
                logs_mongodb()
            elif action == "clean":
                clean_mongodb()
            else:
                print(f"❌ Unknown MongoDB command: {action}")
        
        elif service == "redis":
            if action == "start":
                start_redis()
            elif action == "stop":
                stop_redis()
            elif action == "restart":
                restart_redis()
            elif action == "status":
                status_redis()
            elif action == "logs":
                logs_redis()
            elif action == "clean":
                clean_redis()
            else:
                print(f"❌ Unknown Redis command: {action}")
        
        else:
            print(f"❌ Unknown service: {service}")
            print("Valid services: mongodb, redis")
    
    # Handle combined commands (start, stop, status, logs)
    else:
        if command == "start":
            start_all()
        elif command == "stop":
            stop_all()
        elif command == "status":
            status_all()
        elif command == "logs":
            logs_all()
        else:
            print(f"❌ Unknown command: {command}")
            print("Run without arguments to see usage")

if __name__ == "__main__":
    main()

import os
import subprocess
import sys

class DevelopmentServer:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 8000
        self.reload = True
    
    def start(self):
        print("Starting development server...")
        os.chdir('backend')
        subprocess.run([
            'python3', '-m', 'uvicorn', 
            'main:app', 
            '--host', self.host,
            '--port', str(self.port),
            '--reload' if self.reload else ''
        ])

class ProductionServer:
    def __init__(self):
        self.host = "0.0.0.0"
        self.port = 8000
        self.reload = False
    
    def start(self):
        print("Starting production server...")
        os.chdir('backend')
        subprocess.run([
            'python3', '-m', 'uvicorn', 
            'main:app', 
            '--host', self.host,
            '--port', str(self.port)
        ])

if __name__ == "__main__":
    # Default to development
    environment = sys.argv[1] if len(sys.argv) > 1 else "development"
    
    if environment == "production":
        ProductionServer().start()
    else:
        DevelopmentServer().start()
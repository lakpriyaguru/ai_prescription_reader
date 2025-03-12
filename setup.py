import os
import subprocess
import sys

PYTHON_VERSION = "py -3.12"  # Change to python3.12 if on Mac/Linux
VENV_NAME = ".myenv"

def run_command(command):
    """Run a system command and check for errors."""
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"❌ Error executing: {command}")
        sys.exit(1)

def create_virtual_env():
    """Create a virtual environment using Python 3.12.6."""
    print(f"⚙️ Creating virtual environment with {PYTHON_VERSION}...")
    run_command(f"{PYTHON_VERSION} -m venv {VENV_NAME}")

def activate_virtual_env():
    """Print activation instructions."""
    print("\n✅ Virtual environment created! To activate it manually, run:")
    if os.name == "nt":  # Windows
        print(f"   {VENV_NAME}\\Scripts\\activate")
    else:  # Mac/Linux
        print(f"   source {VENV_NAME}/bin/activate")

def install_dependencies():
    """Install dependencies from requirements.txt."""
    pip_exec = os.path.join(VENV_NAME, "Scripts" if os.name == "nt" else "bin", "pip")
    
    if not os.path.exists("requirements.txt"):
        print("⚠️ requirements.txt not found. Skipping dependency installation.")
        return
    
    print("📦 Installing dependencies from requirements.txt...")
    run_command(f"{pip_exec} install -r requirements.txt")

def main():
    create_virtual_env()
    activate_virtual_env()
    install_dependencies()

if __name__ == "__main__":
    main()

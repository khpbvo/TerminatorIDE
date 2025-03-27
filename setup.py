import os
import platform
import subprocess
import sys

from setuptools import find_packages, setup


def main():
    print("Setting up TerminatorIDE development environment...")

    # Create virtual environment
    if not os.path.exists("venv"):
        print("Creating virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
    else:
        print("Virtual environment already exists.")

    # Activate virtual environment and install dependencies
    if platform.system() == "Windows":
        activate_script = os.path.join("venv", "Scripts", "activate")
        pip_path = os.path.join("venv", "Scripts", "pip")
    else:
        activate_script = os.path.join("venv", "bin", "activate")
        pip_path = os.path.join("venv", "bin", "pip")

    print("Installing dependencies...")
    if platform.system() == "Windows":
        subprocess.check_call([pip_path, "install", "-r", "requirements.txt"])
    else:
        subprocess.check_call(
            f"source {activate_script} && pip install -r requirements.txt", shell=True
        )

    print("\nSetup complete! To activate the virtual environment:")
    if platform.system() == "Windows":
        print(f"    {os.path.join('venv', 'Scripts', 'activate')}")
    else:
        print(f"    source {os.path.join('venv', 'bin', 'activate')}")

    print("\nTo run the application:")
    print("    python -m src.terminatoride.app")


setup(
    name="terminatoride",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)

if __name__ == "__main__":
    main()

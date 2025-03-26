"""
Setup script for the Spring Test App.
"""
import os
import sys
import subprocess
from setuptools import setup, find_packages

# Check Python version
if sys.version_info < (3, 7):
    print("This application requires Python 3.7 or higher.")
    sys.exit(1)

# Make sure requirements are installed
try:
    with open('requirements.txt', 'r') as f:
        requirements = f.read().splitlines()
    
    print("Installing required packages...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
    print("All requirements installed successfully!")
except Exception as e:
    print(f"Error installing requirements: {e}")
    sys.exit(1)

# Create necessary directories
dirs = ['logs', 'exports', 'templates']
for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"Directory '{d}' created or already exists.")

# Setup configuration
setup(
    name="spring_test_app",
    version="0.1.0",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'spring-test=main:main',
        ],
    },
    python_requires='>=3.7',
    author="Sushma",
    description="A Spring Test App with AI capabilities",
    license="MIT",
)

print("\nSetup completed successfully!")
print("You can now run the application with 'python main.py'")
print("Or build an executable with 'python build_exe.py'") 
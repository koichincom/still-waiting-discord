#!/usr/bin/env python3
"""
Test runner script for the Discord bot project using uv.

This script runs all tests and provides a convenient interface for testing.
"""

import sys
import subprocess
import os
from pathlib import Path

def run_tests():
    """Run all tests using uv and pytest."""
    
    # Get the project root directory (parent of tests folder)
    project_root = Path(__file__).parent.parent
    
    # Change to project root
    os.chdir(project_root)
    
    # Basic test command using uv
    cmd = [
        "uv", "run", "pytest",
        "tests/",
        "-v",
        "--tb=short"
    ]
    
    print("Running Discord bot tests with uv...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except FileNotFoundError:
        print("Error: uv not found. Please install uv:")
        print("curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("or visit: https://docs.astral.sh/uv/getting-started/installation/")
        return False

def run_specific_test(test_file=None, test_function=None):
    """Run a specific test file or function using uv."""
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    cmd = ["uv", "run", "pytest", "-v"]
    
    if test_file:
        if test_function:
            cmd.append(f"tests/{test_file}::{test_function}")
        else:
            cmd.append(f"tests/{test_file}")
    
    print(f"Running specific test with uv: {' '.join(cmd[3:])}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except FileNotFoundError:
        print("Error: uv not found. Please install uv first.")
        return False

def install_deps():
    """Install test dependencies using uv."""
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    cmd = ["uv", "sync", "--dev"]
    
    print("Installing dependencies with uv...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except FileNotFoundError:
        print("Error: uv not found. Please install uv first.")
        return False

def main():
    """Main function to handle command line arguments."""
    
    if len(sys.argv) == 1:
        # Run all tests
        success = run_tests()
        sys.exit(0 if success else 1)
    
    elif sys.argv[1] == "install":
        # Install dependencies
        success = install_deps()
        sys.exit(0 if success else 1)
    
    elif len(sys.argv) == 2:
        # Run specific test file
        test_file = sys.argv[1]
        if not test_file.startswith("test_"):
            test_file = f"test_{test_file}"
        if not test_file.endswith(".py"):
            test_file = f"{test_file}.py"
        
        success = run_specific_test(test_file)
        sys.exit(0 if success else 1)
    
    elif len(sys.argv) == 3:
        # Run specific test function
        test_file, test_function = sys.argv[1], sys.argv[2]
        if not test_file.startswith("test_"):
            test_file = f"test_{test_file}"
        if not test_file.endswith(".py"):
            test_file = f"{test_file}.py"
        
        success = run_specific_test(test_file, test_function)
        sys.exit(0 if success else 1)
    
    else:
        print("Usage:")
        print("  python run_tests.py                    # Run all tests")
        print("  python run_tests.py install           # Install dependencies")
        print("  python run_tests.py test_file         # Run specific test file")
        print("  python run_tests.py test_file test_func # Run specific test function")
        print()
        print("Examples:")
        print("  python tests/run_tests.py")
        print("  python tests/run_tests.py install")
        print("  python tests/run_tests.py db")
        print("  python tests/run_tests.py test_db.py")
        print("  python tests/run_tests.py db test_save_message")
        sys.exit(1)

if __name__ == "__main__":
    main()

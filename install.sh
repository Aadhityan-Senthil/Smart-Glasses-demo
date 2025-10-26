#!/bin/bash

# Smart Glasses Demo - Installation Script
# This script sets up the complete system with all dependencies

set -e

echo "🤖 Smart Glasses Demo - Installation Script"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.8+ is installed
check_python() {
    print_status "Checking Python version..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
        REQUIRED_VERSION="3.8"
        
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            print_success "Python $PYTHON_VERSION found"
        else
            print_error "Python 3.8+ is required. Current version: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 is not installed. Please install Python 3.8+ first."
        exit 1
    fi
}

# Install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            # Debian/Ubuntu
            sudo apt-get update
            sudo apt-get install -y python3-pip python3-venv python3-dev
            sudo apt-get install -y libopencv-dev python3-opencv
            sudo apt-get install -y ffmpeg libsm6 libxext6
        elif command -v yum &> /dev/null; then
            # RHEL/CentOS
            sudo yum install -y python3-pip python3-devel
            sudo yum install -y opencv-python ffmpeg
        elif command -v pacman &> /dev/null; then
            # Arch Linux
            sudo pacman -S python-pip opencv ffmpeg
        else
            print_warning "Unknown Linux distribution. Please install dependencies manually."
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install python@3.11 opencv ffmpeg
        else
            print_error "Homebrew is not installed. Please install it first: https://brew.sh/"
            exit 1
        fi
    else
        print_warning "Unknown operating system. Please install dependencies manually."
    fi
    
    print_success "System dependencies installed"
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Removing old one..."
        rm -rf venv
    fi
    
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    print_success "Virtual environment created and activated"
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    # Ensure we're in the virtual environment
    source venv/bin/activate
    
    # Install PyTorch first (CPU version by default)
    if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
        print_status "NVIDIA GPU detected. Installing PyTorch with CUDA support..."
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
    else
        print_status "Installing PyTorch with CPU support..."
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    fi
    
    # Install other requirements
    pip install -r requirements.txt
    
    print_success "Python dependencies installed"
}

# Create configuration file
setup_config() {
    print_status "Setting up configuration..."
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_success "Configuration file created from template"
        print_warning "Please edit .env file with your Telegram bot credentials"
    else
        print_warning "Configuration file already exists"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p videos processed logs models
    
    print_success "Directory structure created"
}

# Set permissions
set_permissions() {
    print_status "Setting file permissions..."
    
    chmod +x main.py
    chmod +x install.sh
    
    print_success "Permissions set"
}

# Test installation
test_installation() {
    print_status "Testing installation..."
    
    source venv/bin/activate
    
    # Test imports
    python3 -c "
import cv2
import torch
import numpy as np
import telegram
from ultralytics import YOLO
print('✅ All critical imports successful')
"
    
    print_success "Installation test passed"
}

# Display next steps
show_next_steps() {
    echo ""
    echo "🎉 Installation completed successfully!"
    echo "======================================"
    echo ""
    echo "Next steps:"
    echo "1. Edit the .env file with your Telegram bot credentials:"
    echo "   nano .env"
    echo ""
    echo "2. Activate the virtual environment:"
    echo "   source venv/bin/activate"
    echo ""
    echo "3. Run the demo:"
    echo "   python main.py --mode demo"
    echo ""
    echo "4. For production use:"
    echo "   python main.py --mode monitor"
    echo ""
    echo "5. Access web interface:"
    echo "   http://localhost:8000"
    echo ""
    echo "For more information, see README.md"
}

# Main installation process
main() {
    print_status "Starting Smart Glasses Demo installation..."
    
    # Check if we're in the right directory
    if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
        print_error "Please run this script from the smart-glasses-demo directory"
        exit 1
    fi
    
    check_python
    install_system_deps
    create_venv
    install_python_deps
    setup_config
    create_directories
    set_permissions
    test_installation
    show_next_steps
    
    print_success "Installation completed successfully! 🎉"
}

# Handle script interruption
trap 'print_error "Installation interrupted"; exit 1' INT

# Run main installation
main "$@"

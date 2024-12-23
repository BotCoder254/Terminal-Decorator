#!/bin/bash

# Terminal Decorator Installation Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Terminal Decorator Installation${NC}"
echo "=============================="

# Check Python version
echo -e "\n${YELLOW}Checking Python version...${NC}"
if command -v python3 >/dev/null 2>&1; then
    python3 --version
else
    echo -e "${RED}Python 3 is not installed. Please install Python 3.7 or later.${NC}"
    exit 1
fi

# Create virtual environment
echo -e "\n${YELLOW}Creating virtual environment...${NC}"
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
echo -e "\n${YELLOW}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Create configuration directory
echo -e "\n${YELLOW}Setting up configuration...${NC}"
CONFIG_DIR="$HOME/.terminal_decorator"
mkdir -p "$CONFIG_DIR"
mkdir -p "$CONFIG_DIR/backups"

# Copy configuration files
echo -e "\n${YELLOW}Copying configuration files...${NC}"
cp config.yaml "$CONFIG_DIR/"
cp custom_themes.yaml "$CONFIG_DIR/"
cp animation_config.yaml "$CONFIG_DIR/"
cp text_config.yaml "$CONFIG_DIR/"

# Set permissions
echo -e "\n${YELLOW}Setting permissions...${NC}"
chmod 700 "$CONFIG_DIR"
chmod 600 "$CONFIG_DIR"/*.yaml

# Create shell integration
echo -e "\n${YELLOW}Setting up shell integration...${NC}"
SHELL_RC="$HOME/.$(basename $SHELL)rc"
if [ -f "$SHELL_RC" ]; then
    # Backup existing rc file
    cp "$SHELL_RC" "$CONFIG_DIR/backups/$(basename $SHELL_RC).backup"
    
    # Add terminal decorator to shell rc
    echo "" >> "$SHELL_RC"
    echo "# Terminal Decorator Integration" >> "$SHELL_RC"
    echo "source $(pwd)/terminal_integration.sh" >> "$SHELL_RC"
fi

# Create executable
echo -e "\n${YELLOW}Creating executable...${NC}"
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/terminal-decorator" << 'EOF'
#!/bin/bash
source "$(dirname $(readlink -f $0))/../.terminal_decorator/.venv/bin/activate"
python3 "$(dirname $(readlink -f $0))/../.terminal_decorator/setup_manager.py" "$@"
EOF
chmod +x "$HOME/.local/bin/terminal-decorator"

# Copy program files
echo -e "\n${YELLOW}Installing program files...${NC}"
cp *.py "$CONFIG_DIR/"
cp terminal_integration.sh "$CONFIG_DIR/"

echo -e "\n${GREEN}Installation complete!${NC}"
echo -e "To start using Terminal Decorator, please:"
echo -e "1. Restart your terminal or run: source $SHELL_RC"
echo -e "2. Run: terminal-decorator"
echo -e "\nFor help and documentation, visit: https://github.com/yourusername/terminal-decorator" 
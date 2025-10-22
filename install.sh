#!/bin/bash
NVM_VERSION="0.39.3"
NVM_URL="https://cdn.pisugar.com/PiSugar-wificonfig/script/nvm/v$NVM_VERSION.tar.gz"
NPM_REGISTRY="https://registry.npmmirror.com"
NODE_BINARY_INSTALL_URL="https://cdn.pisugar.com/PiSugar-wificonfig/script/node-binary/install-node-v18.19.1.sh"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install nvm and Node.js 18
install_node_nvm() {
    echo "Installing Node.js 18 using nvm..."
    
    # Install nvm if it's not already installed
    if [ ! -d "$HOME/.nvm" ]; then
        echo "Installing nvm..."
        TEMP_DIR=$(mktemp -d)
        curl -o $TEMP_DIR/nvm-$NVM_VERSION.tar.gz -L $NVM_URL
        tar -xzf $TEMP_DIR/nvm-$NVM_VERSION.tar.gz -C $TEMP_DIR
        mv $TEMP_DIR/nvm-$NVM_VERSION $HOME/.nvm
        rm -rf $TEMP_DIR

        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

        # check if nvm is in the bash profile
        if ! grep -q "nvm" $HOME/.bashrc; then
            echo "export NVM_DIR=\"$HOME/.nvm\"" >> $HOME/.bashrc
            echo "[ -s \"\$NVM_DIR/nvm.sh\" ] && \. \"\$NVM_DIR/nvm.sh\"" >> $HOME/.bashrc
            echo "[ -s \"\$NVM_DIR/bash_completion\" ] && \. \"\$NVM_DIR/bash_completion\"" >> $HOME/.bashrc
        fi
    else
        echo "nvm is already installed."
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
    fi

    # Install and use Node.js 18
    echo "Swith to Node.js 18"
    nvm install 18
    nvm use 18

    # Verify installation
    if command_exists node && [[ "$(node -v)" =~ ^v18 ]]; then
        echo "Node.js 18 installed successfully."
    else
        echo "Failed to install Node.js 18."
        exit 1
    fi
}

install_node_binary() {
    echo "Installing Node.js 18 for pi zero..."
    TEMP_DIR=$(mktemp -d)
    curl -o $TEMP_DIR/install-node-v18.19.1.sh -L $NODE_BINARY_INSTALL_URL
    chmod +x $TEMP_DIR/install-node-v18.19.1.sh
    sudo bash $TEMP_DIR/install-node-v18.19.1.sh
    rm -rf $TEMP_DIR

    # Verify installation
    if command_exists node && [[ "$(node -v)" =~ ^v18 ]]; then
        echo "Node.js 18 installed successfully."
    else
        echo "Failed to install Node.js 18."
        exit 1
    fi
}

install_node() {
    if [[ "$(uname -m)" == "armv6l" ]]; then
        install_node_binary
    else
        install_node_nvm
    fi
}

# Check if Node.js is installed and is version 18
if command_exists node; then
    NODE_VERSION=$(node -v)
    if [[ "$NODE_VERSION" =~ ^v18 ]]; then
        echo "Node.js 18 is already installed."
    else
        echo "Different version of Node.js detected: $NODE_VERSION"
        install_node
    fi
else
    echo "Node.js is not installed."
    install_node
fi

# Check if npm is installed
if ! command_exists npm; then
    echo "npm is not installed. Installing npm..."
    sudo apt-get install -y npm

    # Verify installation
    if command_exists npm; then
        echo "npm installed successfully."
    else
        echo "Failed to install npm."
        exit 1
    fi
fi

# check if git is installed
# if ! command_exists git; then
#     echo "git is not installed. Installing git..."
#     sudo apt-get install -y git

#     # Verify installation
#     if command_exists git; then
#         echo "git installed successfully."
#     else
#         echo "Failed to install git."
#         exit 1
#     fi
# fi

# check if yarn is installed
if ! command_exists yarn; then
    echo "yarn is not installed. Installing yarn..."
    npm config set registry $NPM_REGISTRY
    npm install -g yarn
    export PATH="$HOME/.yarn/bin:$HOME/.config/yarn/global/node_modules/.bin:$PATH"

    # Verify installation
    if command_exists yarn; then
        echo "yarn installed successfully."
    else
        echo "Failed to install yarn."
        exit 1
    fi
fi

#sudo ln -s "$NVM_DIR/versions/node/$(nvm version)/bin/node" "/usr/local/bin/node"
#sudo ln -s "$NVM_DIR/versions/node/$(nvm version)/bin/npm" "/usr/local/bin/npm"
#sudo ln -s "$NVM_DIR/versions/node/$(nvm version)/bin/npx" "/usr/local/bin/npx"

echo "Installing dependencies..."
yarn --registry=$NPM_REGISTRY


# apt install sox libsox-fmt-mp3 mpg123
sudo apt-get update
sudo apt-get install -y sox mpg123
sudo apt-get install -y libsox-fmt-mp3




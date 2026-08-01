#!/usr/bin/env sh
# compman Linux/macOS One-Line Automatic Installer
set -e

echo "🚀 Installing compman CLI..."

if command -v uv >/dev/null 2>&1; then
    uv tool install --reinstall git+https://github.com/allbegray/compman.git
elif command -v pip >/dev/null 2>&1; then
    pip install --upgrade git+https://github.com/allbegray/compman.git
else
    echo "Error: Neither 'uv' nor 'pip' was found. Please install Python or uv first." >&2
    exit 1
fi

BIN_DIR="$HOME/.local/bin"
case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *)
        PROFILE=""
        if [ -n "$ZSH_VERSION" ] || [ -f "$HOME/.zshrc" ]; then
            PROFILE="$HOME/.zshrc"
        elif [ -f "$HOME/.bashrc" ]; then
            PROFILE="$HOME/.bashrc"
        fi

        if [ -n "$PROFILE" ]; then
            echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$PROFILE"
            echo "✅ Automatically added $BIN_DIR to $PROFILE"
        fi
        export PATH="$BIN_DIR:$PATH"
        ;;
esac

if command -v compman >/dev/null 2>&1; then
    if [ -n "$ZSH_VERSION" ] || [ -f "$HOME/.zshrc" ]; then
        compman completion zsh --install >/dev/null 2>&1 || true
    elif [ -f "$HOME/.bashrc" ]; then
        compman completion bash --install >/dev/null 2>&1 || true
    fi
fi

echo "\n🎉 compman installed successfully! Run 'compman --help' to get started.\n"

#!/bin/bash

# Get the absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Define the line to add to the shell configuration
PYTHONPATH_EXPORT="export PYTHONPATH=\"$PROJECT_ROOT/src:\$PYTHONPATH\""

# Determine the appropriate shell configuration file
SHELL_CONFIG="$HOME/.bashrc"
[[ "$SHELL" =~ zsh ]] && SHELL_CONFIG="$HOME/.zshrc"

# Check if the line already exists in the shell configuration
if grep -Fxq "$PYTHONPATH_EXPORT" "$SHELL_CONFIG"; then
    echo "PYTHONPATH is already configured in $SHELL_CONFIG."
else
    # Append the export command to the shell configuration file
    echo "$PYTHONPATH_EXPORT" >> "$SHELL_CONFIG"
    echo "PYTHONPATH added to $SHELL_CONFIG. Restart your terminal or run 'source $SHELL_CONFIG' to apply."
fi

# Display the current PYTHONPATH
echo "PYTHONPATH set to: $PROJECT_ROOT/src"

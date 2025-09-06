#!/bin/bash
# start-dev.sh

echo "Starting Redis server..."
sudo service redis-server start

echo "Starting development environment..."
# 使用wslpath将WSL路径转换为Windows路径
CURRENT_DIR=$(wslpath -w "$(pwd)")

# 通过PowerShell执行
powershell.exe -ExecutionPolicy Bypass -File "run.ps1"

echo "Development environment started!"
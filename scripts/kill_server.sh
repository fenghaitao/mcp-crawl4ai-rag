#!/bin/bash
#
# Emergency kill script for the MCP server
# Use this if CTRL+C doesn't work
#

echo "🔍 Finding MCP server processes..."
pids=$(pgrep -f "crawl4ai_mcp.py")

if [ -z "$pids" ]; then
    echo "❌ No MCP server processes found"
    exit 1
fi

echo "📍 Found processes: $pids"
for pid in $pids; do
    echo "💀 Killing process $pid..."
    kill -9 $pid 2>/dev/null && echo "✅ Process $pid killed" || echo "⚠️  Process $pid already dead"
done

echo "🧹 Cleaning up any remaining python processes with crawl4ai..."
pkill -f "crawl4ai_mcp" && echo "✅ Additional cleanup completed" || echo "📝 No additional processes to clean"

echo "✅ Server kill completed!"

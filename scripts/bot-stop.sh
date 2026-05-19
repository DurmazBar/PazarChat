#!/usr/bin/env bash
# PazarChat Bot — Background daemon'u durdur
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BOT_DIR="$PROJECT_ROOT/telegram-bot"
PID_FILE="$BOT_DIR/bot.pid"
CAFFEINATE_PID_FILE="$BOT_DIR/caffeinate.pid"

stopped_any=0

# Bot process
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        echo "✓ Bot durduruldu (PID: $PID)"
        stopped_any=1
    else
        echo "ℹ  Bot PID $PID çalışmıyordu (eski PID dosyası)"
    fi
    rm -f "$PID_FILE"
fi

# Caffeinate process (bot bittiğinde otomatik durur ama temizlik için)
if [ -f "$CAFFEINATE_PID_FILE" ]; then
    CPID=$(cat "$CAFFEINATE_PID_FILE")
    if kill -0 "$CPID" 2>/dev/null; then
        kill "$CPID" 2>/dev/null || true
        echo "✓ caffeinate durduruldu (PID: $CPID) — Mac normal uyku davranışına döndü"
    fi
    rm -f "$CAFFEINATE_PID_FILE"
fi

if [ "$stopped_any" -eq 0 ]; then
    echo "ℹ  PID dosyası yok, bot zaten çalışmıyor"
fi

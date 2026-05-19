#!/usr/bin/env bash
# PazarChat Bot — Durum kontrolü
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BOT_DIR="$PROJECT_ROOT/telegram-bot"
PID_FILE="$BOT_DIR/bot.pid"
LOG_FILE="$BOT_DIR/logs/bot.log"

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    PID=$(cat "$PID_FILE")
    # macOS ps formatı
    ELAPSED=$(ps -p "$PID" -o etime= 2>/dev/null | tr -d ' ' || echo "?")
    echo "🟢 Bot çalışıyor"
    echo "   PID:     $PID"
    echo "   Uptime:  $ELAPSED"
    echo "   Log:     $LOG_FILE"
    echo ""
    echo "📜 Son 10 log satırı:"
    if [ -f "$LOG_FILE" ]; then
        tail -10 "$LOG_FILE" | sed 's/^/   /'
    else
        echo "   (log dosyası henüz yok)"
    fi
else
    echo "🔴 Bot çalışmıyor"
    if [ -f "$PID_FILE" ]; then
        echo "   Eski PID dosyası bulundu ($(cat "$PID_FILE")) — temizleniyor"
        rm -f "$PID_FILE"
    fi
    echo "   Başlatmak için: ./scripts/bot-start.sh"
fi

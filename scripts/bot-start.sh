#!/usr/bin/env bash
# =============================================================================
# PazarChat Bot — Mac'te background daemon olarak başlat
# =============================================================================
# Bu script bot'u "headless" modda başlatır:
#   - nohup ile parent process'ten bağımsız (terminal kapatınca devam eder)
#   - stdin /dev/null'a yönlendirilir (orphan process güvenli)
#   - stdout/stderr logs/bot.log'a yazılır
#   - caffeinate ile Mac bot çalıştığı sürece uyku moduna giremez
#   - PID dosyaya kaydedilir → stop/status için
#
# Kullanım:
#   ./scripts/bot-start.sh        # bot'u başlat
#   ./scripts/bot-status.sh       # çalışıyor mu?
#   ./scripts/bot-stop.sh         # durdur
# =============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BOT_DIR="$PROJECT_ROOT/telegram-bot"
PID_FILE="$BOT_DIR/bot.pid"
LOG_FILE="$BOT_DIR/logs/bot.log"
CAFFEINATE_PID_FILE="$BOT_DIR/caffeinate.pid"

# Halihazırda çalışıyor mu?
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "⚠  Bot zaten çalışıyor (PID: $(cat "$PID_FILE"))"
    echo "   Durdurmak için: ./scripts/bot-stop.sh"
    exit 1
fi

# venv kontrolü
if [ ! -d "$BOT_DIR/venv" ]; then
    echo "❌ venv bulunamadı: $BOT_DIR/venv"
    echo "   Önce: cd telegram-bot && python3.12 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# .env kontrolü
if [ ! -f "$BOT_DIR/.env" ]; then
    echo "❌ .env bulunamadı: $BOT_DIR/.env"
    echo "   Önce .env.example'ı .env olarak kopyala ve doldur"
    exit 1
fi

# Log klasörü
mkdir -p "$(dirname "$LOG_FILE")"

# Bot'u background'da başlat
cd "$BOT_DIR"
# shellcheck disable=SC1091
source venv/bin/activate

nohup python main.py > "$LOG_FILE" 2>&1 < /dev/null &
BOT_PID=$!
disown
echo "$BOT_PID" > "$PID_FILE"

# 2 saniye bekle — başlangıçta crash olursa öğren
sleep 2
if ! kill -0 "$BOT_PID" 2>/dev/null; then
    echo "❌ Bot başlayamadı, log:"
    tail -20 "$LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi

echo "✓ Bot başlatıldı (PID: $BOT_PID)"
echo "  Log: $LOG_FILE"

# Mac uyku moduna girmesini engelle (sadece bot süresince)
# -i: idle sleep prevent (CPU dahil)
# -w PID: belirtilen process bittiğinde caffeinate de durur
caffeinate -i -w "$BOT_PID" > /dev/null 2>&1 &
CAFFEINATE_PID=$!
disown
echo "$CAFFEINATE_PID" > "$CAFFEINATE_PID_FILE"
echo "✓ Mac uyku moduna girmesi engellendi (caffeinate PID: $CAFFEINATE_PID)"

echo ""
echo "📋 Komutlar:"
echo "  Durum:  ./scripts/bot-status.sh"
echo "  Log:    tail -f $LOG_FILE"
echo "  Durdur: ./scripts/bot-stop.sh"

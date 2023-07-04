#!/bin/bash
# The execution of this file is intented to be handled by cronie or similar with the following config (path to this file):
# */1 * * * * ~/crypto-trading/check_bot_running.sh

folder="$HOME/logs_bot_failed"

check_and_create_folder() {
  if [ ! -d "$folder" ]; then
    mkdir "$folder"
    echo "The folder '$folder' has been created."
  fi
}

if [[ ! $(pgrep -f "python services.py") ]]
then
    check_and_create_folder
    cd ~/crypto-trading/ && source venv/bin/activate && cd src/
    bot_log_path=$(python -c "import commonutils as cu; print(cu.log_file_path)")
    log_tail=$(tail $bot_log_path)
    msg="El bot se ha parado. Se ha guardado el log y se va a intentar lanzarlo otra vez. Tail del archivo de log:  $log_tail"
    python -c "import externalnotifier as en; import sys; en.externally_notify(sys.argv[1])" "$msg"
    mv "$HOME/botlog.log" "$folder/botlog - $(date '+%Y-%m-%d_%H:%M:%S')"
    python services.py &
fi


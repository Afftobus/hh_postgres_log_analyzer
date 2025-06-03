#!/bin/bash

# Параметры подключения
DB_HOST=$TARGET_TEST_STAND
DB_NAME="DB_NAME"
DB_USER="DB_USER"
DB_PASS="DB_PASS"

# место на локальной машине, где будут производиться все манипуляции
LOCAL_TMP_LOG_DIR="/tmp/pg_logging"

# место, куда скопируется файл отчета после формирования. Он будет каждый раз перезаписываться
DEST_PATH_FOR_COPY_REPORT="/home/user/.config/JetBrains/IntelliJIdea/scratches"

# папка с логами БД, которые мы будем таскать
PATH_TO_LOGS_AT_REMOTE_DB_HOST="/var/log/"

# путь к файлу log_analyzer.py
PATH_TO_ANALYZER='/home/user/log_analyzer.py'

# не думаю, что это стоит менять. Вынес сюда, чтобы не дублировать
TIMESTAMP_FILE="$LOCAL_TMP_LOG_DIR/start_time"
LOGGING_PARAMS_BACKUP_FILE="$LOCAL_TMP_LOG_DIR/logging_params_backup.txt"

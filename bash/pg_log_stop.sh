#!/bin/bash

source ./pg_log_settings.sh

BACKUP_DIR="$LOCAL_TMP_LOG_DIR/$(date +"%Y-%m-%d-%H-%M-%S")"

# Восстанавливаем настройки логирования
echo "Восстановление настроек..."
while IFS='=' read -r param value; do
  PGPASSWORD=$DB_PASS psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "ALTER SYSTEM SET $param = '$value';"
done < "$LOGGING_PARAMS_BACKUP_FILE"

# Перезагружаем конфигурацию PostgreSQL
echo "Перезагрузка конфигурации..."
PGPASSWORD=$DB_PASS psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT pg_reload_conf();"

# Получаем время запуска
START_TIME=$(cat $TIMESTAMP_FILE)
echo "Время запуска: $START_TIME"

# Копируем логи через SSH
START_TIMESTAMP=$(date -d "$START_TIME" +"%Y-%m-%d %H:%M:%S")

echo $START_TIMESTAMP

# Создаем локальную директорию
mkdir -p "$BACKUP_DIR"

ssh "$DB_HOST" "find '$PATH_TO_LOGS_AT_REMOTE_DB_HOST' -maxdepth 1 -type f -name 'postgresql-[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]_*.log' -newermt '$START_TIMESTAMP' -print0" | while IFS= read -r -d '' file; do
  scp "$DB_HOST:$file" "$BACKUP_DIR/"
done

if [ $? -eq 0 ]; then
  echo "Файлы, измененные после $DATE, успешно скопированы в $BACKUP_DIR"
else
  echo "Ошибка при копировании файлов"
  exit 1
fi

# Переход в рабочую директорию
cd "$BACKUP_DIR" || { echo "Не удалось перейти в $BACKUP_DIR"; exit 1; }

# 1. Слияние всех файлов в postgresql.log
echo "Создание объединенного файла postgresql.log..."
rm -f postgresql.log  # Удаляем старый файл, если существует
cat * 2>/dev/null > postgresql.log  # Игнорируем ошибки поддиректорий

# Проверка успешности создания
if [ $? -ne 0 ] || [ ! -s postgresql.log ]; then
    echo "Ошибка: не удалось создать postgresql.log или файл пуст."
    exit 1
fi

python3 $PATH_TO_ANALYZER
if [ $? -ne 0 ]; then
    echo "Ошибка при выполнении log_analyzer.py"
    exit 1
fi

# 3. Копирование отчета в папку JetBrains
echo "Копирование transactions.html..."

# Проверка существования файла и целевой директории
if [ ! -f "transactions.html" ]; then
    echo "Ошибка: transactions.html не найден."
    exit 1
fi

if [ ! -d "$DEST_PATH_FOR_COPY_REPORT" ]; then
    echo "Ошибка: директория $DEST_PATH_FOR_COPY_REPORT не существует."
    exit 1
fi

# Копирование с заменой
cp -f transactions.html "$DEST_PATH_FOR_COPY_REPORT/"
if [ $? -eq 0 ]; then
    echo "Файл успешно скопирован в $DEST_PATH_FOR_COPY_REPORT"
else
    echo "Ошибка при копировании в $DEST_PATH_FOR_COPY_REPORT"
    exit 1
fi

echo "Все операции успешно завершены."
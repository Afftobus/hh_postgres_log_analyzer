#!/bin/bash

source ./pg_log_settings.sh

# Сохраняем время запуска
date +"%Y-%m-%d %H:%M:%S" > $TIMESTAMP_FILE

# Сохраняем текущие настройки логирования
echo "Сохранение текущих настроек..."
{
  echo "logging_collector=$(PGPASSWORD=$DB_PASS psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "SHOW logging_collector;" | xargs)"
  echo "log_statement=$(PGPASSWORD=$DB_PASS psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "SHOW log_statement;" | xargs)"
  echo "log_min_duration_statement=$(PGPASSWORD=$DB_PASS psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "SHOW log_min_duration_statement;" | xargs)"
} > /tmp/logging_params_backup.txt

# Включаем расширенное логирование
echo "Включение расширенного логирования..."
PGPASSWORD=$DB_PASS psql -h $DB_HOST -U $DB_USER -d $DB_NAME <<EOF
SELECT pg_rotate_logfile();
ALTER SYSTEM SET logging_collector = 'on';
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 0;
SELECT pg_reload_conf();
EOF

echo "Логирование включено."

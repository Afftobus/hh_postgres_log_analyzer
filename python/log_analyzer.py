import re
from collections import defaultdict
import html  # Импортируем модуль для экранирования HTML

def parse_log_line(line):
    date_pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} MSK)'
    line_parts = re.split(date_pattern, line, 1)
    if len(line_parts) != 3:
        return None

    date_time = line_parts[1].strip()
    rest = line_parts[2].strip()

    # Извлекаем PID, пользователя и IP
    user_pattern = r'^(\d+)\s+([^@]+@[^ ]+)\s+from\s+([^ ]+)'
    user_match = re.match(user_pattern, rest)
    if not user_match:
        return None

    pid = user_match.group(1)
    user = user_match.group(2)
    ip = user_match.group(3)
    rest = rest[user_match.end():].strip()

    vxid_match = re.search(r'vxid:(\d+/\d+)?', rest)
    vxid = vxid_match.group(1) if vxid_match and vxid_match.group(1) else None
    rest = rest[vxid_match.end():].strip()

    # op_type_match = re.search(r'\[([^\]]+)\]', rest)
    op_type_match = re.search(r'\[([A-Za-z ]+)\]', rest)
    op_type = op_type_match.group(1) if op_type_match else 'UNKNOWN'
    rest = rest[op_type_match.end():].strip()

    message = rest.split(']', 1)[-1].strip()

    duration = 0.0
    duration_match = re.search(r'duration: (\d+\.\d+) ms', message)
    if duration_match:
        duration = float(duration_match.group(1))

    return {
        'timestamp': date_time,
        'pid': pid,
        'user': user,
        'ip': ip,
        'vxid': vxid,
        'type': op_type,
        'message': message,
        'duration': duration
    }

def main(input_file, output_file):
    transactions = defaultdict(lambda: {
        'start_time': None,
        'total_duration': 0.0,
        'operations': [],
        'pid': None,
        'user': None,
        'ip': None
    })

    current_operation = None

    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} MSK', line):
                parsed = parse_log_line(line)
                if not parsed:
                    continue

                current_operation = parsed
                tx_key = parsed['vxid'] if parsed['vxid'] else 'no_transaction'
                tx = transactions[tx_key]

                if tx['start_time'] is None or parsed['timestamp'] < tx['start_time']:
                    tx['start_time'] = parsed['timestamp']

                if tx['pid'] is None:
                    tx['pid'] = parsed['pid']

                if tx['user'] is None:
                    tx['user'] = parsed['user']

                if tx['ip'] is None:
                    tx['ip'] = parsed['ip']

                tx['total_duration'] += parsed['duration']
                tx['operations'].append(parsed)
            else:
                if current_operation:
                    current_operation['message'] += ' ' + line
                    duration_match = re.search(r'duration: (\d+\.\d+) ms', line)
                    if duration_match:
                        additional_duration = float(duration_match.group(1))
                        current_operation['duration'] = additional_duration
                        tx_key = current_operation['vxid'] if current_operation['vxid'] else 'no_transaction'
                        transactions[tx_key]['total_duration'] += additional_duration

    # Множество для сбора уникальных пользователей
    users_set = set()

    # ... (парсинг файла остаётся без изменений)

    # Собираем пользователей из всех транзакций
    for tx in transactions.values():
        if tx['user']:
            users_set.add(tx['user'])

    # Сортируем пользователей для удобства
    sorted_users = sorted(users_set)

    # Генерируем HTML с фильтром
    html_content = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Transaction Log Analysis</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .filter-section { margin-bottom: 20px; padding: 15px; background: #f0f0f0; border-radius: 5px; }
            .transaction { border: 1px solid #e0e0e0; padding: 15px; margin: 10px 0; border-radius: 8px; background: #f9f9f9; }
            .transaction h3 { margin-top: 0; color: #2c3e50; }
            .no-transaction { border-color: #e74c3c; background: #ffe6e6; }
            .operation { margin: 10px 0; padding-left: 20px; }
            .operation-type { color: #3498db; font-weight: bold; }
            .hidden { display: none; }
        </style>
    </head>
    <body>
    <h1>Transaction Log Analysis</h1>
    
    <div class="filter-section">
        <form id="userFilterForm">
            <label for="userSelect">Filter by user:</label>
            <select id="userSelect" multiple size="5">
                <!-- Опции будут добавлены динамически -->
    '''

    # Добавляем опции для всех пользователей
    for user in sorted_users:
        escaped_user = html.escape(user)
        html_content += f'<option value="{escaped_user}">{escaped_user}</option>\n'

    html_content += '''
            </select>
            <button type="button" onclick="applyUserFilter()">Apply</button>
        </form>
    </div>
    '''

    # Генерируем транзакции с data-атрибутами
    for tx_key, tx in transactions.items():
        if not tx['operations']:
            continue

        css_class = 'transaction'
        if tx_key == 'no_transaction':
            css_class += ' no-transaction'

        # Экранируем данные для безопасной вставки в HTML
        header = f"Transaction ID: {html.escape(tx_key)}" if tx_key != 'no_transaction' else "No Transaction"
        header += f"<br>Start Time: {html.escape(tx['start_time'])} | Total Duration: {tx['total_duration']:.3f} ms"
        header += f" | User: {html.escape(tx['user'])} | Pid: {html.escape(tx['pid'])}"

        html_content += f'<div class="{css_class}" data-user="{html.escape(tx["user"])}">\n'
        html_content += f'    <h3>{header}</h3>\n'

        for op in tx['operations']:
            escaped_type = html.escape(op["type"])
            escaped_message = html.escape(op["message"])
            html_content += f'    <div class="operation">\n'
            html_content += f'        <span class="operation-type">[{escaped_type}]</span> {escaped_message}\n'
            html_content += '    </div>\n'

        html_content += '</div>\n'

    # Добавляем JavaScript для фильтрации
    html_content += '''
    <script>
        function applyUserFilter() {
            const select = document.getElementById('userSelect');
            const selectedUsers = Array.from(select.selectedOptions).map(opt => opt.value);
            const transactions = document.querySelectorAll('.transaction');
            
            // Если не выбрано ни одного пользователя - показываем все
            const showAll = selectedUsers.length === 0;
            
            transactions.forEach(transaction => {
                const user = transaction.dataset.user;
                const shouldShow = showAll || selectedUsers.includes(user);
                transaction.classList.toggle('hidden', !shouldShow);
            });
        }
    </script>
    </body>
    </html>
    '''

    with open(output_file, 'w') as f:
        f.write(html_content)

if __name__ == '__main__':
    main('postgresql.log', 'transactions.html')
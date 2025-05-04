import sqlite3

###############
def get_halfhour_info(name):
    connect = sqlite3.connect('database.db')
    command = connect.cursor()
    print(name)
    str_comm = f"""
    SELECT c.date, c.time, c.energy FROM consumption c 
    JOIN equipment AS e
    ON e.id = c.equipment_id
    WHERE e.name = '{name}' 
    AND c.id = (
        SELECT MAX(c.id) FROM consumption c
        JOIN equipment AS e
        ON e.id = c.equipment_id 
        WHERE e.name = '{name}'
    )
    """
    rows = command.execute(str_comm).fetchall()
    connect.close()
    total_consumption = 0
    print(rows)
    for row in rows:
        total_consumption += row[2]
    if total_consumption >=2:
        status = "В рабочем состоянии"
    elif total_consumption > 0:
        status = "В фоновом режиме"
    else:
        status = "Отключён"
    return str(name) + " | " + str(total_consumption) + " | " + status + "\n"


def get_info(name, date):
    connect = sqlite3.connect('database.db')
    command = connect.cursor()
    str_comm = f"""select c.date, c.time, c.energy from consumption c
    join equipment as e
    on e.id = c.equipment_id
    where e.name == '{name}' and c.date == '{date}'
    """
    rows = command.execute(str_comm).fetchall()
    connect.close()
    total_consumption = 0
    for row in rows:
        total_consumption += row[2]
    state = "Нет данных"
    if len(rows) != 0:
        state = "Выключен"
        if rows[len(rows) - 1][2] > 0:
            if rows[len(rows) - 1][2] <= 2:
                state = "Работает в фоновом режиме"
            else:
                state = "Работает"
    return str(date) + " | " + str(name) + " | " + str(round(total_consumption, 2)) + " | " + state + "\n"

dates_command = """
SELECT DISTINCT c.date FROM consumption c
"""

names_command = """
SELECT DISTINCT e.name FROM equipment e
"""

connect = sqlite3.connect("database.db")
command = connect.cursor()

def process_all():
    names = command.execute(names_command).fetchall()
    dates = command.execute(dates_command).fetchall()
    data = ""
    for name in names:
        for date in dates:
            data += get_info(name[0], date[0])
        data += "-----------------------------------------------------------\n"
    return data

def write_info_in(info_str):
    f = open('otchet.txt', 'w')
    f.write(info_str)
    f.close()

###############
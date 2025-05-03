import sqlite3

###############
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
    return str(date) + " | " + str(name) + " | " + str(total_consumption) + " | " + "Unknown" + "\n"

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
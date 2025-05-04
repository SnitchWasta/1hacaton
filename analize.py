from contextlib import nullcontext
from datetime import date, time, timedelta, datetime
import sqlite3

#
# str_comm = f"""INSERT INTO consumption (equipment_id, date, time, energy)
#     VALUES (1, '04.05.2025', '04:00:00', 25.64)"""
# connect = sqlite3.connect('database.db')
# command = connect.cursor()
#
# command.execute(str_comm)
# connect.commit()
# connect.close()

# str_comm = f"""UPDATE consumption
#     SET energy = 0
#     WHERE id = 11562
# """
# connect = sqlite3.connect('database.db')
# command = connect.cursor()
#
# command.execute(str_comm)
# connect.commit()
# connect.close()


def get_range_info(name, hours):
    connect = sqlite3.connect('database.db')
    command = connect.cursor()
    str_comm = f"""SELECT c.date, c.time, c.energy, e.name
        FROM consumption c
        JOIN equipment AS e
        ON e.id = c.equipment_id
        WHERE e.name == '{name}' AND datetime(
        substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2) || ' ' || time) 
        >= datetime('now', 'localtime', '-{hours} hours');
    """
    rows = command.execute(str_comm).fetchall()
    connect.close()
    return rows


def get_current_info(name):
    connect = sqlite3.connect('database.db')
    command = connect.cursor()
    str_comm = f"""SELECT c.date, c.time, c.energy, e.name
        FROM consumption c
        JOIN equipment AS e
        ON e.id = c.equipment_id
        WHERE e.name == '{name}' AND datetime(
        substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2) || ' ' || time) 
        >= datetime('now', 'localtime', '-30 minutes');
    """
    rows = command.execute(str_comm).fetchall()
    connect.close()
    if len(rows) == 0:
        return 0
    return rows[0]


def get_stat_for_last_range(name, hours: int):
    rows = get_range_info(name, hours)
    SUM = 0
    for r in rows:
        SUM += r[2]
    M = SUM/len(rows)
    return rows, SUM, M


def complete_cycle(name):
    connect = sqlite3.connect('database.db')
    command = connect.cursor()
    str_comm = f"""UPDATE charging_cycle_beginnings
            SET completed = 1
            WHERE id = (SELECT MAX(c.id) FROM charging_cycle_beginnings c
                JOIN equipment AS e
                ON e.id = c.equipment_id 
                WHERE e.name = '{name}');
        """
    command.execute(str_comm)
    connect.commit()
    connect.close()


def check_end_of_cycle(name):
    info = get_current_info(name)
    if info == 0:
        return True
    if info[2] == 0:
        complete_cycle(name)
        return True
    return False


def start_cycle(name, date, time):
    connect = sqlite3.connect('database.db')
    command = connect.cursor()
    str_comm = f"""INSERT INTO charging_cycle_beginnings (equipment_id, date, time)
             VALUES ((SELECT id FROM equipment
                WHERE name = '{name}'), '{date}', '{time}');
            """
    command.execute(str_comm)
    connect.commit()
    connect.close()


def check_start_of_cycle(name):
    info = get_range_info(name, 1)
    if info == 0:
        return True
    if info[0][2] == 0 and info[1][2] > 0:
        start_cycle(name, info[1][0], info[1][1])
        return True
    return False


def get_last_cycle_info(name):
    connect = sqlite3.connect('database.db')
    command = connect.cursor()
    str_comm = f"""SELECT c.date, c.time, c.energy, e.name
            FROM consumption c
            JOIN equipment e ON e.id = c.equipment_id
            JOIN (
                SELECT equipment_id, date, time
                FROM charging_cycle_beginnings
                WHERE equipment_id = (
                    SELECT id FROM equipment WHERE name = '{name}'
                )
                ORDER BY date(substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2)) DESC,
                         time DESC
                LIMIT 1
            ) last_cycle ON last_cycle.equipment_id = c.equipment_id
            WHERE datetime(
                substr(c.date, 7, 4) || '-' || substr(c.date, 4, 2) || '-' || substr(c.date, 1, 2) || ' ' || c.time
            ) >= datetime(
                substr(last_cycle.date, 7, 4) || '-' || substr(last_cycle.date, 4, 2) || '-' || substr(last_cycle.date, 1, 2) || ' ' || last_cycle.time
            )
            """
    rows = command.execute(str_comm).fetchall()
    connect.close()
    return rows


def get_last_cycle_stat(name):
    rows = get_last_cycle_info(name)
    SUM = 0
    for r in rows:
        SUM += r[2]
    M = SUM/len(rows)
    return rows, round(SUM, 2), round(M,2)


name = "038 QF 1,26 Р—РЈ PzS 12V 1   (kWh)"
# print(check_end_of_cycle(name))
#
# rows = get_last_cycle_info(name)
# for row in rows:
#     print(row)
#
# print(get_stat_for_last_range(name, 4))
# print()
# print(get_last_cycle_stat(name))
# print()
# print(get_current_info(name))

print(check_start_of_cycle(name))
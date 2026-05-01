import serial
import time 
import datetime
from PIL import ImageFont
from time import sleep
import psycopg2

conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="098102324",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

def mark_attendance(student_id):
    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    current_date = datetime.datetime.now().strftime('%d/%m/%Y')

    # 1. Проверяем, есть ли уже запись за сегодня
    cur.execute("SELECT time_in, time_out FROM attendance WHERE student_id = %s AND date = %s", (student_id, current_date))
    result = cur.fetchone()

    if result is None:
        # Вообще нет строки — создаем новую с временем прихода
        query = "INSERT INTO attendance (student_id, date, time_in, status) VALUES (%s, %s, %s, 'present')"
        cur.execute(query, (student_id, current_date, current_time))
        print(f"Студент {student_id}: НОВАЯ ЗАПИСЬ (Приход в {current_time})")
    
    elif result[0] is None:
        # Строка есть (от старого кода), но время прихода ПУСТОЕ — заполняем приход
        query = "UPDATE attendance SET time_in = %s WHERE student_id = %s AND date = %s"
        cur.execute(query, (current_time, student_id, current_date))
        print(f"Студент {student_id}: ЗАПОЛНЕН ПРИХОД ({current_time})")
        
    elif result[1] is None:
        # Приход уже был, а ухода нет — заполняем уход
        query = "UPDATE attendance SET time_out = %s WHERE student_id = %s AND date = %s"
        cur.execute(query, (current_time, student_id, current_date))
        print(f"Студент {student_id}: ЗАПОЛНЕН УХОД ({current_time})")
    
    else:
        # И приход, и уход уже стоят
        print(f"Студент {student_id}: У этого студента уже заполнены и вход, и выход.")
    conn.commit()


mark_attendance(13)  # Пример вызова функции для студента с ID 1    
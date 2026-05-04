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
global id
ser = serial.Serial('COM3', 9600)  
time.sleep(2)
ser.reset_input_buffer()
# serial = i2c(port=1, address=0x3C)
# device = ssd1306(serial, width=128, height=64)
# font_small = ImageFont.truetype("DejaVuSans.ttf", 12)

def mark_attendance(student_id):
    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    current_date = datetime.datetime.now().strftime('%d/%m/%Y')

    # 1. Проверяем, есть ли уже запись за сегодня
    cur.execute("SELECT time_in, time_out FROM attendance WHERE student_id = %s AND date = %s", (student_id, current_date))
    result = cur.fetchone()
    if result is None:
        # Вообще нет строки — создаем новую с временем прихода
        if current_time < "11:02:00":
            query = "INSERT INTO attendance (student_id, date, time_in, status) VALUES (%s, %s, %s, 'present')"
            cur.execute(query, (student_id, current_date, current_time))
            print(f"Студент {student_id}: НОВАЯ ЗАПИСЬ (Приход в {current_time})")
        if current_time > "11:05:00":
            query = "INSERT INTO attendance (student_id, date, time_in, status) VALUES (%s, %s, %s, 'late')"
            cur.execute(query, (student_id, current_date, current_time))
            # print(f"Студент {student_id}: НОВАЯ ЗАПИСЬ (Приход в {current_time})")
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

def create_table(student_id):
    data = datetime.datetime.now().strftime('%d/%m/%Y')
    print(data)    
    status = "present"
    print(student_id)
    query = """
    INSERT INTO attendance (student_id, date, status)
    VALUES (%s, %s, %s)
    ON CONFLICT (student_id, date)
    DO UPDATE SET status = EXCLUDED.status
    RETURNING *;
    """

    cur.execute(query, (student_id, data, status))

    result = cur.fetchone()
    conn.commit()

def detect(fid):
    print(f"Обнаружен студент с ID: {fid}")
    mark_attendance(fid)

def students():
    """Проверяет базу на наличие новых студентов и отправляет их в Arduino"""
    # print("Проверка новых студентов...")
    try:
        with open("last_id.txt", "r") as f:
            last_id = int(f.read().strip())
    except:
        last_id = 0

    cur.execute("SELECT id FROM students WHERE id > %s ORDER BY id ASC", (last_id,))
    new_students = cur.fetchall()

    for row in new_students:
        s_id = row[0]
        print(f"Регистрация нового студента ID: {s_id}")
        
        # Попытка отправить ID в Arduino (ждем подтверждения)
        attempts = 0
        while attempts < 5:
            ser.write(f"x{s_id}".encode("utf-8"))
            response = ser.readline().decode("utf-8").strip()
            print(response)
            if response == str(s_id):
                print(f"Arduino подтвердил получение ID {s_id}")
                break
            attempts += 1
            time.sleep(1)

        last_id = s_id
        with open("last_id.txt", "w") as f:
            f.write(str(last_id))

while True:
    students()
    ser.write(b'a')
    if ser.in_waiting > 0:
            line = ser.readline().decode("utf-8").strip()
            print(line)
            if line and line.isdigit():
                print(f"Считан ID со сканера: {line}")
                detect(line)

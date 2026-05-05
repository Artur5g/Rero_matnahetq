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
ser = serial.Serial('COM7', 9600)  
time.sleep(2)
ser.reset_input_buffer()
# serial = i2c(port=1, address=0x3C)
# device = ssd1306(serial, width=128, height=64)
# font_small = ImageFont.truetype("DejaVuSans.ttf", 12)
print("start")
def mark_attendance(student_id):
    current_time_obj = datetime.datetime.now().time()
    current_time_str = current_time_obj.strftime('%H:%M:%S')
    current_date = datetime.datetime.now().strftime('%d/%m/%Y')

    # Получаем настройки группы для времени
    cur.execute("""
        SELECT g.start_time, g.late_threshold 
        FROM students s
        JOIN student_groups g ON s.group_id = g.group_id
        WHERE s.id = %s
    """, (student_id,))
    group_settings = cur.fetchone()
    
    if not group_settings: return
    start_time, late_threshold = group_settings

    # Проверяем текущий статус (был ли уже приход)
    cur.execute("SELECT status, time_in, time_out FROM attendance WHERE student_id = %s AND date = %s", (student_id, current_date))
    result = cur.fetchone()

    # Если статус 'absent' — значит это первое сканирование (ПРИХОД)
    if result and result[0] == 'absent':
        if current_time_obj <= start_time:
            new_status = 'present'
        else:
            new_status = 'late'

        query = "UPDATE attendance SET time_in = %s, status = %s WHERE student_id = %s AND date = %s"
        cur.execute(query, (current_time_str, new_status, student_id, current_date))
        print(f"Студент {student_id}: статус изменен на {new_status}")
        
        # Здесь можно вызвать функцию отправки SMS родителям
        # send_sms_via_arduino(...) 

    # Если вход уже был, а выхода нет — фиксируем ВЫХОД
    elif result and result[2] is None:
        query = "UPDATE attendance SET time_out = %s WHERE student_id = %s AND date = %s"
        cur.execute(query, (current_time_str, student_id, current_date))
        print(f"Студент {student_id}: зафиксирован выход")

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

def initialize_attendance():
    current_date = datetime.datetime.now().strftime('%d/%m/%Y')
    print(f"Инициализация посещаемости на {current_date}...")

    try:
        # Получаем список всех активных студентов
        cur.execute("SELECT id FROM students")
        all_students = cur.fetchall()

        for row in all_students:
            student_id = row[0]
            
            # Пытаемся вставить запись со статусом 'absent'
            # Если запись уже есть (например, скрипт перезапустили), ON CONFLICT ничего не делает
            query = """
            INSERT INTO attendance (student_id, date, status)
            VALUES (%s, %s, 'absent')
            ON CONFLICT (student_id, date) DO NOTHING;
            """
            cur.execute(query, (student_id, current_date))
        
        conn.commit()
        print("Все студенты отмечены как 'absent'. Ожидание сканирования...")
    except Exception as e:
        print(f"Ошибка инициализации: {e}")
        conn.rollback()

# --- ВЫЗОВ ПЕРЕД ЦИКЛОМ ---
initialize_attendance()

while True:
    students()
    ser.write(b'a')
    if ser.in_waiting > 0:
            line = ser.readline().decode("utf-8").strip()
            print(line)
            if line and line.isdigit():
                print(f"Считан ID со сканера: {line}")
                detect(line)

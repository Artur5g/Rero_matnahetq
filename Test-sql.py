
import psycopg2
import time
import serial
ser = serial.Serial('COM9', 9600) 
time.sleep(2)
ser.reset_input_buffer()
global id
# Параметры подключения
config = {
    "host": "localhost",
    "database": "postgres",
    "user": "postgres",
    "password": "098102324",
    "port": "5432"
}


conn = psycopg2.connect(**config)
cur = conn.cursor()

def students():
    # пробуем загрузить последний ID из файла
    try:
        with open("last_id.txt", "r") as f:
            last_id = int(f.read())
    except:
        last_id = 0

    print("Старт. Последний ID:", last_id)

    while True:
        cur.execute("""
            SELECT id, full_name, phone, email 
            FROM students
            WHERE id > %s
            ORDER BY id ASC
        """, (last_id,))

        rows = cur.fetchall()

        for row in rows:
            student_id, name, phone, email = row

            # print(f"\nНовый студент:")
            print(f"ID: {student_id}")
            id = student_id
            # print(f"Имя: {name}")
            # print(f"Телефон: {phone}")
            # print(f"Email: {email}")
            # payload = f"b{student_id}".encode("utf-8")
            while True:
                print(f"x{student_id}".encode("utf-8"))
                ser.write(f"x{student_id}".encode("utf-8"))
                dver1 = ser.readline()
                decoded_bytes1 = (dver1[0:len(dver1)-2].decode("utf-8"))
                print(decoded_bytes1)
                if decoded_bytes1 == f"{student_id}":
                    break


            # обновляем последний ID
            last_id = student_id
            print(id)
            # сохраняем в файл
            with open("last_id.txt", "w") as f:
                f.write(str(last_id))


        time.sleep(5)


students()

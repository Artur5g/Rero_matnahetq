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

ser = serial.Serial('COM7', 9600)  
time.sleep(2)
ser.reset_input_buffer()      
# serial = i2c(port=1, address=0x3C)
# device = ssd1306(serial, width=128, height=64)
# CREDENTIALS_FILE = 'rero-462308-93702059b7a2.json'
# font_small = ImageFont.truetype("DejaVuSans.ttf", 12)


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
# start()
def detect(fid):
            print(fid)
            a1 = 0
            if a1 == 0:
                named_tuple = time.localtime() # получаем struct_time
                time_string = time.strftime("%m/%d/%Y, %H:%M:%S", named_tuple)
                time_minut = time.strftime("%M", named_tuple)
                with open("file.txt", "w") as file:
                    file.write(time_string)
                print(time_string)
                a1 = 1
                print(1)
                time.sleep(2)
                #  workspace("2")
                create_table(fid)
            if a1 == 1:
                print("if")
                named_tuple2 = time.localtime() # получаем struct_time
                time_string2 = time.strftime("%M", named_tuple2)
                print(time_minut)
                print(time_string2)                
                if (time_string2 > time_minut):
                    with open("file.txt", "w") as file:
                        file.write(time_string2)
                        print(time_string2)
                        print("time_string2")
                    print(2)


while True:
    dver1 = ser.readline()
    decoded_bytes1 = (dver1[0:len(dver1)-2].decode("utf-8"))
    detect(decoded_bytes1)


# %% Import Section
import cv2  # Module to use Camera
from pyzbar import pyzbar  # Module to read qrcodes and QR codes from Python
import time  # Module to access Time
import sqlite3  # Database Module to connect with Sqlite Database
import os # Module to determine OS to play beep sound
from datetime import datetime # Module for date conversion

# %% Main Code Section
my_os = os.name # Identify OS
id = input('\nPlease enter your user ID --> ')

# %% Connection to SQLite Database
EAN = sqlite3.connect('database/ean_database.db') 
ean_database = EAN.cursor()
BASKET = sqlite3.connect('database/basket_database.db')
basket_database = BASKET.cursor()

# %% Using Camera to read QR Codes
camera = cv2.VideoCapture(0)  # Start capturing Video feed
basket = []  # The basket is empty at the beginning
print('=' * 40 + '\nProducts:')

# Loop for every Transaction ( 1 Loop -> 1 Transaction)
while True:  # Loop to scan qrcode ( 1 Loop -> 1 Frame from Camera)
    key = cv2.waitKey(1) # Start reading 'ESC' key press
    _, frame = camera.read()  # captures the frame
    cv2.imshow("QR Code Scanner", frame)  # Showing frame 
    qrcodes = pyzbar.decode(frame)  # scanning for qrcode
    if key == 27:  # ESC key to end a transaction
        break
    elif not qrcodes:  # repeat if no QR Code on the frame is found
        continue

    # We consider only one QR code per frame
    first_qrcode = qrcodes[0]
    qr_code = first_qrcode.data.decode("utf-8")  # decoded QR code
    if len(qr_code) != 34:  # checking for correct QR code format
        continue
    # Extraction of data from QR code
    EAN_Number = qr_code[2:16]
    Weight = int(qr_code[21:26])
    Expiry_Date = str(datetime.strptime(qr_code[28:], '%y%m%d'))
    
    # Beep if correct QR code is found
    if my_os == 'posix':
        # play audio in macos
        os.system('afplay resources/beep.aiff')
    elif my_os == 'nt':
        # play audio in windows os
        import winsound
        winsound.Beep(2500,500)

    # Fetch all the data of product from database
    ean_database.execute(
        "SELECT Name, Price FROM Product_Info WHERE EAN=:b", {'b': EAN_Number})
    data_read = ean_database.fetchall()

    if data_read:
        # adds those data into the basket
        Name = list(data_read[0])[0]
        Price = list(data_read[0])[1]
        scanned_product = (EAN_Number,Name,Weight,Expiry_Date,Price)
        basket.append(scanned_product)
        print('  ', str(Weight)+'g', Name)
        time.sleep(1.5)

# %% Saving basket into the database
id_compatible = "_" + str(id)
basket_database.execute("""CREATE TABLE if not exists {} (
            EAN integer,
            Name text,
            Weight integer,
            Expiry_Date integer,
            Price real
            )""".format(id_compatible))
basket_database.executemany(
    f"insert into '{id_compatible}' values(?,?,?,?,?)", basket)
print('=' * 40 + '\n')

camera.release()  # releases the Camera for another program
cv2.destroyAllWindows()  # closes all the Window
# Closing Database
EAN.close() 
BASKET.commit()
BASKET.close()
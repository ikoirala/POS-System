# %% Import Section
import RPi.GPIO as GPIO  # Module to control Raspberry Pi GPIO channels
import cv2  # Module to use Camera
from pyzbar import pyzbar  # Module to read qrcodes and QR codes from Python
import time  # Module to access Time
import sqlite3  # Database Module to connect with Sqlite Database
from mfrc522 import SimpleMFRC522  # Module for NFC Chip
from datetime import datetime

# %% GPIO Pin Connection Setting for Buzzer
buzzerPin = 11  # Buzzer is set to Pin 11
GPIO.setmode(GPIO.BOARD)
GPIO.setup(buzzerPin, GPIO.OUT)
GPIO.output(buzzerPin, GPIO.HIGH)

# %% Database Connection
EAN = sqlite3.connect('database/ean_database.db') 
ean_database = EAN.cursor()
BASKET = sqlite3.connect('database/basket_database.db')
basket_database = BASKET.cursor()

# %% Functions
def read_RFID():
    # Function to read id from RFID Chip
    reader = SimpleMFRC522()
    print("Hold your RFID Chip on the reader... ")
    id, text = reader.read()
    print(id,text)
    return id

def save_to_basket(id, basket):
    # This function saves the items in 'basket' in a table with name 'id'
    # Adding '_' because number is not supported at the beginning of table name
    id_compatible = "_" + str(id)
    # Creates a table if not exists
    basket_database.execute("""CREATE TABLE if not exists {} (
                EAN integer,
                Name text,
                Weight integer,
                Expiry_Date integer,
                Price real
                )""".format(id_compatible))
    basket_database.executemany(
        f"insert into '{id_compatible}' values(?,?,?,?,?)", basket)

# %% Main Code Section
# Start capturing Video
active = 'y'
camera = cv2.VideoCapture(0)  # Start capturing Video feed

# Loop for every Transaction ( 1 Loop -> 1 Transaction)
while active == 'Y' or active == 'y':
    basket = []  # The basket is empty at the beginning
    while True:  # Loop to scan qrcode ( 1 Loop -> 1 Frame from Camera)
        key = cv2.waitKey(1)
        _, frame = camera.read()  # captures the frame
        # updates frame in Camera Feed Window
        cv2.imshow("QR Code Scanner", frame)
        # scans every frame for qrcode/QR Code
        qrcodes = pyzbar.decode(frame)
        if key == 27:  # ESC key to end a transaction
            break
        elif not qrcodes:  # if no qrcode/QR Code on the frame
            continue

        # We consider only one bar/QR code per frame
        first_qrcode = qrcodes[0]
        qr_code = first_qrcode.data.decode("utf-8")  # decoded bar/QR code

        if len(qr_code) != 34:  # checking for correct QR code format
            continue

        # Audio Signal
        GPIO.output(buzzerPin, GPIO.HIGH)  # Buzzer on
        time.sleep(0.2)  # Duration of Buzzer
        GPIO.output(buzzerPin, GPIO.LOW)  # Buzzer off

        # Extraction of data from QR code
        EAN_Number = qr_code[2:16]
        Weight = int(qr_code[21:26])
        Expiry_Date = str(datetime.strptime(qr_code[28:], '%y%m%d'))

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

        # Closing Camera in Loop because of a Bug in our Camera
        camera.release()
        cv2.destroyAllWindows()
        time.sleep(1)
        camera = cv2.VideoCapture(0)  # Start capturing Video feed

    # upload basket into Basket Database
    id = read_RFID()  # read id from RFID reader
    # saves all the data in basket to basket database
    save_to_basket(id, basket)

    active = input('\nStart new Transaction: \nProceed (y/n)? ')

GPIO.cleanup()  # This sets all the GPIO ports to input in order to prevent short circuit
camera.release()  # releases the Camera for another programme
cv2.destroyAllWindows()  # closes all the Window
EAN.close()  # Close EAN database connection
BASKET.commit()  # Saves the changes in BASKET Database
BASKET.close()  # Close the BASKET database connection
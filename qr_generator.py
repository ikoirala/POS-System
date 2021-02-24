# %% import section
import sqlite3
import qrcode
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# %% Functions
def get_Products(input):
    if input == 'all':
        # Fetch all the product information database
        database_connection.execute(
            "SELECT * FROM Product_Info")
    else:
        # Fetch information of a specific product
        database_connection.execute(
            "SELECT * FROM Product_Info WHERE Name=:b", {'b': input})
    return database_connection.fetchall()


# %% Main code section
# Database Connection
EAN_Database = sqlite3.connect('database/ean_database.db')
database_connection = EAN_Database.cursor()

# Input from the User
name_product = input(
    "Please enter the name of the product ('list' for List & 'all' for all Products): ")

# List all the products if the user wants so
if name_product == 'list':
    sep = '=' * 50
    print(f'\nList of products:\n{sep}')
    for items in get_Products('all'):
        print(' ', items[1])
    print(f'{sep}\n')
    name_product = input(
        "Please enter the name of the product ('all' for all Products): ")

ask_date = input(
    'Do you want to enter a different expiry date other than that in the database [y/n]? --> ')

# %% QR Code creation for all products one by one
for items in get_Products(name_product):
    
    EAN_Number = items[0]
    # Adjustment of the length of EAN_Number
    EAN_Number = str(EAN_Number)
    while len(EAN_Number) < 14:
        EAN_Number = ("0"+EAN_Number)
    name_product = items[1]
    weight = items[2]
    
    # Adjustment of the length of weight
    weight = str(weight)
    while len(weight) < 6:
        weight = ("0"+weight)
        
    # Confirmation of expiry date
    if ask_date == 'y' or ask_date == 'Y':
        EXP = input(
            f'Please enter the expiry date of {name_product} (Format: yymmdd): ')
    else:
        iso_EXP = datetime.fromisoformat(items[3])
        EXP = iso_EXP.strftime("%y%m%d")
        
    # EXP in german datetime format
    german_EXP = f'{EXP[4:6]}.{EXP[2:4]}.20{EXP[0:2]}'
    
    # String for QR Code
    qr_code_data = ("01"+EAN_Number+"3102"+weight+"17"+EXP)
    
    # Generation of QR Code image
    qr = qrcode.make(qr_code_data)
    
    # make a blank image for the text
    new_image = Image.new('RGBA', (290, 350), (255, 255, 255))
    new_image.paste(qr, (0, 0))  # Paste QR in the new image
    # get a font
    fnt = ImageFont.truetype("resources/font_for_qr.ttf", 18)
    d = ImageDraw.Draw(new_image)  # to write something in the image
    # Draw text in Image
    d.text((38, 265), f'Product: {name_product}',
           font=fnt, fill=(0, 0, 0, 256))
    d.text((38, 288), f'EAN: {EAN_Number}', font=fnt, fill=(0, 0, 0, 256))
    d.text((38, 311), f'Expiry Date: {german_EXP}',
           font=fnt, fill=(0, 0, 0, 256))
    # Save new image
    new_image.save('qr_codes/' + name_product + '_' + EXP + '.png')
    print(
        f'----> QR Code is generated for {name_product} with expiry date {EXP[4:6]}.{EXP[2:4]}.20{EXP[0:2]}')

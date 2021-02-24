# %% Import Section
import sqlite3
from datetime import datetime, timedelta
import art

# %% Database Connection
BASKET = sqlite3.connect('database/basket_database.db')
basket_database = BASKET.cursor()
RECIPE = sqlite3.connect('database/recipe_database.db')
recipe_database = RECIPE.cursor()

# %% Functions

def database_organise(customer):
    """This function sorts the entries in the database. The products with weight less than 1 g are deleted. 
    The weight of the products with the same EAN number and expiry date is added. 
    The input 'Customer' is the name of the table."""
    # Search of products that have no multiple entries in the database
    not_rep_str = f"SELECT * FROM {customer} GROUP BY EAN HAVING COUNT(*) <= 1"
    basket_database.execute(not_rep_str)
    organised_data = basket_database.fetchall()

    # Search of products that have multiple entries in the database
    rep_str = f"SELECT EAN FROM {customer} GROUP BY EAN HAVING COUNT(*) > 1"
    basket_database.execute(rep_str)
    multiple_entries = basket_database.fetchall()  # list of dublicate products

    # Merge of Products with same EAN Number
    for multiple_product in multiple_entries:
        ean = multiple_product[0]
        sp_rep_str = f"SELECT Expiry_Date FROM {customer} WHERE EAN = '{ean}' GROUP BY Expiry_Date"
        basket_database.execute(sp_rep_str)
        multiple_product_dates = basket_database.fetchall()

        # Merge of Products with same expiry date
        for multiple_product_date in multiple_product_dates:
            current_date = multiple_product_date[0]
            add_dub_str = f"""select EAN, Name, sum(Weight), Expiry_Date,
                sum(Price) FROM {customer} where EAN = '{ean}' AND Expiry_Date = '{current_date}';"""
            basket_database.execute(add_dub_str)
            date_organised_product = basket_database.fetchall()[0]
            organised_data.append(date_organised_product)

    # Delete original database table
    basket_database.execute(f'DELETE FROM {customer}')
    # Create new table with organised data
    basket_database.executemany(
        f"insert into {customer} values(?,?,?,?,?)", organised_data)
    # Delete all the products with weight less than 1g
    basket_database.execute(f'DELETE FROM {customer} WHERE Weight < 1')
    BASKET.commit()

def sorted_list(customer):
    # Extraction of products sorted by expiry date
    product_string = f"SELECT *  FROM {customer} ORDER BY Expiry_Date"
    basket_database.execute(product_string)
    products = basket_database.fetchall()
    return products


def show_as_table(products):
    # Print the product information in a table format
    print(separate2)  # First line
    print('| Index\t| Product\t\t| Weight [g]\t| Days Left\t|')  # Legend
    print(separate2)  # Second line

    # prints the product information
    for idx, product in enumerate(products, start=1):
        # Extraction of expiry date in datetime format
        expiry_date1 = datetime.fromisoformat(product[3])
        # Calculation of remaining times
        rem_days = str(expiry_date1 - datetime.now())
        product_name = product[1]
        # Name length adjustment
        while len(product_name) < 14:
            product_name = product_name + ' '
        # Output product information in commond window
        print('| ' + str(idx) + '\t| ' + product_name + '\t| ' +
              str(product[2]) + '\t\t| ' + rem_days.split(',')[0] + ' \t|')
    print(separate2)  # Last line


def recipe_print(customer, selected_recipe):
    # Print the items needed for the selected recipe with the amount insufficient in user's database
    # List of items needed for the selected recipe
    recipe_database.execute(f"SELECT * from '{selected_recipe}'")
    products_needed_for_recipe = recipe_database.fetchall()
    # Initialise the separator for better Visual
    print(separate2)
    print(f' You need the following products for {selected_recipe}:')
    for items in products_needed_for_recipe:
        print('\t', str(items[2]) + 'g\t', items[1])
    # Initialise some empty list to determine if the needed products are in user's database
    product_insufficient = []
    product_not_exist = []
    products_in_recipe = []
    for items in products_needed_for_recipe:
        # Fetch total weight of needed product from user's database
        basket_database.execute(
            f"SELECT sum(Weight) FROM {customer} where EAN = {items[0]}")
        total_weight = basket_database.fetchall()[0][0]
        if total_weight:  # if there is some amount in database
            weight_diff = total_weight - items[2]
            # Add the product in products_in_recipe, if it is in user's database
            products_in_recipe.append(
                tuple([items[2], weight_diff, items[1], items[0]]))
            if weight_diff < 0:  # In case the product is not sufficient
                product_insufficient.append(
                    tuple([items[2], weight_diff, items[1], items[0]]))
        else:
            product_not_exist.append(
                tuple([items[2], -items[2], items[1], items[0]]))
    if product_insufficient or product_not_exist:
        print(' However, it lacks:')
        # output eg: 150g von 200g Reis
        for items in product_insufficient:
            print(f'\t{-items[1]}g\tfrom ', str(items[0]) + 'g\t', items[2])
        for items in product_not_exist:
            print(f'\t{-items[1]}g\tfrom ', str(items[0]) + 'g\t', items[2])
    print(separate2)
    return products_in_recipe


def deduct_quantity(customer, products_in_recipe):
    # This functions reduces the amount of used products if a recipe is selected
    for product in products_in_recipe:
        # selected product with different expiry date is fetched
        basket_database.execute(f"""SELECT Expiry_Date, Weight FROM {customer} where EAN
                = {product[3]} ORDER BY Expiry_Date""")
        product_with_different_date = basket_database.fetchall()
        required_quantity = product[0]
        for entries in product_with_different_date:
            if required_quantity <= entries[1]:
                # if the product with this expiry date is enough for the recipe, reduce the amount
                basket_database.execute(f"""update {customer} set Weight = {int(entries[1]) - int(required_quantity)}
                    WHERE EAN = {product[3]} and Expiry_Date = '{entries[0]}'""")
                break
            else:  # if the product with this expiry date is not enough for the recipe,
                # delete all the entry and reduce the deleted amount from required quantity
                basket_database.execute(
                    f"DELETE FROM {customer} WHERE EAN = {product[3]} and Expiry_Date = '{entries[0]}'")
                required_quantity = required_quantity - entries[1]
    BASKET.commit()


# %% Main Code Section
# Separators for better Visual in Command line
separate1 = 65 * '='
separate2 = 65 * '-'

# Customer Reference
print('\n' + separate1)  # upper seperator
customer = '_' + str(input('Please enter your ID --> '))
database_organise(customer)  # Organise the Database
# Extraction of products to be consumed quickly
products = sorted_list(customer)

# Show the list of products in command window
print('\nHallo' + customer + ',', 'You have the following products.\n')
show_as_table(products)
print('\n')

# Checking Expired Products
basket_database.execute(
    f"select * from {customer} where Expiry_Date < '{datetime.now()}'")
expired = basket_database.fetchall()
if expired:
    print('-' * 65)
    art.tprint('Warning')
    delete_q = input(
        'Expired products are found in the database!\nDelete [y/n]? --> ')
    print('-' * 65, '\n')
    if delete_q == 'y' or delete_q == 'Y':
        basket_database.execute(
            f"DELETE FROM {customer} where Expiry_Date < '{datetime.now()}'")
        BASKET.commit()
        products = sorted_list(customer)
        print('You now have following products left:')
        show_as_table(products)
        print('\n')

# Checking for Products expiring soon
warning_till = datetime.now() + timedelta(days=5)
basket_database.execute(
    f"select * from {customer} where Expiry_Date < '{warning_till}'")
expiring_soon = basket_database.fetchall()
if expiring_soon:
    print('-' * 65)
    art.tprint('Warning')
    print('There are products that are about to expire!\n' + '-' * 65, '\n')


# Extraction of all recipies
recipe_database.execute('SELECT name from sqlite_master where type= "table"')
recipe_names = recipe_database.fetchall()

# Algorithm for recipe search
search_recipe_for_EAN = products[0][0]  # product with nearest expiry date

# Search for suitable recipes
matching_recipes = []
for recipe in recipe_names:
    recipe_name = recipe[0]
    extraction_string = f"SELECT * from '{recipe_name}' where EAN = {search_recipe_for_EAN}"
    recipe_database.execute(extraction_string)
    product_in_recipe = recipe_database.fetchall()
    if product_in_recipe:
        matching_recipes.append(recipe_name)

# Presentation & selection of suitable recipe
if matching_recipes:
    print('Matching recipes:')
    # Print a list of matching recipes
    for idx, recipe_match in enumerate(matching_recipes, start=1):
        print('--> ' + str(idx) + '.' + recipe_match)
    # Ask to select a recipe
    recipe_number = input(
        'Enter the index of the recipe you want to use [0 to skip]. --> ')
    # If a recipe is selected
    if not (recipe_number == '0' or (not recipe_number)):
        selected_recipe = matching_recipes[int(recipe_number) - 1]
        products_in_recipe = recipe_print(customer, selected_recipe)
        # Ask if the user is really going to use the recipe
        cook_recipe = input(
            f'Do you want to cook {selected_recipe} (The quantity will be deducted) [y/n]?')
        if cook_recipe == 'y' or cook_recipe == 'Y':
            # Reduce the used products from database
            deduct_quantity(customer, products_in_recipe)
            # Organise the database
            database_organise(customer)
            products = sorted_list(customer)
            # Show the remaining products in user's database
            print('You now have the following products left:')
            show_as_table(products)
else:  # If no matching recipe is found
    print('---- No matching recipes found in the database! ----')

# Manuel delete section
condition = input('Do you want to remove a product from the database [y/n]? --> ')
while condition == 'Y' or condition == 'y':
    d_product = int(
        input('Enter the index of product you have used. --> '))
    d_weight = input(
        f'Enter the weight of {products[d_product-1][1]} you have used [in g]. --> ')
    # reduces the d_weight amount of d_product from customer's database
    basket_database.execute(
        f"""UPDATE {customer} SET weight = weight - {int(d_weight)} WHERE EAN = 
            {products[d_product-1][0]} AND Expiry_Date = '{products[d_product-1][3]}'""")
    # Confirmation of the reduction
    print('\n' + d_weight + 'g ' +
          products[d_product-1][1] + ' is deducted from database.\n')
    BASKET.commit()
    # Organise the database
    database_organise(customer)
    products = sorted_list(customer)
    # Show the remaining products in user's database
    show_as_table(products)
    condition = input('Do you want to remove other products [y/n]? --> ')

print(separate1 + '\n')  # End of skript
import pandas as pd
from sqlalchemy import create_engine

# Update ean_database
file = 'ean_list.xlsx'
engine = create_engine('sqlite:///ean_database.db')
df = pd.read_excel(file, sheet_name='Product_Info')
df.to_sql('Product_Info', con=engine, if_exists='replace', index=False)

# Update recipe database
file = 'recipe_list.xlsx'
engine = create_engine('sqlite:///recipe_database.db')
sheets = pd.ExcelFile(file).sheet_names

# separate table for each recipes 
for recipe in sheets:
    if recipe == 'links': # ignore table with links
        continue
    df = pd.read_excel(file, sheet_name=recipe)
    df.to_sql(recipe, con=engine, if_exists='replace', index=False)

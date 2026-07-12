from database.session import engine

try:
    with engine.connect() as connection:
        print("Connected successfully!")
except Exception as e:
    print(e)
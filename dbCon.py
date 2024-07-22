#!/usr/bin/python  

import sqlite3  

conn = sqlite3.connect('database.db')  
print ("Opened database successfully")  


conn.execute("create table sales (id INTEGER PRIMARY KEY AUTOINCREMENT, InvoiceNo TEXT NOT NULL, StockCode TEXT NOT NULL, Quantity TEXT NOT NULL, InvoiceDate TEXT NOT NULL, UnitPrice TEXT NOT NULL, CustomerID TEXT NOT NULL,  Description TEXT NOT NULL, Country TEXT NOT NULL,Total TEXT NOT NULL,ActualPrice TEXT NOT NULL)")  


print ("Table created successfully")  
conn.close()  

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans


# Load Data

data = pd.read_csv('data.csv')

data_head = data.head()
data_description = data.describe()
missing_values_in_data = data.isnull().sum()
# print(missing_values_in_data)
# drop_rows_with_missing customerId
data.dropna(subset=['CustomerID'],inplace=True)
# Remove rows with negative Quantity and Price
data[(data['Quantity']>0) & (data['UnitPrice']>0)]

# convert CustomerId to an integer 
data['CustomerID'] = data['CustomerID'].astype(int)

# print (data.dtypes)

# Compute Recency, Frequency, and Monetary Value
# initial date 
snapshot_date = max(data['InvoiceDate']) #pd.DateOffset(days=1)

# create a “Total” column that contains Quantity*UnitPrice for all the records:
data['Total'] = data['Quantity'] * data['UnitPrice']

# Recency, Frequency, and MonetaryValue
rfm = data.groupby('CustomerID').agg({
    'InvoiceDate': lambda x: (snapshot_date - x.max()).days,
    'InvoiceNo':'nunique',
    'Total':'sum'
})

# Rename columns 
rfm.rename(columns={'InvoiceDate':'Recency','InvoiceNo':'Frequency','Total':'MonetaryValue'},inplace=True)
rfm.head()

print (rfm)
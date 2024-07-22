# Importing required functions  


from flask import Flask,redirect, url_for, render_template, request,Response 
import sqlite3  
# Flask constructor  

app = Flask(__name__) 

@app.route('/download-csv')
def download_csv():
    import csv
    import io
    try:
        # db = get_db()
        with sqlite3.connect("database.db") as db:
            cursor = db.cursor()
            cursor.execute('SELECT * FROM sales')  # Replace 'mytable' with your table name
            rows = cursor.fetchall()

            # Create a StringIO object to write the CSV data
            output = io.StringIO()
            writer = csv.writer(output)

            # Write the column headers
            writer.writerow([i[0] for i in cursor.description])

            # Write the data
            writer.writerows(rows)

            output.seek(0)
            
            # Create a response object and set the headers for file download
            return Response(
                output,
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment;filename=sales.csv'}
                )

    except Exception as e:
        return str(e)

def import_csv():
    import csv
    import io
    try:
        # db = get_db()
        with sqlite3.connect("database.db") as db:
            cursor = db.cursor()
            cursor.execute('SELECT * FROM sales')  # Replace 'mytable' with your table name
            rows = cursor.fetchall()

            # Create a StringIO object to write the CSV data
            output = io.StringIO()
            writer = csv.writer(output)

            # Write the column headers
            writer.writerow([i[0] for i in cursor.description])

            # Write the data
            writer.writerows(rows)

            output.seek(0)
            
            # Create a response object and set the headers for file download
            return output
    except Exception as e:
        return str(e)

def generate_plot ():
    import pandas as pd
    import matplotlib.pyplot as plt 
    from sklearn.cluster import KMeans
    import datetime as dt
    # Load Data
    """     STEP 1 - Load the Dataset       """
    # data = pd.read_csv('sales.csv')
    data = pd.read_csv(import_csv())

    """     STEP 2 - Explore and Clean the Dataset       """
    data_head = data.head()
    data_description = data.describe()
    missing_values_in_data = data.isnull().sum()
    # print(missing_values_in_data)
    # print (data_description)
    # drop_rows_with_missing customerId
    data.dropna(subset=['CustomerID'],inplace=True)
    # Remove rows with negative Quantity and Price
    data[(data['Quantity']>0) & (data['UnitPrice']>0)]

    # convert CustomerId to an integer 
    data['CustomerID'] = data['CustomerID'].astype(int)

    # print (data.dtypes)

    """     STEP 3 - Compute Recency, Frequency, and Monetary Value       """
    # initial date 
    data['InvoiceDate'] = pd.to_datetime(data['InvoiceDate'], errors='coerce')
    snapshot_date = max(data.InvoiceDate) + dt.timedelta(days=1)

    """     STEP 4 - Map RFM Values onto a 1-5 Scale        """

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

    # print (rfm)

    # Calculate custom bin edges for Recency, Frequency, and Monetary scores
    recency_bins = [rfm['Recency'].min()-1, 20, 50, 150, 250, rfm['Recency'].max()]
    frequency_bins = [rfm['Frequency'].min() - 1, 2, 3, 10, 100, rfm['Frequency'].max()]
    monetary_bins = [rfm['MonetaryValue'].min() - 3, 300, 600, 2000, 5000, rfm['MonetaryValue'].max()]

    # Sort bins in ascending order
    recency_bins.sort()
    frequency_bins.sort()
    monetary_bins.sort()
    # Calculate Recency score based on custom bins 
    rfm['R_Score'] = pd.cut(rfm['Recency'], bins=recency_bins, labels=range(1, 6), include_lowest=True)

    # Reverse the Recency scores so that higher values indicate more recent purchases
    rfm['R_Score'] = 5 - rfm['R_Score'].astype(int) + 1

    # Calculate Frequency and Monetary scores based on custom bins
    rfm['F_Score'] = pd.cut(rfm['Frequency'], bins=frequency_bins, labels=range(1, 6), include_lowest=True).astype(int)
    rfm['M_Score'] = pd.cut(rfm['MonetaryValue'], bins=monetary_bins, labels=range(1, 6), include_lowest=True).astype(int)

    # Print the first few rows of the RFM DataFrame to verify the scores
    print(rfm[['R_Score', 'F_Score', 'M_Score']].head(10))

    """     STEP 5 - Perform K-Means Clustering         """
    # Extract RFM scores for K-means clustering
    X = rfm[['R_Score', 'F_Score', 'M_Score']]

    # Calculate inertia (sum of squared distances) for different values of k
    inertia = []
    for k in range(2, 11):
        kmeans = KMeans(n_clusters=k, n_init= 10, random_state=42)
        kmeans.fit(X)
        inertia.append(kmeans.inertia_)

    # Plot the elbow curve
    # plt.figure(figsize=(8, 6),dpi=150)
    # plt.plot(range(2, 11), inertia, marker='o')
    # plt.xlabel('Number of Clusters (k)')
    # plt.ylabel('Inertia')
    # plt.title('Elbow Curve for K-means Clustering')
    # plt.grid(True)
    # plt.show()

    # Perform K-means clustering with best K
    best_kmeans = KMeans(n_clusters=4, n_init=10, random_state=42)
    rfm['Cluster'] = best_kmeans.fit_predict(X)

    """     STEP 6 - Interpret the Clusters to Identify Customer Segments       """

    # Group by cluster and calculate mean values
    cluster_summary = rfm.groupby('Cluster').agg({
        'R_Score': 'mean',
        'F_Score': 'mean',
        'M_Score': 'mean'
    }).reset_index()

    # print(cluster_summary)

    cluster_counts = rfm['Cluster'].value_counts()

    # Let’s visualize the distribution of the different clusters using a pie chart:
    colors = ['#3498db', '#2ecc71', '#f39c12','#C9B1BD']
    # Calculate the total number of customers
    total_customers = cluster_counts.sum()

    # Calculate the percentage of customers in each cluster
    percentage_customers = (cluster_counts / total_customers) * 100
    labels = ['Champions','Loyal','At-risk','Recent']

    # labels = ['At-risk Customers','Recent Customers']
    # labels = list(labelsNames)

    # print ("====================")
    # print (percentage_customers)
    # print(len(labels))

    # Create a pie chart
    plt.figure(figsize=(8, 8),dpi=200)
    plt.pie(percentage_customers, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
    plt.title('Percentage of Customers in Each Segment')
    plt.legend(cluster_summary['Cluster'], title='Segments', loc='upper left')
    # plt.show()
    return plt



# Root URL 
@app.get('/plot') 
def single_converter(): 
    import os
    # Get the matplotlib plot  
    plot = generate_plot()
    # Save the figure in the static directory  
    plot.savefig(os.path.join('static', 'images', 'plot.png')) 
    return render_template('plot.html') 


def generateInvoiceNo ():
    import random
    import math
    ## storing strings in a list
    digits = [i for i in range(0, 10)]

    ## initializing a string
    random_str = ""

    for i in range(6):
        index = math.floor(random.random() * 10)

        random_str += str(digits[index])
    # print(random_str)
    return random_str

def generateStockCode ():
    import random
    import math
    ## storing strings in a list
    digits = [i for i in range(0, 10)]

    ## initializing a string
    random_str = ""

    for i in range(4):
        index = math.floor(random.random() * 10)

        random_str += str(digits[index])
    # print(random_str)
    return random_str

def generateInvoiceDate ():
    from datetime import date
    today = date.today()
    # dd/mm/YY
    todayDate = today.strftime("%d/%m/%Y")
    return todayDate



# InvoiceNo StockCode Quantity InvoiceDate UnitPrice CustomerID  Description Country Total
@app.route("/saveSales",methods = ["POST","GET"])  
def saveDetails():  
    msg = "msg"  
    if request.method == "POST":  
        try:  
            InvoiceNo = generateInvoiceNo () #request.form['InvoiceNo'] 
            InvoiceDate = generateInvoiceDate()  
            StockCode = generateStockCode()  
            Country = "Uganda"  
            CustomerID = generateInvoiceNo () #request.form['CustomerId'] 
            Quantity = request.form["Quantity"]  
            Description = request.form["Description"]  
            Total = request.form["Total"]  

            ActualPrice = request.form["UnitPrice"] 
            first_two_digits = int(str(ActualPrice)[:2])

            UnitPrice = float(first_two_digits) 

            with sqlite3.connect("database.db") as con:  
                cur = con.cursor()  
                cur.execute("INSERT into sales (InvoiceNo, StockCode, Quantity, InvoiceDate, UnitPrice, CustomerID, Description, Country,Total,ActualPrice) values (?,?,?,?,?,?,?,?,?,?)",(InvoiceNo, StockCode, Quantity, InvoiceDate, UnitPrice, CustomerID, Description, Country,Total,ActualPrice))  
                con.commit()  
                msg = "Sale Successfully Recorded"  
        except:  
            con.rollback()  
            msg = "Sale Was Not Recorded"  
        finally:  
            return redirect(url_for('viewSales')) 
            # return render_template("index.html",msg = msg)  
            con.close()  


@app.route("/login", methods=["GET", "POST"])
def login():
    # If a post request was made, find the user by 
    # filtering for the username
    if request.method == "POST":
        username=request.form.get("username")
        password=request.form.get("password")
        if username == "Admin" and password == "Admin":
            return redirect(url_for("viewSales"))
    return render_template("login.html") 

@app.route("/logout", methods=["GET", "POST"])
def logout():
    return render_template("login.html") 

@app.route("/viewSales")  
def viewSales():  
    con = sqlite3.connect("database.db")  
    con.row_factory = sqlite3.Row  
    cur = con.cursor()  
    cur.execute("select * from sales")  
    rows = cur.fetchall()  
    return render_template("index.html",rows = rows)  

@app.route("/")  
def log_in_page():  
    return render_template("login.html")  




# Main Driver Function  
if __name__ == '__main__': 
    # Run the application on the local development server  
    # app.run(debug=True) 
    app.run(debug=True,host='0.0.0.0',port=5858)
    # generate_plot ()
    # import_csv()
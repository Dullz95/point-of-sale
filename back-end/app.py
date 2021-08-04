import hmac
import sqlite3

from flask import Flask, request
from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS

# create class for user log in details
class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

# create class(object) for prroducts
# class Product(object):
#     def __init__(self, product_id, product_name, product_type, price, quantity):
#         self.product_id = product_id
#         self.product_name = product_name
#         self.product_type = product_type
#         self.price = price
#         self.quantity = quantity

# create class (object) for Database functions
class Database(object):
    def __init__(self):
        self.conn = sqlite3.connect('sales.db')
        self.cursor = self.conn.cursor()

    def commiting(self, query, values):
        self.cursor.execute(query,values)
        self.conn.commit()

    # select
    def single_commiting(self, query):
        self.cursor.execute(query)

    def fetching(self):
        return self.cursor.fetchall()



# fetch username and password from the users table
def fetch_users():
    with sqlite3.connect('sales.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[3], data[4]))
    return new_data

# def fetch_products():
#     with sqlite3.connect('sales.db') as conn:
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM product")
#         products = cursor.fetchall()
#
#         new_data = []
#
#         for data in products:
#             new_data.append(Product(data[0], data[1], data[2], data[3], data[4]))
#     return new_data



# call function to fetch username and password
users = fetch_users()

# create user table
def init_user_table():
    conn = sqlite3.connect('sales.db')
    conn.execute("CREATE TABLE IF NOT EXISTS user(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("user table created successfully")
    conn.close()

# create cart table
def init_cart_table():
    with sqlite3.connect('sales.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS cart (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "item TEXT NOT NULL,"
                     "quantity TEXT NOT NULL,"
                     "itemPrice TEXT NOT NULL,"
                     "total TEXT NOT NULL)")
    print("cart table created successfully.")
    conn.close()

# create product table
def init_product_table():
    with sqlite3.connect('sales.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS product (product_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "product_name TEXT NOT NULL,"
                     "product_type TEXT NOT NULL,"
                     "price TEXT NOT NULL,"
                     "quantity TEXT NOT NULL)")
    print("items table created successfully")
    conn.close()

# calling function to create the three tables above
init_user_table()
init_cart_table()
init_product_table()

# fetch data to use for JWT token
username_table = { u.username: u for u in users }
userid_table = { u.id: u for u in users }

# authenticate login using username and password created when the account was registered to return the user profile
def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


app = Flask(__name__)
CORS(app)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'

jwt = JWT(app, authenticate, identity)

@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity

# create various end-points using SQL to fetch and post data to/from tables in DB

# creating registration end-point
@app.route('/user-registration/', methods=["POST"])
def user_registration():
    response = {}
    db = Database()

    if request.method == "POST":

        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password']

        query = "INSERT INTO user(first_name,last_name,username,password) VALUES(?, ?, ?, ?)"
        values = first_name, last_name, username, password

        db.commiting(query, values)

        response["message"] = "success"
        response["status_code"] = 201
        return response

# creating add product end-point
@app.route('/add-product/', methods=["POST"])
def add_product():
    response = {}
    db = Database()

    if request.method == "POST":
        item = request.form['item']
        quantity = request.form['quantity']
        itemPrice = request.form['itemPrice']
        total = int(quantity) * int(itemPrice)

        query = "INSERT INTO cart(item, quantity, itemPrice, total) VALUES(?, ?, ?, ?)"
        values = item, quantity, itemPrice, total

        db.commiting(query, values)

        response["status_code"] = 201
        response['description'] = "item added succesfully"
        return response

# create view items in users cart end-point
@app.route('/view-items/', methods=["GET"])
def view_items():
    response = {}
    db =Database()
    query = "SELECT * FROM cart"

    db.single_commiting(query)

    response['status_code'] = 200
    response['data'] = db.fetching()
    return response

# create end-point to delete products from users cart
@app.route("/delete-product/<int:id>")
def delete(id):
    response = {}
    db = Database()

    query = "DELETE FROM cart WHERE id=" + str(id)
    db.single_commiting(query)
    response['status_code'] = 200
    response['message'] = "item deleted successfully."
    return response

# create end-point to allow the user to view their profile
@app.route("/view-profile/<int:user_id>", methods=["GET"])
def view_profile(user_id):
    response = {}
    db= Database()

    query = "SELECT * FROM user WHERE user_id= " + str(user_id)
    db.single_commiting(query)
    response['status_code'] = 200
    response['data']= db.fetching()

    return response

# end-point to allow user to view all available products
@app.route("/view-all-products/", methods=["GET"])
def view_all():
    response = {}
    db = Database()

    query = "SELECT * FROM  product"
    db.single_commiting(query)

    response['status_code'] = 200
    response['data'] = db.fetching()

    return response

# end-point to allow the owner of the business to add products to the list of products available
@app.route("/add-to-product-table/", methods=["POST"])
def add():
    response = {}
    db = Database()

    if request.method == "POST":
        product_name = request.form['product_name']
        quantity = request.form['quantity']
        product_type = request.form['product_type']
        price = request.form['price']

        query = "INSERT INTO product(""product_name,product_type,price,quantity) VALUES(?, ?, ?, ?)"
        values = product_name, product_type, price, quantity
        db.commiting(query,values)
        response["status_code"] = 201
        response['description'] = "item added succesfully"

        return response

# create end-point to edit existing products/
@app.route("/updating-products/<int:product_id>",methods=["PUT"])
def edit(product_id):
    response = {}
    db = Database()

    if request.method == "PUT":
        product_name = request.form['product_name']
        product_type = request.form['product_type']
        price = request.form['price']
        quantity = request.form['quantity']

        query = "UPDATE product SET product_name=?, product_type=?, price=?, quantity=?" \
                    " WHERE product_id='" + str(product_id) + "'"
        values = product_name, product_type, price, quantity

        db.commiting(query,values)

        response['message'] = 200
        response['message'] = "Product successfully updated "
        return response

if __name__ == '__main__':
    app.debug = True
    app.run()
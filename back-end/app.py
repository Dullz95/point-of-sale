import hmac
import sqlite3

from flask import Flask, request
from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def fetch_users():
    with sqlite3.connect('sales.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[3], data[4]))
    return new_data


users = fetch_users()

def init_user_table():
    conn = sqlite3.connect('sales.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS user(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("user table created successfully")
    conn.close()


def init_post_table():
    with sqlite3.connect('sales.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS cart (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "item TEXT NOT NULL,"
                     "quantity TEXT NOT NULL,"
                     "itemPrice TEXT NOT NULL,"
                     "total TEXT NOT NULL)")
    print("cart table created successfully.")
    conn.close()


init_user_table()
init_post_table()

username_table = { u.username: u for u in users }
userid_table = { u.id: u for u in users }


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

@app.route('/user-registration/', methods=["POST"])
def user_registration():
    response = {}

    if request.method == "POST":

        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect("sales.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user("
                           "first_name,"
                           "last_name,"
                           "username,"
                           "password) VALUES(?, ?, ?, ?)", (first_name, last_name, username, password))
            conn.commit()
            response["message"] = "success"
            response["status_code"] = 201
        return response

@app.route('/add-product/', methods=["POST"])
def add_product():
    response = {}

    if request.method == "POST":
        item = request.form['item']
        quantity = request.form['quantity']
        itemPrice = request.form['itemPrice']
        total = request.form['total']

        with sqlite3.connect('sales.db') as conn:
            cursor = conn.cursor()

            cursor.execute("INSERT INTO cart("
                           "item,"
                           "quantity,"
                           "itemPrice,"
                           "total) VALUES(?, ?, ?, ?)", (item, quantity, itemPrice, total))
            conn.commit()
            response["status_code"] = 201
            response['description'] = "item added succesfully"
        return response


@app.route('/view-items/', methods=["GET"])
def view_items():
    response = {}
    with sqlite3.connect("sales.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cart")

        posts = cursor.fetchall()

    response['status_code'] = 200
    response['data'] = posts
    return response


@app.route("/delete-product/<int:id>")
def delete(id):
    response = {}
    with sqlite3.connect("sales.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cart WHERE id=" + str(id))
        conn.commit()
        response['status_code'] = 200
        response['message'] = "item deleted successfully."
    return response

if __name__ == '__main__':
    app.debug = True
    app.run()
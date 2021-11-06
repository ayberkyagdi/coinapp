from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators,FloatField
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import datetime
# Login Decorator Check
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Please login to view this page","danger")
            return redirect(url_for("login"))
    return decorated_function
# User Register
class RegisterForm(Form):
    username_register = StringField("Username:", validators=[validators.Length(min=4,max=15,message="Your username should consist of minimum 4 and maximum 15 characters"),validators.DataRequired("Please enter a username")])
    password_register = PasswordField("Password:", validators=[validators.EqualTo(fieldname="confirm",message="Passwords do not match") ,validators.Length(min=4,max=15,message="Your password should consist of minimum 4 and maximum 15 characters"),validators.DataRequired("Please enter a password")])
    email_register = StringField("Email:", validators=[validators.Length(min=4,max=35,message="Your email should consist of minimum 4 and maximum 35 characters"),validators.DataRequired("Please enter an email"),validators.Email("That is not a valid e-mail address")])
    confirm = PasswordField("Retype Your Password:")
class LoginForm(Form):
    username_login = StringField("Username:")
    password_login = PasswordField("Password:")

app = Flask(__name__)
app.secret_key = "coinmaster"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "coinadvisor"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)
@app.route("/")
def index():
    return render_template("index.html")
#Calculating Imaginary
@app.route("/calculate",methods = ["GET","POST"])
@login_required
def calculate():
    form = CalculateForm(request.form)
    if request.method == "POST" and form.validate():
        coinname_calculate = form.coinname_calculate.data
        sellprice_calculate = form.sellprice_calculate.data
        if(sellprice_calculate.find(",")):
            sellprice_calculate=sellprice_calculate.replace(",",".")            
        cursor = mysql.connection.cursor()
        query = "Select * from coins where name = %s and position = %s"
        db_coinexist = cursor.execute(query,(coinname_calculate,"OPEN"))
        mysql.connection.commit()
        coin_allinfo = cursor.fetchone()
        if db_coinexist>0 and  coin_allinfo["position"] == "OPEN":
            sellprice_calculate = float(sellprice_calculate)
            buyprice_calculate = (coin_allinfo["buyprice"])
            totalcoin = coin_allinfo["cost"]/coin_allinfo["buyprice"]
            difference = abs(sellprice_calculate - buyprice_calculate)*totalcoin
            difference = round(difference,3)
            percent = abs(((sellprice_calculate/buyprice_calculate)*100)-100)
            percent = round(percent,3)
            sign = 0
            if sellprice_calculate>buyprice_calculate: 
                percent = "+%"+str(percent)
                sign = 1
            else:
                percent = "- %"+str(percent)
            return render_template("calculate.html",sign = sign,percent = percent ,form = form, coin_allinfo = coin_allinfo, difference = difference)
        else:
            flash("No such {} coin was found".format(coinname_calculate),"danger")
        
    return render_template("calculate.html",form = form)
# Calculate Form
class CalculateForm(Form):
    coinname_calculate = StringField("Coin Name:",validators=[validators.DataRequired("Please enter a coin")])
    sellprice_calculate = StringField("Selling Price:",validators=[validators.DataRequired("Please enter a selling price")])
#Accounting List
@app.route("/account")
@login_required
def account():
    net_profit = 0
    cursor = mysql.connection.cursor()
    query = "Select * From coins where position = %s"
    db_coinexist = cursor.execute(query,("CLOSED",))
    if db_coinexist:
        all_info = cursor.fetchall()
        for info in all_info:
            net_profit+=(info["cost"]/info["buyprice"])*(info["sellprice"]-info["buyprice"])
        return render_template("account.html",all_info = all_info, net_profit = net_profit)
    else:
        return render_template("account.html")
#Listing Coins
@app.route("/listcoin")
@login_required
def listcoin():
    cursor = mysql.connection.cursor()
    query = "Select * From coins where position = %s"
    listed_coins = cursor.execute(query,("OPEN",))
    if listed_coins:
        all_info = cursor.fetchall()
        return render_template("listcoin.html",all_info = all_info)
    else:
        return render_template("listcoin.html")
# Coin Entry
@app.route("/coinentry",methods=["GET","POST"])
@login_required
def coinentry():
    form = CoinBuyForm(request.form)
    if request.method == "POST" and form.validate():
        coinname_entry = form.coinname_entry.data
        buyprice_entry = form.buyprice_entry.data
        if(buyprice_entry.find(",")):
            buyprice_entry=buyprice_entry.replace(",",".")            
        cost_entry = form.cost_entry.data
        if(cost_entry.find(",")):
            cost_entry=cost_entry.replace(",",".")  
        cursor = mysql.connection.cursor()
        query = "Select * From coins where name = %s and position = %s"
        db_coinexist = cursor.execute(query,(coinname_entry,"OPEN"))
        mysql.connection.commit()  
        coin_allinfo = cursor.fetchone()
        if db_coinexist>0 and coin_allinfo["position"] =="OPEN" :
            id = coin_allinfo["id"]
            cost_entry = float(cost_entry)
            coin_quantity_new = float(cost_entry)/float(buyprice_entry)
            coin_quantity_old = float(coin_allinfo["cost"])/float(coin_allinfo["buyprice"])
            coin_quantity_new+=coin_quantity_old
            cost_entry+=coin_allinfo["cost"]
            a = cost_entry/coin_quantity_new
            cost_entry = str(cost_entry)
            a = str(a)
            query = "Update coins SET buyprice = %s,cost = %s where id = %s"
            val = (a,cost_entry,coin_allinfo["id"])
            cursor.execute(query, val)
            mysql.connection.commit()
            cursor.close()          
            flash("{} Coin succesfully updated".format(coinname_entry),"success")
            return redirect(url_for("coinentry"))
        else:
            query = "Insert into coins(name,buyprice,cost) VALUES(%s,%s,%s)"
            cursor.execute(query,(coinname_entry,buyprice_entry,cost_entry))
            mysql.connection.commit()
            cursor.close()
            flash("{} Coin succesfully added".format(coinname_entry),"success")
            return redirect(url_for("coinentry"))
    return render_template("coinentry.html",form = form)
# Coin_buy Form
class CoinBuyForm(Form):
    coinname_entry = StringField("Coin Name:",validators=[validators.DataRequired("Please enter a coin")])
    buyprice_entry = StringField("Buying Price:",validators=[validators.DataRequired("Please enter a coin")])
    cost_entry = StringField("Cost:",validators=[validators.DataRequired("Please enter a coin")])
# Coin Sell
@app.route("/coinsell",methods=["GET","POST"])
@login_required
def coinsell():
    form = CoinSellForm(request.form)
    if request.method == "POST" and form.validate():
        coinname_sell = form.coinname_sell.data
        sellprice_sell = form.sellprice_sell.data
        if(sellprice_sell.find(",")):
            sellprice_sell=sellprice_sell.replace(",",".")  
        cursor = mysql.connection.cursor()
        query = "Select * From coins where name = %s and position = %s"
        db_coinexist = cursor.execute(query,(coinname_sell,"OPEN"))
        coin_allinfo = cursor.fetchone()
        if db_coinexist>0 and coin_allinfo["position"] == "OPEN":
            sellprice_sell = float(sellprice_sell)
            buyprice_sell = (coin_allinfo["buyprice"])
            totalcoin = coin_allinfo["cost"]/coin_allinfo["buyprice"]
            difference = abs(sellprice_sell - buyprice_sell)*totalcoin
            difference = round(difference,3)
            percent = abs(((sellprice_sell/buyprice_sell)*100)-100)
            percent = round(percent,3)
            query = "Update coins SET sellprice = %s,position = %s where name = %s"
            val = (sellprice_sell,"CLOSED",coinname_sell)
            cursor.execute(query, val)
            mysql.connection.commit()
            cursor.close()
            sign = 0
            if sellprice_sell>buyprice_sell: 
                percent = "+%"+str(percent)
                sign = 1
            else:
                percent = "- %"+str(percent)
            flash("{} succesfully sold".format(coinname_sell),"success")
            return render_template("coinsell.html",sign = sign,percent = percent ,form = form, coin_allinfo = coin_allinfo, difference = difference)
        else:
            flash("Incorrect entry","danger")
            
    return render_template("coinsell.html",form=form)

# coin_sell Form
class CoinSellForm(Form):
    coinname_sell = StringField("Coin Name:",validators=[validators.DataRequired("Please enter a coin")])
    sellprice_sell = StringField("Selling Price:",validators=[validators.DataRequired("Please enter a price")])
#Coin Delete
@app.route("/delete/<string:id>",methods=["GET","POST"])
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    query = "Select * from coins where id = %s"
    result = cursor.execute(query,(id,))
    if result:
        query = "Delete from coins where id =%s"
        cursor.execute(query,(id,))
        mysql.connection.commit()
        flash("Coin has been deleted","danger")
        return(redirect(url_for("index")))
    else:
        flash("No coin to delete","danger")
        return redirect(url_for("index"))
#Coin Update
@app.route("/update/<string:id>",methods=["GET","POST"])
@login_required
def update(id):
    form = UpdateForm(request.form)
    sellprice_update = form.sellprice_update.data
    if sellprice_update.find(","):
        sellprice_update = sellprice_update.replace(",",".")
    if  request.method == "POST" and form.validate():
        cursor = mysql.connection.cursor()
        query = "Select * from coins where id = %s"
        result = cursor.execute(query,(id,))
        result = cursor.fetchone()
        if result:
            query = "Update coins SET sellprice = %s where id = %s"
            cursor.execute(query,(sellprice_update,id))
            mysql.connection.commit()
            flash("Coin has been updated","success")
            return redirect(url_for("account"))
        else:
            flash("No coin to update","danger")
    return render_template("update.html", form = form)
# Coin Update Form
class UpdateForm(Form):
    sellprice_update = StringField("Selling Price:",validators=[validators.DataRequired("Please enter a price")])
@app.route("/coin/<string:id>")
@login_required
def details(id):
    net_profit = 0
    cursor = mysql.connection.cursor()
    query = "Select * from coins where id = %s"
    clicked_coin = cursor.execute(query,(id,))
    clicked_coin = cursor.fetchone()
    if clicked_coin :
        query = "Select * from coins where name = %s"
        all_info = cursor.execute(query,(clicked_coin["name"],))
        all_info = cursor.fetchall()
        name = clicked_coin["name"]
        for info in all_info:
            net_profit+=(info["cost"]/info["buyprice"])*(info["sellprice"]-info["buyprice"])
        return render_template("coin.html", all_info = all_info,name = name, net_profit = net_profit)
        
    else:
        return render_template("account.html")
#User Login
@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method =="POST":
        username_login = form.username_login.data
        password_login = form.password_login.data
        cursor = mysql.connection.cursor()
        query = "Select * From users where username = %s"
        db_user = cursor.execute(query,(username_login,))
        if db_user:
            user_allinfo = cursor.fetchone()
            db_password = user_allinfo["password"]
            if sha256_crypt.verify(password_login,db_password):
                flash("Welcome {}".format(username_login.capitalize()),"success")
                session["logged_in"] = True
                session["username_login"] = username_login
                return redirect(url_for("index"))
            else:
                flash("Password Incorrect","danger")
                return(redirect(url_for("login")))
        else:
            flash("There is no user such {}".format(username_login),"danger")
            return redirect(url_for("login"))
        mysql.connection.commit() 
        cursor.close()
    else:
        return render_template("login.html",form=form)
#User Login
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if request.method =="POST" and form.validate():
        username_register = form.username_register.data
        password_register = sha256_crypt.encrypt(form.password_register.data)
        email_register = form.email_register.data
        cursor = mysql.connection.cursor()
        query = "Insert into users(username,password,email) VALUES(%s,%s,%s)"
        cursor.execute(query,(username_register,password_register,email_register))
        mysql.connection.commit() 
        cursor.close()
        flash("You have successfully registered...","success")
        return redirect(url_for("login"))

    else:
        return render_template("register.html",form=form)
if __name__=="__main__":
    app.run(debug=True)
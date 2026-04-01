from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
import os

app=Flask(__name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in"in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın.","danger")
            return redirect(url_for("login"))
    return decorated_function

app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="bilgili"
app.config["MYSQL_CURSORCLASS"]= "DictCursor"

app.config['SECRET_KEY'] = os.urandom(24)
mysql=MySQL(app)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/addproduct",methods=["GET","POST"])
def addproduct():
    form=ProductForm(request.form)
    if request.method=="POST"and form.validate():
        name = form.name.data
        renkler = form.renkler.data
        min_tekrar = form.min_tekrar.data
        maks_tekrar = form.maks_tekrar.data
        maks_hiz = form.maks_hiz.data
        baski_olanaklari = form.baski_olanaklari.data
        boyut = form.boyut.data
        ekleme = form.ekleme.data

        cursor= mysql.connection.cursor()
        sorgu = """
            INSERT INTO products (name, `renkler`, `min-tekrar`, `maks-tekrar`, `maks-hız`, `Baskı-Olanakları`, `Boyut`, `ekleme`) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sorgu,(name, renkler, min_tekrar, maks_tekrar, maks_hiz, baski_olanaklari, boyut, ekleme))
        mysql.connection.commit()
        cursor.close()

        flash("Başarıyla makine eklendi","success")
        return redirect(url_for("home"))

    return render_template("addproduct.html",form=form)


class RegisterForm(Form):
    name= StringField("İsim Soyisim:",validators=[validators.Length(min=4,max=25)])
    username= StringField("Kullanıcı Adı:",validators=[validators.Length(min=5,max=35)])
    email= StringField("E-mail:",validators=[validators.Email(message="Lütfen Geçerli bir Email Adresi giriniz.")])
    password=PasswordField("Parola:",validators=[
        validators.DataRequired(message="Lütfen bir Parola belirleyiniz."),
        validators.EqualTo(fieldname="confirm",message="parolanız uyuşmuyor.")
    ])
    confirm=PasswordField("Parola Doğrula")


class ProductForm(Form):
    name = StringField("Makine İsmi", validators=[validators.Length(min=2, max=30)])
    renkler = StringField("Renkler", validators=[validators.Length(min=1)])
    min_tekrar = StringField("Min Tekrar (mm)", validators=[validators.Length(min=1)])
    maks_tekrar = StringField("Maks Tekrar (mm)", validators=[validators.Length(min=1)])
    maks_hiz = StringField("Maks Hız (m/dak)", validators=[validators.Length(min=1)])
    baski_olanaklari = StringField("Baskı Olanakları", validators=[validators.Length(min=1)])
    boyut = StringField("Boyut", validators=[validators.Length(min=1)])
    ekleme = StringField("Ekleme", validators=[validators.Length(min=1)])

class LoginForm(Form):
    username=StringField("Kullanıcı Adı")
    password=PasswordField("Parola")

@app.route("/product/<string:id>")
def product(id):
    cursor=mysql.connection.cursor()
    sorgu="SELECT * FROM PRODUCTS WHERE id=%s"
    result= cursor.execute(sorgu,(id,))

    if result>0:
        product=cursor.fetchone()
        return render_template("products_detail.html",product=product)
    else:
        return redirect(url_for("products"))
    

    
@app.route("/products")
def products():
    cursor = mysql.connection.cursor()

    sorgu = "SELECT * FROM products"
    result = cursor.execute(sorgu)

    if result > 0:
        products = cursor.fetchall()  
        return render_template("products.html", products=products)  
    else:
        return render_template("products.html")  

@app.route("/service")
def service():
    return render_template("service.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM users WHERE username=%s"
        result = cursor.execute(sorgu, (username,))
        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]

            # Şifreyi doğrula
            if sha256_crypt.verify(password_entered, real_password):
                flash("Başarıyla giriş yaptınız.", "success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("dashboard"))
            else:
                flash("Parolayı yanlış girdiniz.", "danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmuyor.", "danger")
            return redirect(url_for("login"))
    return render_template("login.html", form=form)

@app.route("/register",methods=["GET","POST"])
def register():
    form=RegisterForm(request.form)
    if request.method=="POST" and  form.validate():
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        sorgu="Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()

        flash("Başarıyla Kayıt oldunuz...","success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html",form=form)



@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM products"
    result = cursor.execute(sorgu)
    
    if result > 0:
        products = cursor.fetchall()
        return render_template("dashboard.html", products=products)
    else:
        return render_template("dashboard.html")

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor=mysql.connection.cursor()
    sorgu="SELECT * FROM  PRODUCTS where id=%s"
    result=cursor.execute(sorgu,(id,))
    if result>0:
        sorgu2="DELETE FROM PRODUCTS WHERE ID=%s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        cursor.close()
        flash("Makine Başarıyla Silindi.","success")
        return redirect(url_for("dashboard"))
    else:
        cursor.close()
        flash("Böyle bir makale yok veya bu işleme yetkiniz yok.")
        return redirect(url_for("home"))







@app.route("/logout")
def logout():
    session.clear()
    flash("Çıkış yaptınız. Panele Girmek İçin Tekrar Giriş Yapın.","success")
    return redirect(url_for("login"))


if __name__=="__main__":
    app.run(debug=True)

from flask import Flask, render_template ,request, send_from_directory,Response,redirect,url_for,flash
import cv2
import os
import datetime
from flask import jsonify
import time
import requests
import fitz
import re
import warnings
from werkzeug.utils import secure_filename
import numpy as np
from deepface import DeepFace

import db
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

from pyzbar.pyzbar import decode

app = Flask(__name__)
app.config["IMAGE_UPLOADS"] = r"C:\\Users\\Tapojita Kar\\kyc\\"

app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\\Users\\Tapojita Kar\\kyc\\database.db\\'
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
#db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    try:
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(15), unique=True)
        email = db.Column(db.String(50), unique=True)
        password = db.Column(db.String(80))
        fname = db.Column(db.String(1000))
        lname = db.Column(db.String(1000))
        print("User created")
    except:
        print("User not created")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=6, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=6, max=80)])
    fname = StringField('first name', validators=[InputRequired(), Length(min=4)])
    lname = StringField('last name', validators=[InputRequired(), Length(min=3)])

#=======================ROUTES=================================================================

#-------------Home Page---------------------
@app.route('/')
def index():
    return render_template('home.html')

#--------------LOGIN PAGE-------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                print("Succefully Logged in user\n")
                return redirect(url_for('dashboard'))
        print("Invalid Username or Password\n")
        flash("Invalid username or password")  
        return redirect(url_for('login'))
        #return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'

    return render_template('login.html', form=form)

#---------------SIGNUP PAGE----------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password,fname=form.fname.data,lname=form.lname.data)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("New user has been created!")  
            print('New user has been created!\n') 
            return redirect(url_for('login'))
        
        except:
            print("There was an issue while adding new user") 

    return render_template('signup.html', form=form)
#------------------------DASHBOARD----------------------
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', fname=current_user.fname,lname=current_user.lname,uname=current_user.username,email=current_user.email)

#------------------------CREATED BY----------------------
@app.route('/created')
@login_required
def created():
    return render_template('created.html')

#------------------------PROFILE----------------------
@app.route('/profile')
@login_required
def profile():
    f=open(app.config["IMAGE_UPLOADS"]+'comparison_result.txt','r')
    st=f.read()
    stat='Not Verified'
    if st=='1':
        stat='Verified'
    print('status : ',stat)
    return render_template('profile.html',status=stat,password='******',fname=current_user.fname,lname=current_user.lname,uname=current_user.username,email=current_user.email)

#-----------Steps Routes-------------------
@app.route('/stp1')
def stp1():
    return render_template('stp1.html')

@app.route('/stp2')
def stp2():
    return render_template('stp2.html')

@app.route('/stp3')
def stp3():
    f=open(app.config["IMAGE_UPLOADS"]+'comparison_result.txt','r')
    res=f.read()
    print(res)
    print(type(res))
    if res=='0':
        return render_template('stp3.html',result=False,fname=current_user.fname,lname=current_user.lname)
    else:
        return render_template('stp3.html',result=True,fname=current_user.fname,lname=current_user.lname)

@app.route('/stp4')
def stp4():
    return render_template('stp4.html')

@app.route('/stp5')
def stp5():
     return render_template('stp5.html')

#--------------------------End Page------------------------------
@app.route('/end')
def endpage():
    return render_template('end.html')

#------------------LOGOUT--------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('home2.html')

#------------Make New Dir DatTime.Now ----------------------------------   






@app.route("/upload-image", methods=["GET", "POST"])
def upload_image():
    dirname = ''
    if request.method == "POST":
        if request.files:
            print("REQUEST FILES")
            image = request.files["image"]
            print("IMAGE")
            upload_path = os.path.join(app.config["IMAGE_UPLOADS"], 'Uploads', image.filename)
            image.save(upload_path)
            dirname = str(datetime.datetime.now()).replace(':', '').replace('-', '').replace(' ', '')
            newpath = os.path.join('C:\\Users\\Tapojita Kar\\kyc\\imgdatabase', dirname, 'Dataset')
            print(image.filename)
            if not os.path.exists(newpath):
                os.makedirs(newpath)
            if allowed_pdf(image.filename):
                formImg(image.filename, dirname)
            else:
                print(image.filename)
                formDirectImg(image.filename, dirname)
    return render_template('stp2.html', dirname=dirname)


def allowed_pdf(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'


count1 = 0


def formImg(fileName, dirname):
    doc = fitz.open(os.path.join(app.config["IMAGE_UPLOADS"], 'Uploads', fileName))
    counter = 0
    for i in range(len(doc)):
        for img in doc.getPageImageList(i):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            img_path = os.path.join('C:\\Users\\Tapojita Kar\\kyc\\imgdatabase', dirname, 'Dataset', f"img{i}.png")
            if pix.n < 5:
                pix.writePNG(img_path)
            else:
                pix1 = fitz.Pixmap(fitz.csRGB, pix)
                pix.writePNG(img_path)
                pix1 = None
            pix = None
            counter += 1

    global count1
    count1 = 0
    for i in range(counter):
        imagePath = os.path.join('C:\\Users\\Tapojita Kar\\kyc\\pdf', f"{i}.png")
        image = cv2.imread(imagePath)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = faceCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30))
        print(f"[INFO] Found {len(faces)} Faces.")
        padding = 30
        for (x, y, w, h) in faces:
            image = cv2.rectangle(image, (x - padding, y - padding), (x + w + padding, y + h + padding), (0, 255, 0), 2)
            roi_color = image[y - 30:y + h + 30, x - 30:x + w + 30]
            face_path = os.path.join('C:\\Users\\Tapojita Kar\\kyc\\imgdatabase', dirname, 'Dataset',
                                     f'face{count1}.jpg')
            cv2.imwrite(face_path, roi_color)
            count1 += 1
        status = cv2.imwrite('C:\\Users\\Tapojita Kar\\kyc\\faces_detected.jpg', image)
        print(f"[INFO] Image faces_detected.jpg written to filesystem: {status}")


def formDirectImg(filename, dirname):
    global count1
    count1 = 0
    image_path = os.path.join(app.config["IMAGE_UPLOADS"], 'Uploads', filename)
    image = cv2.imread(image_path)
    save_path = os.path.join('C:\\Users\\Tapojita Kar\\kyc\\imgdatabase', dirname, 'Dataset', 'img0.png')
    cv2.imwrite(save_path, image)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = faceCascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=3, minSize=(30, 30))
    print(f"[INFO] Found {len(faces)} Faces.")
    padding = 30
    for (x, y, w, h) in faces:
        image = cv2.rectangle(image, (x - padding, y - padding), (x + w + padding, y + h + padding), (0, 255, 0), 2)
        roi_color = image[y - 30:y + h + 30, x - 30:x + w + 30]
        face_path = os.path.join('C:\\Users\\Tapojita Kar\\kyc\\imgdatabase', dirname, 'Dataset', f'face{count1}.jpg')
        cv2.imwrite(face_path, roi_color)
        count1 += 1
    status = cv2.imwrite('C:\\Users\\Tapojita Kar\\kyc\\faces_detected.jpg', image)
    print(f"[INFO] Image faces_detected.jpg written to filesystem: {status}")


@app.route('/opencamera', methods=['GET', 'POST'])
def camera():
    dirname = request.form['dirname']
    t = 1500
    cam = cv2.VideoCapture(0)
    cv2.namedWindow("Test")
    count = 0
    while t:
        ret, img = cam.read()
        cv2.imshow("Test", img)
        cv2.waitKey(1)
        if t == 500 or t == 1000:
            img_path = os.path.join('C:\\Users\\Tapojita Kar\\kyc\\imgdatabase', dirname, 'Dataset', f'cam{count}.jpeg')
            cv2.imwrite(img_path, img)
            count += 1
        time.sleep(0.01)
        t -= 1
        if t == 0:
            break
    cam.release()
    cv2.destroyAllWindows()
    compare(dirname)
    return redirect(url_for('stp3'))


def compare(dirname):
    global count1
    dirname_path = 'C:\\Users\\Tapojita Kar\\kyc\\dirname.txt'
    with open(dirname_path, 'w+') as p:
        p.write(dirname)
    for j in range(2):
        path1 = os.path.join('C:\\Users\\Tapojita Kar\\kyc\\imgdatabase', dirname, 'Dataset', f'cam{j}.jpeg')
        for i in range(count1):
            try:
                path2 = os.path.join('C:\\Users\\Tapojita Kar\\kyc\\imgdatabase', dirname, 'Dataset', f'face{i}.jpg')
                result = DeepFace.verify(img1_path=path1, img2_path=path2, model_name="VGG-Face",
                                         distance_metric="cosine")
                threshold = 0.30
                print(f"Is verified: {result['verified']}")
                with open('C:\\Users\\Tapojita Kar\\kyc\\comparison_result.txt', 'w+') as f:
                    f.write('1' if result["verified"] else '0')
                    if result["verified"]:
                        return ''
            except Exception as e:
                print(f"There was an issue: {e}")
    return ''



#---------------------QRCODE-----------------------------



@app.route('/scan-qr', methods=['GET', 'POST'])
def scan_qr():
    try:
        # Ensure the dirname.txt file exists
        dirname_path = os.path.join(app.config["IMAGE_UPLOADS"], 'dirname.txt')
        if not os.path.exists(dirname_path):
            print("dirname.txt file not found.")
            return render_template('stp5.html', result=False, fname=current_user.fname, lname=current_user.lname)

        with open(dirname_path, 'r') as f:
            dirname = f.read().strip()

        if request.method == "POST":
            name1 = request.form["user_name"]
            uid1 = request.form["user_uid"]

            # Ensure the image file exists
            img_path = os.path.join(f"C:\\Users\\Tapojita Kar\\kyc\\imgdatabase{dirname}\\Dataset\\img0.png")
            if not os.path.exists(img_path):
                print("Image file not found.")
                return render_template('stp5.html', result=False, fname=current_user.fname, lname=current_user.lname)

            img = cv2.imread(img_path)
            code = decode(img)
            dat = ''
            for i in code:
                dat += i.data.decode("utf-8")

            print(dat)

            uid = dat[28:40] if len(dat) > 40 else ''
            name = ''
            for i in range(50):
                if i + 48 < len(dat) and dat[i + 48] != "'":
                    name += dat[i + 48]
                else:
                    break

            print(f"Extracted UID: {uid}")
            print(f"Extracted Name: {name}")

            if uid1 == uid and name1 == name:
                print("\nQR CODE Verified\n")
                return render_template('stp5.html', result=True, fname=current_user.fname, lname=current_user.lname)
            else:
                print("\nQR CODE VERIFICATION NOT SUCCESSFUL\n")
                return render_template('stp5.html', result=False, fname=current_user.fname, lname=current_user.lname)
    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('stp5.html', result=False, fname=current_user.fname, lname=current_user.lname)


if __name__ == "__main__":
    if not os.path.exists('C:\\Users\\Tapojita Kar\\kyc\\database.db'):
        db.create_all()
    app.run(debug=True)

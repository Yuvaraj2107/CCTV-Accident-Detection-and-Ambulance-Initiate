from flask import Flask, render_template, Response, request, redirect, url_for, flash,session
import cv2
import cv2
import numpy as np  # Import NumPy
from detection import AccidentDetectionModel
import sqlite3
import os
import smtplib
from email.mime.multipart import MIMEMultipart  
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib
from email.utils import formataddr
import hashlib
from datetime import datetime
import re
from creatDB import createdatabase


app = Flask(__name__)
app.secret_key = "123"



print(createdatabase()) # this will create all tables for this project


camera=["10.0.3.2"]




@app.route('/')
def loginpage():
    session["register"]=False
    return render_template('loginpage1.html')

@app.route('/')
def registers():
    return render_template('register1.html')


@app.route('/Acctable' , methods=["GET","POST"])
def Acctable():
    search_term=""
    search_msg=""
    if request.method == "POST":
        search_term = request.form.get('search')  # Get search term from form data (POST)
    try:
        if search_term:
            sql = f"SELECT * FROM Accidentlog WHERE DayDatetime LIKE ?"
            print(f"Executing query: {sql} with arguments: '{search_term}'")  # Wrap in single quotes
            
            #sql = f"SELECT * FROM Accidentlog WHERE ACCID=?",(search_term)  # Replace with your table and column
            con = sqlite3.connect("database.db")
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute(sql, ('%' + search_term + '%',))
            search_msg="Search Result:"
        else:
            con = sqlite3.connect("database.db")
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("select * from Accidentlog")
        data = cur.fetchall()
        con.close()

        # Pass data to the template for rendering
        return render_template("logtable.html", table_data=data,search_term=search_term,msg=search_msg)
    
    except Exception as e:
        # Handle any errors that might occur during database connection or query execution
        print("searchterm",search_term)
        print(f"Error connecting to database: {e}")
        return "Error: Something went wrong!"


@app.route('/Admin', methods=["GET", "POST"])
def admin():
    adminname="Admin"
    adminpass="Admin"
    session["register"]=False
    if request.method == 'POST':
        try:
            session["Adminname"] = request.form['name']
            session["Adminpass"] = request.form['password']
            if((session["Adminname"]==adminname) and (session["Adminpass"]==adminpass)):
                    return redirect("register")
            else:
                flash("Username and password Mismatch", "danger")


        except Exception as e:
            print(f"Error: {str(e)}")
            flash("Check Your AdminName And AdminPassword","danger")


    return render_template('admin.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        try:
            session["name"] = request.form['name']
            session["password"] = request.form['password']

            log_pwd=hashlib.sha256(session["password"].encode())
            log_hsh=log_pwd.hexdigest()

            
            
            con = sqlite3.connect("database.db")
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("select * from ControlRoom where name=? and password=?", (session["name"], log_hsh))
            data = cur.fetchone()

            if data:

                if(session["name"]==data["name"] and log_hsh==data["password"]):
                    return redirect("home")
            else:
                flash("Username and password Mismatch", "danger")

        except Exception as e:
            print(f"Error: {str(e)}")
            flash("Check Your Name And Password","danger")

    
    if request.method == 'GET': #Logout session clearing
        session.pop("name",None)
        session.pop("password",None)
        session.pop("Adminname",None)
        session.pop("Adminpass",None)
        session.pop("register",None)

    return redirect(url_for("loginpage"))



@app.route('/register', methods=['GET','POST'])
def register():
    session["register"]=True
    if request.method=='POST':
        try:
            name=request.form['name']
            mail=request.form['address']
            passwrd=request.form['passwords']
            
            reg_pwd=hashlib.sha256(passwrd.encode())
            reg_hsh=reg_pwd.hexdigest()

            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            print(mail)
            
            if(re.match(email_regex, mail)):
                con=sqlite3.connect("database.db")
                cur=con.cursor()
                cur.execute("insert into ControlRoom(name,mail,password)values(?,?,?)",(name,mail,reg_hsh))
                con.commit()
                flash("Record Added Successfully","success")
                return redirect(url_for("loginpage"))
                con.close()
            else:
                flash("Invalid mail ID","danger")
                #return redirect(url_for("register"))
            
        except sqlite3.OperationalError as e:
            print("SQLite Operational Error:", e)
            flash("Error in Insert Operation","danger")
        #finally:
            #return redirect(url_for("registerpage"))
            #con.close()

    #return redirect(url_for("register")
    return render_template('register1.html')


model = AccidentDetectionModel("model.json", 'model_weights.h5')
font = cv2.FONT_HERSHEY_SIMPLEX

def startapplication():
    cnt=0 # avoid false prediction
    now = datetime.now()
    rand=now.strftime("%d %m %Y %H %M")
    
    video = cv2.VideoCapture(0)  # Assuming you want to use the default camera
    if not video.isOpened():
        print("Error: Couldn't open video capture.")
        return "Error: Couldn't open video capture."

    while True:
        ret, frame = video.read()
        if not ret:
            print("Error: Couldn't retrieve frame.")
            break

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        roi = cv2.resize(gray_frame, (250, 250))

        pred, prob = model.predict_accident(roi[np.newaxis, :, :])  # Now np.newaxis is defined
        print(pred)
        
        if pred == "Accident":
            prob = round(prob[0][0] * 100, 2)
            print(prob)
            
            if(prob>=90):
                cnt=cnt+1
            cv2.rectangle(frame, (0, 0), (280, 40), (0, 0, 0), -1)
            cv2.putText(frame, pred + " " + str(prob), (20, 30), font, 1, (255, 255, 0), 2)
            
            if (prob>=92 and cnt>=3):
                     save_image(frame,rand) #unique file name
                     print(cnt)
                     dbloc = location_fetcher()

                     accidentlogger(int(rand.replace(" ","")),dbloc["AccLoc"],dbloc["HospName"])  #Accident data logging
                     
                     if(len(dbloc)>1):
                         loc=dbloc["AccLoc"] 
                         hosp=dbloc["HospName"]
                     subject = "Accident Detected At:"+loc+"Alert:"+hosp
                     print(subject)
                     


                     receiver_email=dbloc["HopsMailID"]  #hospital email address
                       
                     
                     sender_email = ''  #control room email address
                     sender_password = ''       #control room email address

                     smtp_server = "smtp.gmail.com"
                     smtp_port = 587

                     mmail = sender_email
                     hmail = receiver_email

                     sender_name = "Control Room"
                     receiver_name = dbloc["HospName"]
                     
                     msg = MIMEMultipart()
                    
                     txt_msg="https://www.google.com/search?q="+str(dbloc["lattitude"])+"+"+str(dbloc["longitude"])
                     
                     msg.attach(MIMEText(txt_msg, 'plain'))   # Attach the text message to the MIMEMultipart object
                     
                     
                     image_folder="accident_frames/image"+rand+".jpg"
                     image_data = cv2.imread(image_folder)
                     image_bytes = cv2.imencode('image'+rand+'.jpg', image_data)[1].tobytes()
                     image_attachment = MIMEImage(image_bytes, name="image"+rand+".jpg")
                     msg.attach(image_attachment)
                     
                     msg['To'] = formataddr((receiver_name, hmail))
                     msg['From'] = formataddr((sender_name, mmail))
                     msg['Subject'] = subject

                     #Email server code
                     
                     server = smtplib.SMTP(smtp_server, smtp_port)       
                     server.ehlo()
                     server.starttls()
                     password = sender_password
                     server.login(mmail,password)
                     server.sendmail(mmail, [hmail], msg.as_string())
                     server.quit()
                     
                     break
                    
        ret, jpeg = cv2.imencode('.jpg', frame)
        frame = jpeg.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        

@app.route('/home')
def home():
    if(("name" in session )and("password" in session)):
        return render_template('home.html')
    elif((session["register"]==True)):
        return render_template('home.html')
    elif(("Adminname" in session ) and ("Adminpass" in session)):
        return render_template('register1.html')


    else:
        return redirect(url_for("loginpage"))

@app.route('/accident_detection', methods=["GET"])
def accident_detection():
    return Response(startapplication(), mimetype='multipart/x-mixed-replace; boundary=frame')

predist={}#dbug

@app.route('/video', methods=["GET", "POST"])
def video():
    
        cont=0  #to prevent false prediction

        now = datetime.now()   #date and time
        rand=now.strftime("%d %m %Y %H %M")
        
        video = request.files['videoFile']
        print(video)
        if 'videoFile' not in request.files:    
            return "No video file selected"
        video_file = request.files['videoFile']
        
        if video_file.filename == '':
            return "No selected file"
        
        video_path = 'uploads/' + video_file.filename
        video_file.save(video_path)
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return "Error: Unable to open video file"
        
        while True:
            
            ret, frame = cap.read()
            if not ret:
                print("Error: Couldn't retrieve frame.")
                print("predlst",predist) ##dbug
                return "No Accident Occured"
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            roi = cv2.resize(gray_frame, (250, 250))
            pred, prob = model.predict_accident(roi[np.newaxis, :, :])
            print(pred)
            cv2.imshow('Video', frame)
            
            if pred == "Accident":
                prob = round(prob[0][0] * 100, 2)
                print(prob)
                
                if(int(str(prob).split('.')[0]) in predist):
                    predist[int(str(prob).split('.')[0])]+=1
                else:
                    predist[int(str(prob).split('.')[0])]=1
                
                if(prob>=90):     #TO avoid false prediction
                    cont=cont+1
                    
                cv2.rectangle(frame, (0, 0), (280, 40), (0, 0, 0), -1)
                cv2.putText(frame, pred + " " + str(prob), (20, 30), font, 1, (255, 255, 0), 2)
                
                if (prob>=95 and cont>=5):
                     save_image(frame,rand) #unique filename
                     
                     
                     dbloc = location_fetcher()

                     accidentlogger(int(rand.replace(" ","")),dbloc["AccLoc"],dbloc["HospName"])
                     
                     if(len(dbloc)>1):
                         loc=dbloc["AccLoc"] 
                         hosp=dbloc["HospName"]
                     subject = "Accident Detected At:"+loc+"Alert:"+hosp
                     print(subject) #dbug
                    

                     receiver_email=dbloc["HopsMailID"] #Hospital Email
                       
                     
                     sender_email = 'yuvaraj200216@gmail.com'   #control Room Email
                     sender_password = 'hhfnuhyfaqtackbh'       #control Room Email passwrd
                     
                     smtp_port = 587
                     smtp_server="smtp.gmail.com"
                
                     mmail = sender_email      
                     hmail = receiver_email
                     
                     sender_name= "Control Room"
                     receiver_name=dbloc["HospName"]
                     msg = MIMEMultipart()
                     
                     
                     txt_msg="https://www.google.com/search?q="+str(dbloc["lattitude"])+"+"+str(dbloc["longitude"])
                     
                     msg.attach(MIMEText(txt_msg, 'plain'))   # Attach the text message to the MIMEMultipart object
                     
                     image_folder="accident_frames/image"+rand+".jpg"
                     image_data = cv2.imread(image_folder)
                     image_bytes = cv2.imencode('image'+rand+'.jpg', image_data)[1].tobytes()
                     image_attachment = MIMEImage(image_bytes, name="image"+rand+".jpg")
                     msg.attach(image_attachment)
                     
                     msg['To'] = formataddr((receiver_name, hmail))
                     msg['From'] = formataddr((sender_name, mmail))
                     msg['Subject'] = subject
                     
                     server = smtplib.SMTP(smtp_server, smtp_port)
                     server.ehlo()
                     server.starttls()
                     password = sender_password
                     server.login(mmail, password)
                     server.sendmail(mmail, [hmail], msg.as_string())
                     server.quit()
                     
                     break
            ret, jpeg = cv2.imencode('.jpg', frame)
            frame = jpeg.tobytes()
            
            

            if cv2.waitKey(1) & 0xFF == ord('q'): #TO stop the process 'q'
                break
        cap.release()
        cv2.destroyAllWindows()
        
        print("predist",predist) #dbug
        print(cont)#dbug
        
        #return "Video processed successfully"
        return redirect(url_for("Acctable"))

def save_image(frame,srand):
    directory = 'accident_frames'
    if not os.path.exists(directory):
        os.makedirs(directory)
    filename = os.path.join(directory, 'image'+srand+'.jpg')
    cv2.imwrite(filename, frame)
    print(f"Accident frame saved as: {filename}")

def location_fetcher():
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("select * from Location where IPaddrs=?",(camera))
    dbloc = cur.fetchone()
    return dbloc

def accidentlogger(ID,Loc,hospname):

    now = datetime.now()
    dt=now.strftime("%d/%m/%Y-%H:%M%p")

    con=sqlite3.connect("database.db")
    cur=con.cursor()
    cur.execute("insert into Accidentlog(ACCID,DayDatetime,location,Hospital)values(?,?,?,?)",(ID,dt,Loc,hospname))
    con.commit()

if __name__ == '__main__':
    app.run(debug=False, port=700)

from flask import Flask,redirect,url_for,render_template,request,send_file,flash,session,send_from_directory,abort
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField,SelectField,StringField
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired
from flaskext.mysql import MySQL
import pymysql
import os
import shutil
import hashlib
import time


from io import BytesIO
from datetime import datetime

app = Flask(__name__,template_folder="templates",static_folder="static")
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SOURCE'] = "static/video/"
app.config['UPLOAD_FOLDER'] = 't2/'
app.config['time_start'] = ''
app.config['VIDEO'] = 'video/'
app.config['ALLOWED_VIDEO_EXTENSION'] = [".MP4",'.mp4']
mysql = MySQL()


app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD']= ''
app.config['MYSQL_DATABASE_DB']='phude'
app.config['MYSQL_DATABASE_HOST']='localhost'
mysql.init_app(app)

# today = datetime.today()

# time = today.strftime("%H") + "h" + today.strftime("%M")
# date = today.strftime("%Y-%m-%d") 

# dateVN = today.strftime("%d-%m-%Y")

# days = f'{time}- {dateVN}'







# Get number data of database
def get_num_of_items():

    conn = mysql.connect()
    cursor1 = conn.cursor()

    
    user = session['user']
    cur = cursor1.execute("SELECT * FROM ketquataophude WHERE username=%s",user)
    return (cur)

def check_dk():
    conn = mysql.connect()
    
    cursor3 = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor3.execute("SELECT username FROM user")
    users = cursor3.fetchall()
    user_list = []
    for u in users:
        if u:
            user_list.append(u['username'])
    return user_list



def check_name():
    user = session['user']

    conn = mysql.connect()
    
    cursor3 = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor3.execute("SELECT output_srt FROM ketquataophude WHERE username=%s",(user) )
    ta = cursor3.fetchall()
    
    fullname = []
    for t in ta:
        # print(t['output_srt'])
        name = os.path.splitext(t['output_srt'])[0]
        fullname.append(name)
    return fullname


@app.route("/",methods=["GET","POST"])

def login():
    if "user" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form['username']
        password = hashlib.md5(request.form['password'].encode())
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * from user WHERE username=%s",username)
        userlist = cursor.fetchall()
        if not userlist:
            flash("Tài khoản hoặc mật khẩu không đúng!")
        name = userlist[0]['username']
        pass_word = userlist[0]['password']
        password = password.hexdigest()
        if username == name and password == pass_word:
                session['user'] = username
                flash("Đăng nhập thành công")
                return redirect(url_for("index"))
        else:
            flash("Mật khẩu không đúng!")
            
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()       
    
        
    return render_template('login.html')
@app.route('/dangky',methods=['POST','GET'])
def dang_ky():
    if "user" in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if len(username) < 4:
            flash('Tên tài khoản ít nhất 4 kí tự!')
            return redirect(url_for('dang_ky'))
        if len(password) < 6:
            flash('Mật khẩu ít nhất 6 kí tự!')
            return redirect(url_for('dang_ky'))

        if username not in check_dk():
            conn = mysql.connect()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("INSERT INTO user(username,password) VALUES(%s,MD5(%s))",(username,password))
            conn.commit()
            session['user'] = username
            flash("Đăng kí thành công")
            return redirect(url_for('index'))
        else:
            flash("Tài khoản đã tồn tại!")


        
    return render_template('dangky.html')


def login(err):
    return render_template("login.html",err)


class UploadFileForm(FlaskForm):
    file = FileField("File",validators=[InputRequired()])
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * from ngonngu")
    languages  = cursor.fetchall()
    language_l = []
    file_noise = []
    for langs in languages:
        lang = (langs['ma_nn'],langs['ten_nn'])
        language_l.append(lang)
    language_list = [(None,'Chọn ngôn ngữ')]
    language_list.extend(language_l)

    cursor2 = conn.cursor(pymysql.cursors.DictCursor)
    cursor2.execute("SELECT * FROM giaithuatnhieu")
    noises = cursor2.fetchall()

    for noise in noises:
        reduce = (noise['ma_gt'],noise['ten_gt'])
        file_noise.append(reduce)
    
    language = SelectField("Ngôn ngữ ", choices=language_list)
    language2 = SelectField("Ngôn ngữ 2",choices=language_list)
    name = StringField(u'Tên bài',validators=[InputRequired()])
    algorithm = SelectField("Giảm nhiễu",choices=file_noise)
    submit = SubmitField("Tạo phụ đề")

class DownloadFile(FlaskForm):
    submit2 = SubmitField("Tải phụ đề (.srt)")


@app.route("/index",methods=["POST","GET"])

def index():
    
    print(check_name())
   
    if "user" not in session:
        return redirect(url_for("login"))
    
    form = UploadFileForm()
    if "user" in session:
        user = session["user"]
    
    
   
    if form.validate_on_submit():

        source = app.config['SOURCE']
        PATH = app.config['UPLOAD_FOLDER']

        conn = mysql.connect()

        start_time = datetime.now()
        
        
        file = form.file.data
        filename = file.filename
        name = filename[:filename.index('.mp4')]
        language_in = form.language.data
        language_out = form.language2.data
        choose_algorithm = form.algorithm.data
        file_ext = filename[filename.index('.'):]
        newname = form.name.data
      
        if file_ext not in app.config['ALLOWED_VIDEO_EXTENSION']:
            flash("Định dạng file không hợp lệ!")
            return redirect(url_for('index'))
        
        if newname in check_name():
            flash("Tên file đã tồn tại!Vui lòng chọn tên mới")
            return redirect(url_for('index'))
        if language_in == 'None':
            flash("Chọn ngôn ngữ gốc")
            return redirect(url_for('index'))
        if language_out == 'None':
            flash("Chọn ngôn ngữ đầu ra")
            return redirect(url_for('index'))
        os.makedirs(PATH, exist_ok=True)
        # Thời gian bắt đầu thực thi
        start_time = time.time()
        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename)))
        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['SOURCE'],secure_filename(file.filename)))
       
        
        os.system('python3 phude.py {} -s {} -d {} -noise {} -n {} '.format(PATH+file.filename,language_in,language_out,choose_algorithm,newname))

        if language_in == language_out:
            file_srt = newname + '.srt' 
            shutil.move(PATH+file_srt, source)
        else:
            file_srt_org = newname + '.srt'   
            file_srt = newname + '_translated.srt'
            shutil.move(PATH+file_srt_org, source)
            shutil.move(PATH+file_srt, source)
        # 
        file_output = newname + '.mp4'
        shutil.move(PATH+file_output, source)
        # Thời gian kết thúc
        if language_in != language_out: 
            os.system('ffmpeg -y -i {} -filter_complex "subtitles={}" {}'.format(PATH+file.filename,source+newname+'.srt',source+newname+'_out.mp4'))
        end_time = time.time()
        time_xuly = round(float(end_time-start_time),2)
        
        # print(str(end_time - start_time))
        cursor1 = conn.cursor(pymysql.cursors.DictCursor)
        cursor1.execute("INSERT INTO ketquataophude(name_video,username,ma_gt,ma_nn_input,ma_nn_output,thoigianxuly,output_srt,output_mp4) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",(filename,user,choose_algorithm,language_in,language_out,time_xuly,newname+'.srt',newname+'.mp4'))
        # userlist = cursor1.fetchall()
        conn.commit()
        # if os.path.exists(PATH):
        #     shutil.rmtree(PATH)
       
        return redirect(url_for("loading",filename=newname+'.mp4'))
    return render_template('index.html',form=form)



@app.route("/loading/<filename>",methods = ["POST","GET"])

def loading(filename):
    if "user" not in session:
        return redirect(url_for("login"))
    if "user" in session:
        user = session["user"]
    down = DownloadFile()
    conn = mysql.connect()
    cursor3 = conn.cursor(pymysql.cursors.DictCursor)
    name = filename[:filename.index('.mp4')]
   
    cursor3.execute("SELECT * FROM ketquataophude WHERE username=%s and output_mp4=%s",(user,filename) )
    historys = cursor3.fetchall()
    PATH = app.config['UPLOAD_FOLDER']
    SOURCE =app.config['VIDEO']
    # flash(filename)
    redirect(url_for("loading",filename=PATH+filename),code=301)
    if historys:
        lang_in = historys[0]['ma_nn_input']
        lang_out = historys[0]['ma_nn_output']
        nn = lang_out+'/'+lang_in
        session['nn'] = nn
    if down.validate_on_submit():
            lang_in = historys[0]['ma_nn_input']
            lang_out = historys[0]['ma_nn_output']
            if lang_in == lang_out:
                srt = (filename[:filename.index(".mp4")]+'.srt')
                return send_from_directory(app.config['SOURCE'],srt,as_attachment=True)
            else:
                srt = (filename[:filename.index(".mp4")]+'_translated.srt')
                return send_from_directory(app.config['SOURCE'],srt,as_attachment=True)
    

    return render_template("loading.html",down=down,filename=SOURCE+filename)


@app.route("/dangxuat")

def dangxuat():
    if "user" not in session:
        redirect(url_for("login"))
    if "user" in session:
        session.pop("user",None)
        flash("Đăng xuất thành công!")
    return redirect(url_for("login"))
# def success():
#     return render_template("success.html")

@app.route("/lichsu")

def lichsu():
    try:
        if "user" in session:
            user = session["user"]

        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM user WHERE username=%s",user)
        userlist = cursor.fetchall()

        cursor1 = conn.cursor(pymysql.cursors.DictCursor)
        cursor1.execute("SELECT * FROM ketquataophude WHERE username=%s",userlist[0]['username'])
        userlist1 = cursor1.fetchall()

       
        quantity = get_num_of_items()

        return render_template("lichsu.html",data=userlist1,quantity=quantity)

        # return render_template("lichsu.html",data=userlist1,quantity=quantity)
        

        
        # return redirect(url_for("index"))
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()  
    return render_template("lichsu.html")

@app.route("/xoa/<filename>",methods=['POST','GET'])

def xoa(filename):
    if "user" not in session:
        return redirect(url_for("login"))
    if "user" in session:
        user = session["user"]
    conn = mysql.connect()
    name = filename[:filename.index('.mp4')]
    source = app.config['SOURCE']
    if os.path.exists(source+filename):
        os.remove(source+filename)
    if os.path.exists(source+name+'.srt'):
        os.remove(source+name+'.srt')
    cursor3 = conn.cursor(pymysql.cursors.DictCursor)
    cursor3.execute("DELETE FROM ketquataophude WHERE username=%s and output_mp4=%s",(user,filename))
    conn.commit()
    flash("File {} được xoá thành công".format(filename))
    return redirect(url_for('lichsu'))

#
if __name__ == "__main__":
    # app.run(debug=True)
    app.run(debug=True,host='127.0.0.1',port=5003)
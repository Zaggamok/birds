import os
import sqlite3
from flask import Flask, request, Response, session, g, redirect, url_for, abort, \
    render_template, flash, send_from_directory
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask('birds')
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'birds.db'),
    SECRET_KEY='development key',
    USERNAME='dave',
    PASSWORD='spoon',
    UPLOAD_FOLDER=os.path.join(app.root_path, 'static/img'),
    MAX_CONTENT_LENGTH=16*1024*1024
))
app.config.from_envvar('BIRDS_SETTINGS', silent=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


# allow for easy connections to the specified database
def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


# flask creates application context. Command: "flask initdb"
@app.cli.command('initdb')
def initdb_command():
    # initialises the database
    init_db()
    print('Initialised the database.')


# opens new db conn if there is none yet for the current application context
def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


# closes the db again at the end of every request
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            #^ session.get('user') ???
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/up', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect((url_for('uploaded_file', filename=filename)))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute('select title, text, imgurl from entries order by id desc')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)

    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            fileurl = ('/static/img/' + filename)
            print('fileurl:', fileurl)
            db = get_db()
            db.execute('insert into entries (title, text, imgurl) values (?, ?, ?)', [request.form['title'], request.form['text'], fileurl])
            db.commit()
            flash('New entry was successfully posted')
            return redirect(url_for('show_entries'))



@app.route('/secret_page')
@login_required
def secret():
    return '''
    <p>shhhhh it's a secret!</p>
    '''


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            session['username'] = request.form['username']
            g.user = request.form['username']
            flash('Hello ' + session['username'] + ', you were logged in ')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    g.user = None
    flash('You were logged out')
    return redirect(url_for('show_entries'))


if __name__ == '__main__':
    app.run()
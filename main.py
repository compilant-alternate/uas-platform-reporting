# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from datetime import datetime
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# MySQL Configuration
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'port': os.getenv('DB_PORT'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}


# Login decorator
def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


# Database connection
def get_db_connection():
    return mysql.connector.connect(**db_config)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit_report', methods=['POST'])
def submit_report():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        email = request.form['email']
        title = request.form['title']
        level = request.form['level']
        report_type = request.form['type']
        urls = request.form['urls']
        description = request.form['description']
        timestamp = datetime.now()
        status = 'Pending'

        query = """INSERT INTO reports 
                  (email, title, level, type, urls, description, timestamp, status) 
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query, (email, title, level, report_type, urls,
                               description, timestamp, status))

        conn.commit()
        flash('Report submitted successfully!', 'success')
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Error submitting report: {str(e)}', 'error')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == os.getenv('USERNAME') and password == os.getenv('PASSWORD'):
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reports ORDER BY timestamp DESC")
    reports = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('dashboard.html', reports=reports)


@app.route('/report/<int:id>')
@login_required
def view_report(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reports WHERE id = %s", (id, ))
    report = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('report_detail.html', report=report)


@app.route('/update_status/<int:id>', methods=['POST'])
@login_required
def update_status(id):
    new_status = request.form['status']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE reports SET status = %s WHERE id = %s",
                   (new_status, id))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Status updated successfully!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/delete_report/<int:id>', methods=['POST'])
@login_required
def delete_report(id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete the report
        cursor.execute("DELETE FROM reports WHERE id = %s", (id, ))
        conn.commit()

        flash('Report deleted successfully!', 'success')
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Error deleting report: {str(e)}', 'error')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)

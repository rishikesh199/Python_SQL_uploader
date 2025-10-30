from flask import Flask, render_template, request, flash, redirect, url_for, session
import pandas as pd
import psycopg2
import numpy as np
from werkzeug.utils import secure_filename
import os
import tempfile
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 32MB max-limit
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class DatabaseManager:
    @staticmethod
    def test_connection(host, user, password, database):
        try:
            conn = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                dbname=database
            )
            conn.close()
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_pg_type(dtype):
        dtype_str = str(dtype)
        if dtype_str.startswith(('int', 'uint')):
            return 'BIGINT'
        elif dtype_str.startswith('float'):
            return 'DOUBLE PRECISION'
        elif dtype_str.startswith('datetime'):
            return 'TIMESTAMP'
        elif dtype_str == 'bool':
            return 'BOOLEAN'
        elif dtype_str == 'object':
            return 'TEXT'
        else:
            return 'TEXT'

    @staticmethod
    def clean_column_name(col):
        # Remove special characters and spaces
        clean = ''.join(e.lower() for e in col if e.isalnum() or e == '_')
        # Ensure it doesn't start with a number
        if clean[0].isdigit():
            clean = 'col_' + clean
        return clean

    @staticmethod
    def create_table_and_upload_data(db_config, df, table_name):
        conn = None
        cursor = None
        try:
            # Clean and validate table name
            table_name = ''.join(e.lower() for e in table_name if e.isalnum() or e == '_')
            if table_name[0].isdigit():
                table_name = 'tbl_' + table_name

            # Clean column names
            df.columns = [DatabaseManager.clean_column_name(col) for col in df.columns]

            # Pre-process data: Convert all numeric columns to appropriate types
            for col in df.columns:
                # Convert to string first to handle numpy types
                if df[col].dtype.name.startswith(('int', 'float')):
                    # Convert numpy types to Python native types
                    df[col] = df[col].astype(object).where(pd.notna(df[col]), None)
                    try:
                        # Try converting to numeric
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    except:
                        pass

            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()

            # Create table with proper types
            columns = []
            for column in df.columns:
                if pd.api.types.is_numeric_dtype(df[column]):
                    if df[column].dtype == 'float64':
                        pg_type = 'DOUBLE PRECISION'
                    else:
                        pg_type = 'BIGINT'
                elif pd.api.types.is_datetime64_any_dtype(df[column]):
                    pg_type = 'TIMESTAMP'
                else:
                    pg_type = 'TEXT'
                columns.append(f'"{column}" {pg_type}')

            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS "{table_name}" (
                id SERIAL PRIMARY KEY,
                {', '.join(columns)},
                upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_table_query)

            # Insert data
            placeholders = ','.join(['%s'] * len(df.columns))
            columns = ','.join([f'"{col}"' for col in df.columns])
            insert_query = f'INSERT INTO "{table_name}" ({columns}) VALUES ({placeholders})'
            
            # Convert DataFrame to list of tuples with proper NULL handling
            data = []
            for row in df.values:
                cleaned_row = []
                for val in row:
                    if pd.isna(val) or val == 'None' or val == '':
                        cleaned_row.append(None)
                    elif isinstance(val, (np.integer, np.floating)):
                        cleaned_row.append(float(val) if isinstance(val, np.floating) else int(val))
                    else:
                        cleaned_row.append(val)
                data.append(tuple(cleaned_row))

            cursor.executemany(insert_query, data)
            conn.commit()
            
            return True, len(data)

        except pd.errors.EmptyDataError:
            return False, "The file appears to be empty"
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            return False, f"Database error: {str(e)}"
        except Exception as e:
            if conn:
                conn.rollback()
            return False, f"Error: {str(e)}"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/connect', methods=['POST'])
def connect():
    host = request.form.get('host', 'localhost')
    user = request.form.get('user', '')
    password = request.form.get('password', '')
    database = request.form.get('database', '')

    success, message = DatabaseManager.test_connection(host, user, password, database)
    if success:
        session['db_config'] = {
            'host': host,
            'user': user,
            'password': password,
            'dbname': database
        }
        flash('Successfully connected to database!', 'success')
        return redirect(url_for('upload'))
    else:
        flash(f'Connection failed: {message}', 'danger')
        return redirect(url_for('index'))

@app.route('/upload')
def upload():
    if 'db_config' not in session:
        flash('Please connect to database first', 'warning')
        return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/process', methods=['POST'])
def process():
    if 'files' not in request.files:
        flash('No files selected', 'danger')
        return redirect(url_for('upload'))

    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        flash('No files selected', 'danger')
        return redirect(url_for('upload'))

    results = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            table_name = os.path.splitext(filename)[0]
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                file.save(filepath)
                
                # Read file based on extension
                if filename.endswith('.csv'):
                    df = pd.read_csv(filepath, low_memory=False)
                else:
                    df = pd.read_excel(filepath)

                # Check if DataFrame is empty
                if df.empty:
                    results.append(f'❌ {filename}: File is empty')
                    continue

                success, result = DatabaseManager.create_table_and_upload_data(
                    session['db_config'], df, table_name
                )
                
                if success:
                    results.append(f'✅ {filename}: {result} records uploaded to table "{table_name}"')
                else:
                    results.append(f'❌ {filename}: {result}')

            except Exception as e:
                results.append(f'❌ {filename}: {str(e)}')
            finally:
                if os.path.exists(filepath):
                    os.remove(filepath)
        else:
            results.append(f'❌ {file.filename}: Invalid file type')

    if results:
        flash('<br>'.join(results), 'info')
    return redirect(url_for('upload'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
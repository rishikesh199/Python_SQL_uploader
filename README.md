# Python_SQL_uploader

This Flask-based web app provides a simple web interface where you can select and upload multiple files (CSV, XLSX, XLS) at once. Each file's data is automatically uploaded to a separate table in the PostgreSQL database, with no manual intervention required.

---

## Business Requirement

Many organizations need to upload multiple Excel/CSV files to a database at once, such as sales, inventory, or HR data from different branches. Manual upload is slow, error-prone, and requires separate processes for each file. Fast and accurate data upload to the database is essential for reporting, analytics, and automation.

---

## Actual Problem

- **Manual Upload:** Uploading each file separately is time-consuming.
- **Data Consistency:** Repeated manual uploads increase the risk of errors.
- **Speed Issues:** Uploading large or multiple files together can slow down the system.
- **Technical Barrier:** Direct database uploads are difficult for non-technical users.

---

## Solution

This project solves these problems by providing a simple web interface for bulk file upload. Each file is automatically uploaded to a separate table in PostgreSQL, with automatic table creation and data type detection.

---

## Key Features
- **Multiple File Upload:** Upload as many files as you want at once.
- **Automatic Table Creation:** Each file creates its own table, with columns based on the file's columns.
- **Bulk Insert:** Data is uploaded quickly, optimized to complete within 10-20 seconds for normal file sizes.
- **Error Handling:** Clear messages for empty files or wrong formats.
- **User Friendly:** Easy for non-technical users to operate.

---

## Benefits

- **Time Saving:** Uploading multiple files at once reduces manual effort.
- **Accuracy:** Automated process minimizes the chance of incorrect data uploads.
- **Scalability:** Large datasets or data from multiple branches can be uploaded in one go.
- **Business Agility:** Data is available in the database quickly, enabling faster reporting and decision-making.
- **No Technical Hassle:** Users only need to provide database details and files; everything else is automated.

---

## Technical Details

- **Tech Stack:** Python (Flask), Pandas, psycopg2, numpy, Werkzeug
- **Supported File Types:** CSV, XLSX, XLS
- **Database:** PostgreSQL
- **Max File Size:** 100MB (configurable)
- **How It Works:**
  1. User enters database details.
  2. Selects multiple files to upload.
  3. Each file's data is uploaded to a separate table.
  4. Status messages are shown for each file.

  ## Snapshot
  ### Start Page
![Start Page](https://github.com/rishikesh199/Python_SQL_uploader/blob/main/Web_Start_Page.png)

### After Login
![AfterLogin.png](https://github.com/rishikesh199/Python_SQL_uploader/blob/main/Web_AfterLogin.png)

### After Selecting Multiple Files
![Start Page](https://github.com/rishikesh199/Python_SQL_uploader/blob/main/Web_AfterSelectingMultipleFile.png)

### After Uploaded
![After Uploaded](https://github.com/rishikesh199/Python_SQL_uploader/blob/main/Web_After_Uploaded).

# Pseudo Code — Email Sending Service with Template Rendering

---

## 1. Initialize Configurations & Environment

- **Load required modules for:**
  - File system, SMTP, email formatting, date/time, background tasks
  - Template rendering (Jinja2)
  - Custom utility modules (logger, DB connection, config, exceptions, models)
- **Initialize** logger from singleton logger.
- **Load** environment-specific configuration values.
- **Set** SMTP server details (host, port, user, password, `from_email`).
- **Configure** Jinja2 to load HTML templates from `html_templates` folder.
- **Define** a dictionary mapping template names to template file names.

---

## 2. Function: `send_emails_process(request, background_tasks)`

- **If** background tasks parameter is given:
  - Add `send_email_function(request)` to background task queue.
  - **Return:** status `"processing"` and message `"Email queued for sending"`.
- **Else:**
  - Call `send_email_function(request)` directly (synchronous).
  - **Return:** status `"success"` and message `"Email sent successfully"`.
- **If** any error occurs:
  - Log error.
  - Raise exception.

---

## 3. Function: `send_email_function(request)`

1. **If** `request.Type` is not `"email"`:
   - Log and exit function.
2. Get template file name from `template_mapping` using `request.TemplateName`.
   - **If** not found → raise `ValueError`.
3. **Try:**
   - Load and render HTML template:
     - Create rendering context from `request.EmailBody`.
     - Add `"Date"` (current date) and `"Subject"` to context.
   - **If** template is `"Template-Table"` or `"Template-Mediation"`:
     - Get `Table_Filter_infor.data` from email body.
     - Convert this data into an HTML table using `build_html_table()` and add to context as `"DYNAMIC_TABLE"`.
   - Render HTML body with the prepared context.
4. **If** template file not found → log and raise error.
5. **If** rendering fails → log and raise error.

---

## 4. Prepare Email Message

- Create multipart email object.
- **Set From:**
  - If `Sender_Name` exists: format `"Name <email>"`.
  - Else: just use `FROM_EMAIL`.
- **Set To** to `request.SendersMail`.
- **Set Cc** to a joined string of all CC addresses.
- **Set email Subject**.
- Attach HTML body.
- **For each** attachment:
  - **If** file exists → read and attach.
  - **Else** log a warning.

---

## 5. Send Email

- Set `status = "success"`, record `sent_at = now`.
- **Try:**
  - Connect to SMTP server.
  - Start TLS encryption.
  - If credentials exist → log in.
  - Send message.
  - Log success.
- **If** error occurs:
  - Set `status = "failed"`.
  - Log failure and raise error.
- **Finally:**
  - Try inserting email log into MongoDB.
  - If DB connection fails → raise `DatabaseConnectionError`.
  - If update fails → raise `DatabaseUpdateError`.
  - Log DB insertion success.

---

## 6. Function: `build_html_table(data)`

- **If** no data:
  - Return `<p>No data available.</p>`.
- Extract table headers from first dictionary’s keys.
- Start HTML table with border and styling.
- Add header row with all keys.
- **For each** data row:
  - Add table row with values.
  - If value is a list of 2 items → format `"item1 - item2"`.
- Close HTML table and return as string.




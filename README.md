# Pseudocode — Email Sending Service with HTML Templates & Attachments

---

## Initialize Configurations & Environment

1. **Import Required Modules**  
   - OS, SMTP, MIME modules (for email formatting)  
   - Datetime, BackgroundTasks (for async sending)  
   - Jinja2 (for HTML template rendering)  
   - MongoDB connection, custom exceptions, configuration loader, logging

2. **Set Logger**  
   - `logger ← SingletonLogger.get_logger('appLogger')`

3. **Load Environment Configurations**  
   - `config ← get_config()`  
   - `SMTP_HOST ← ENV or default 'localhost'`  
   - `SMTP_PORT ← ENV or default 587`  
   - `SMTP_USER ← ENV or ''`  
   - `SMTP_PASSWORD ← ENV or ''`  
   - `FROM_EMAIL ← SMTP_USER or 'no-reply@example.com'`

4. **Set Template & Attachment Paths**  
   - `template_dir ← "current_folder/html_templates"`  
   - `attachments_dir ← "../../../Attachments"`  
   - Create `attachments_dir` if not exists

5. **Set Jinja2 Environment**  
   - `jinja_env ← jinja2.Environment(loader=FileSystemLoader(template_dir))`

6. **Define Template Name → File Mapping**  
   - e.g. `"Template-Table" → "table_template"`

---

## Function: send_emails_process(request, background_tasks=None)

**Purpose:** Decide whether to send email in the background or immediately.

1. If `background_tasks` is provided:  
   - Add `send_email_function(request)` as a background task  
   - Return: `{status: "processing", message: "Email queued for sending"}`  

2. Else:  
   - Call `send_email_function(request)` directly  
   - Return: `{status: "success", message: "Email sent successfully"}`

---

## Function: send_email_function(request)

**Purpose:** Build, render, and send the email.

1. Check Request Type  
   - If `request.Type.lower() ≠ 'email'` → log & return

2. Get HTML Template File  
   - `template_file ← template_mapping[request.TemplateName]`  
   - If not found → raise error

3. Render HTML Body  
   - Load template from Jinja environment  
   - Create `render_context` from `request.EmailBody`  
   - Add `"Date"` and `"Subject"` to context  

4. If Template Requires Table (`Template-Table` or `Template-Mediation`):  
   - Extract `table_data` from `request.EmailBody.Table_Filter_infor.data`  
   - `DYNAMIC_TABLE ← build_html_table([table_data])`  
   - Add `DYNAMIC_TABLE` to context  

5. Generate HTML  
   - `html_body ← template.render(**render_context)`

---

## Prepare Email Message

1. Create MIME Multipart  
   - Set `From` header: `"Sender_Name <FROM_EMAIL>"` or `FROM_EMAIL`  
   - Set `To` from `request.SendersMail`  
   - Set `Cc` from `request.CarbonCopyTo`  
   - Set `Subject` from `request.Subject`  
   - Attach HTML body

2. Add Attachments (if any)  
   - For each file in `request.Attachments`:  
     - Check if exists in `attachments_dir`  
     - If exists → open & attach as `MIMEApplication`  
     - If missing → log warning

---

## Send Email via SMTP

1. Open SMTP Connection to `SMTP_HOST:SMTP_PORT`  
2. Start TLS  
3. If Credentials Provided → `server.login(SMTP_USER, SMTP_PASSWORD)`  
4. Send Message  
5. Log Success or set `status = 'failed'` on error

---

## Log Email in Database

1. Connect to MongoDB (`MongoDBConnectionSingleton`)  
2. Insert log record into `email_logs` collection with:  
   - `type, to, cc, subject, template, body, attachments, date, sent_at, status`  
3. Handle database connection or insertion errors

---

## Function: build_html_table(data)

**Purpose:** Convert list of dictionaries into HTML table string.

1. If `data` is empty → return "No data available"
2. Get `headers` from first dict’s keys
3. Build HTML `<table>` with:  
   - Header row (`<th>`) from keys  
   - Data rows (`<td>`) from values  
     - If value is list of length 2 → format `"item1 - item2"`
4. Return full HTML table string

import os
import sqlite3
from flask import (
    Flask,
    flash,
    redirect,
    render_template_string,
    request,
    url_for,
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "dks_hub_secret_key"

FILES_DIR = "vendor_files"
if not os.path.exists(FILES_DIR):
  os.makedirs(FILES_DIR)

app.config["FILES_DIR"] = FILES_DIR


def get_db():
  conn = sqlite3.connect("dks_hub.db")
  conn.row_factory = sqlite3.Row
  return conn


# Автоматическая проверка структуры БД
def init_db():
  conn = get_db()
  conn.execute("""
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            country TEXT,
            contact_person TEXT,
            email TEXT,
            phone TEXT,
            file_path TEXT,
            notes TEXT
        )
    """)
  try:
    conn.execute("ALTER TABLE vendors ADD COLUMN products_activity TEXT")
  except sqlite3.OperationalError:
    pass
  conn.commit()
  conn.close()


init_db()

# Текстовые словари для двуязычного интерфейса
TRANSLATIONS = {
    "ru": {
        "title": "ATYRAU TECHNICAL SOURCING",
        "subtitle": "VENDOR AUDIT & LOGISTICS | DKS HUB WEB PORTAL",
        "add_vendor": "Добавить нового вендора",
        "company_name": "Название компании *",
        "category": "Направление",
        "products": "📦 Поставляемая продукция / Деятельность",
        "products_placeholder": (
            "Например: Трубы ПНД, запорная арматура, фланцы, насосное"
            " оборудование..."
        ),
        "country": "Страна / Адрес",
        "contact_person": "Контактное лицо",
        "email": "Email",
        "phone": "Телефон",
        "file_label": "Файл компании (анкета, КП)",
        "notes": "Примечания / Сайт",
        "save_btn": "Сохранить вендора",
        "db_title": "База данных вендоров DKS Hub (Облако)",
        "total_records": "Всего записей:",
        "th_id": "ID",
        "th_company": "Компания & Продукция",
        "th_category": "Направление",
        "th_country": "Страна / Адрес",
        "th_contacts": "Контакты",
        "th_file": "Файл",
        "th_actions": "Действия",
        "no_file": "Нет файла",
        "download": "Файл",
        "delete_confirm": "Удалить этого вендора?",
        "cats": [
            "1. Industrial (Промышленное)",
            "2. Commercial & Infrastructure (Бытовое/Строй)",
            "3. Agro & Food Trade (Пищевое)",
        ],
    },
    "en": {
        "title": "ATYRAU TECHNICAL SOURCING",
        "subtitle": "VENDOR AUDIT & LOGISTICS | DKS HUB WEB PORTAL",
        "add_vendor": "Add New Vendor",
        "company_name": "Company Name *",
        "category": "Category / Industry",
        "products": "📦 Supplied Products / Scope of Activity",
        "products_placeholder": (
            "E.g.: HDPE pipes, valves, flanges, pumping equipment..."
        ),
        "country": "Country / Address",
        "contact_person": "Contact Person",
        "email": "Email",
        "phone": "Phone",
        "file_label": "Company File (Questionnaire, Quotation)",
        "notes": "Notes / Website",
        "save_btn": "Save Vendor",
        "db_title": "DKS Hub Vendor Database (Cloud)",
        "total_records": "Total records:",
        "th_id": "ID",
        "th_company": "Company & Products",
        "th_category": "Category",
        "th_country": "Country / Address",
        "th_contacts": "Contacts",
        "th_file": "File",
        "th_actions": "Actions",
        "no_file": "No file",
        "download": "File",
        "delete_confirm": "Delete this vendor?",
        "cats": [
            "1. Industrial",
            "2. Commercial & Infrastructure",
            "3. Agro & Food Trade",
        ],
    },
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DKS | Atyrau Technical Sourcing & Vendor Audit</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-light">
    <div class="container my-4">
        <!-- Шапка с логотипом и переключателем языка -->
        <div class="p-4 mb-4 bg-white rounded shadow-sm d-flex justify-content-between align-items-center flex-wrap">
            <div class="d-flex align-items-center">
                <div class="me-4">
                    <img src="/logo" alt="Logo" style="height: 120px; width: 120px; object-fit: contain;" class="rounded">
                </div>
                <div>
                    <h2 class="text-primary fw-bold mb-0">{{ t.title }}</h2>
                    <p class="text-muted mb-0">{{ t.subtitle }}</p>
                </div>
            </div>
            <div class="mt-3 mt-md-0">
                <div class="btn-group" role="group">
                    <a href="/?lang=ru" class="btn btn-sm {% if lang == 'ru' %}btn-primary{% else %}btn-outline-primary{% endif %}">🇷🇺 Русский</a>
                    <a href="/?lang=en" class="btn btn-sm {% if lang == 'en' %}btn-primary{% else %}btn-outline-primary{% endif %}">🇬🇧 English</a>
                </div>
            </div>
        </div>

        <!-- Форма добавления вендора -->
        <div class="card shadow-sm mb-4">
            <div class="card-header bg-primary text-white fw-bold">
                <i class="fa-solid fa-plus-circle me-2"></i> {{ t.add_vendor }}
            </div>
            <div class="card-body">
                <form method="POST" action="/add?lang={{ lang }}" enctype="multipart/form-data">
                    <div class="row g-3">
                        <div class="col-md-6">
                            <label class="form-label fw-bold">{{ t.company_name }}</label>
                            <input type="text" class="form-control" name="name" required>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label fw-bold">{{ t.category }}</label>
                            <select class="form-select" name="category">
                                {% for cat in t.cats %}
                                <option value="{{ cat }}">{{ cat }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-12">
                            <label class="form-label fw-bold text-dark">{{ t.products }}</label>
                            <textarea class="form-control" name="products_activity" rows="2" placeholder="{{ t.products_placeholder }}"></textarea>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">{{ t.country }}</label>
                            <input type="text" class="form-control" name="country">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">{{ t.contact_person }}</label>
                            <input type="text" class="form-control" name="contact_person">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">{{ t.email }}</label>
                            <input type="email" class="form-control" name="email">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">{{ t.phone }}</label>
                            <input type="text" class="form-control" name="phone">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">{{ t.file_label }}</label>
                            <input type="file" class="form-control" name="file">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">{{ t.notes }}</label>
                            <input type="text" class="form-control" name="notes">
                        </div>
                        <div class="col-12 text-end">
                            <button type="submit" class="btn btn-success px-4"><i class="fa-solid fa-save me-1"></i> {{ t.save_btn }}</button>
                        </div>
                    </div>
                </form>
            </div>
        </div>

        <!-- Таблица базы данных -->
        <div class="card shadow-sm">
            <div class="card-header bg-secondary text-white fw-bold d-flex justify-content-between align-items-center">
                <span><i class="fa-solid fa-database me-2"></i> {{ t.db_title }}</span>
                <span class="badge bg-light text-dark">{{ t.total_records }} {{ vendors|length }}</span>
            </div>
            <div class="card-body table-responsive">
                <table class="table table-striped table-hover align-middle">
                    <thead class="table-dark">
                        <tr>
                            <th>{{ t.th_id }}</th>
                            <th>{{ t.th_company }}</th>
                            <th>{{ t.th_category }}</th>
                            <th>{{ t.th_country }}</th>
                            <th>{{ t.th_contacts }}</th>
                            <th>{{ t.th_file }}</th>
                            <th>{{ t.th_actions }}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for v in vendors %}
                        <tr>
                            <td>{{ v.id }}</td>
                            <td>
                                <strong class="text-primary">{{ v.name }}</strong>
                                {% if v.products_activity %}
                                <div class="small text-dark mt-1 bg-white p-1 rounded border border-info"><strong>Products:</strong> {{ v.products_activity }}</div>
                                {% endif %}
                            </td>
                            <td>{{ v.category }}</td>
                            <td>{{ v.country }}</td>
                            <td>{{ v.contact_person }}<br><small class="text-muted">{{ v.email }} | {{ v.phone }}</small></td>
                            <td>
                                {% if v.file_path %}
                                <a href="/download/{{ v.id }}" class="btn btn-sm btn-outline-primary" target="_blank"><i class="fa-solid fa-file-arrow-down"></i> {{ t.download }}</a>
                                {% else %}
                                <span class="text-muted">{{ t.no_file }}</span>
                                {% endif %}
                            </td>
                            <td>
                                <a href="/delete/{{ v.id }}?lang={{ lang }}" class="btn btn-sm btn-danger" onclick="return confirm('{{ t.delete_confirm }}')"><i class="fa-solid fa-trash"></i></a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""


@app.route("/")
def index():
  lang = request.args.get("lang", "ru")
  if lang not in TRANSLATIONS:
    lang = "ru"
  t = TRANSLATIONS[lang]

  conn = get_db()
  vendors = conn.execute(
      "SELECT * FROM vendors ORDER BY id DESC"
  ).fetchall()
  conn.close()
  return render_template_string(HTML_TEMPLATE, vendors=vendors, t=t, lang=lang)


@app.route("/logo")
def logo():
  if os.path.exists("logo_dks.jpg"):
    from flask import send_file

    return send_file("logo_dks.jpg", mimetype="image/jpeg")
  return "Логотип не найден", 404


@app.route("/add", methods=["POST"])
def add_vendor():
  lang = request.args.get("lang", "ru")
  name = request.form.get("name")
  category = request.form.get("category")
  products_activity = request.form.get("products_activity")
  country = request.form.get("country")
  contact = request.form.get("contact_person")
  email = request.form.get("email")
  phone = request.form.get("phone")
  notes = request.form.get("notes")

  file_path = ""
  file = request.files.get("file")
  if file and file.filename:
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["FILES_DIR"], filename)
    file.save(file_path)

  conn = get_db()
  conn.execute(
      """
        INSERT INTO vendors (name, category, products_activity, country, contact_person, email, phone, file_path, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
      (
          name,
          category,
          products_activity,
          country,
          contact,
          email,
          phone,
          file_path,
          notes,
      ),
  )
  conn.commit()
  conn.close()
  return redirect(url_for("index", lang=lang))


@app.route("/delete/<int:id>")
def delete_vendor(id):
  lang = request.args.get("lang", "ru")
  conn = get_db()
  conn.execute("DELETE FROM vendors WHERE id = ?", (id,))
  conn.commit()
  conn.close()
  return redirect(url_for("index", lang=lang))


@app.route("/download/<int:id>")
def download_file(id):
  conn = get_db()
  vendor = conn.execute(
      "SELECT file_path FROM vendors WHERE id = ?", (id,)
  ).fetchone()
  conn.close()
  if vendor and vendor["file_path"] and os.path.exists(vendor["file_path"]):
    from flask import send_file

    return send_file(vendor["file_path"], as_attachment=True)
  return "Файл не найден", 404


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)

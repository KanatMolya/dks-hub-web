import os
import sqlite3
from flask import Flask, flash, redirect, render_template_string, request, url_for
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


# Автоматическая проверка и добавление колонки товаров/деятельности, если её нет
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
    pass  # Колонка уже существует
  conn.commit()
  conn.close()


init_db()

# HTML-шаблон с увеличенным логотипом и полем продукции
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DKS | Atyrau Technical Sourcing & Vendor Audit</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-light">
    <div class="container my-4">
        <!-- Шапка с крупным логотипом -->
        <div class="p-4 mb-4 bg-white rounded shadow-sm d-flex align-items-center">
            <div class="me-4">
                <img src="/logo" alt="Logo" style="height: 120px; width: 120px; object-fit: contain;" class="rounded">
            </div>
            <div>
                <h2 class="text-primary fw-bold mb-0">ATYRAU TECHNICAL SOURCING</h2>
                <p class="text-muted mb-0">VENDOR AUDIT & LOGISTICS | DKS HUB WEB PORTAL</p>
            </div>
        </div>

        <!-- Форма добавления вендора -->
        <div class="card shadow-sm mb-4">
            <div class="card-header bg-primary text-white fw-bold">
                <i class="fa-solid fa-plus-circle me-2"></i> Добавить нового вендора
            </div>
            <div class="card-body">
                <form method="POST" action="/add" enctype="multipart/form-data">
                    <div class="row g-3">
                        <div class="col-md-6">
                            <label class="form-label fw-bold">Название компании *</label>
                            <input type="text" class="form-control" name="name" required>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label fw-bold">Направление</label>
                            <select class="form-select" name="category">
                                <option>1. Industrial (Промышленное)</option>
                                <option>2. Commercial & Infrastructure (Бытовое/Строй)</option>
                                <option>3. Agro & Food Trade (Пищевое)</option>
                            </select>
                        </div>
                        <div class="col-12">
                            <label class="form-label fw-bold text-dark">📦 Поставляемая продукция / Деятельность</label>
                            <textarea class="form-control" name="products_activity" rows="2" placeholder="Например: Трубы ПНД, запорная арматура, фланцы, насосное оборудование..."></textarea>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Страна / Адрес</label>
                            <input type="text" class="form-control" name="country">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Контактное лицо</label>
                            <input type="text" class="form-control" name="contact_person">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Email</label>
                            <input type="email" class="form-control" name="email">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Телефон</label>
                            <input type="text" class="form-control" name="phone">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Файл компании (анкета, КП)</label>
                            <input type="file" class="form-control" name="file">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Примечания / Сайт</label>
                            <input type="text" class="form-control" name="notes">
                        </div>
                        <div class="col-12 text-end">
                            <button type="submit" class="btn btn-success px-4"><i class="fa-solid fa-save me-1"></i> Сохранить вендора</button>
                        </div>
                    </div>
                </form>
            </div>
        </div>

        <!-- Таблица базы данных -->
        <div class="card shadow-sm">
            <div class="card-header bg-secondary text-white fw-bold d-flex justify-content-between align-items-center">
                <span><i class="fa-solid fa-database me-2"></i> База данных вендоров DKS Hub (Облако)</span>
                <span class="badge bg-light text-dark">Всего записей: {{ vendors|length }}</span>
            </div>
            <div class="card-body table-responsive">
                <table class="table table-striped table-hover align-middle">
                    <thead class="table-dark">
                        <tr>
                            <th>ID</th>
                            <th>Компания & Продукция</th>
                            <th>Направление</th>
                            <th>Страна / Адрес</th>
                            <th>Контакты</th>
                            <th>Файл</th>
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for v in vendors %}
                        <tr>
                            <td>{{ v.id }}</td>
                            <td>
                                <strong class="text-primary">{{ v.name }}</strong>
                                {% if v.products_activity %}
                                <div class="small text-dark mt-1 bg-white p-1 rounded border border-info"><strong>Товары/Деятельность:</strong> {{ v.products_activity }}</div>
                                {% endif %}
                            </td>
                            <td>{{ v.category }}</td>
                            <td>{{ v.country }}</td>
                            <td>{{ v.contact_person }}<br><small class="text-muted">{{ v.email }} | {{ v.phone }}</small></td>
                            <td>
                                {% if v.file_path %}
                                <a href="/download/{{ v.id }}" class="btn btn-sm btn-outline-primary" target="_blank"><i class="fa-solid fa-file-arrow-down"></i> Файл</a>
                                {% else %}
                                <span class="text-muted">Нет файла</span>
                                {% endif %}
                            </td>
                            <td>
                                <a href="/delete/{{ v.id }}" class="btn btn-sm btn-danger" onclick="return confirm('Удалить этого вендора?')"><i class="fa-solid fa-trash"></i></a>
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
  conn = get_db()
  vendors = conn.execute(
      "SELECT * FROM vendors ORDER BY id DESC"
  ).fetchall()
  conn.close()
  return render_template_string(HTML_TEMPLATE, vendors=vendors)


@app.route("/logo")
def logo():
  if os.path.exists("logo_dks.jpg"):
    from flask import send_file

    return send_file("logo_dks.jpg", mimetype="image/jpeg")
  return "Логотип не найден", 404


@app.route("/add", methods=["POST"])
def add_vendor():
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
  return redirect(url_for("index"))


@app.route("/delete/<int:id>")
def delete_vendor(id):
  conn = get_db()
  conn.execute("DELETE FROM vendors WHERE id = ?", (id,))
  conn.commit()
  conn.close()
  return redirect(url_for("index"))


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

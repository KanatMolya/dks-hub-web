import os
import sqlite3
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Проверка и автоустановка Pillow и openpyxl
try:
  from PIL import Image, ImageTk
except ImportError:
  subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
  from PIL import Image, ImageTk

try:
  import openpyxl
except ImportError:
  subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
  import openpyxl


class DKSHubApp:

  def __init__(self, root):
    self.root = root
    self.root.title("DKS | Atyrau Technical Sourcing & Vendor Audit")
    self.root.geometry("1280x800")

    # Настройка стиля высоты строк таблицы (чтобы текст не обрезался снизу)
    self.style = ttk.Style()
    self.style.theme_use("clam")
    self.style.configure("Treeview", rowheight=32, font=("Helvetica", 9))
    self.style.configure("Treeview.Heading", font=("Helvetica", 9, "bold"))

    # Папка для прикрепленных файлов
    self.files_dir = "vendor_files"
    if not os.path.exists(self.files_dir):
      os.makedirs(self.files_dir)

    # Инициализация БД
    self.init_db()

    # Закрепление и установка иконки/логотипа
    self.load_app_logo()

    # Создание интерфейса
    self.create_widgets()
    self.load_vendors()

  def load_app_logo(self):
    """Закрепляет утвержденный логотип DKS Hub в заголовке и окне приложения с пропорциональным масштабированием"""
    logo_candidates = [
        "logo_dks.jpg",
        "logo.jpg",
        "watermarked_img_4776893141062815066.jpg",
        "watermarked_img_5801491470821782171.jpg",
    ]
    self.logo_path = None
    for cand in logo_candidates:
      if os.path.exists(cand):
        self.logo_path = cand
        break

    if self.logo_path:
      try:
        img = Image.open(self.logo_path)
        icon_img = ImageTk.PhotoImage(img.resize((32, 32), Image.LANCZOS))
        self.root.iconphoto(True, icon_img)
        self.icon_img_ref = icon_img

        # Аккуратное сохранение пропорций без сплющивания самолетом и поездом
        img.thumbnail((85, 85), Image.LANCZOS)
        self.header_logo_ref = ImageTk.PhotoImage(img)
      except Exception as e:
        print(f"Ошибка при загрузке логотипа: {e}")
        self.header_logo_ref = None
    else:
      self.header_logo_ref = None

  def init_db(self):
    self.conn = sqlite3.connect("dks_hub.db")
    self.cursor = self.conn.cursor()
    self.cursor.execute("""
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
    self.conn.commit()

  def create_right_click_menu(self, entry_widget):
    """Контекстное меню ПКМ (Вырезать, Копировать, Вставить)"""
    menu = tk.Menu(entry_widget, tearoff=0)
    menu.add_command(
        label="Вырезать",
        command=lambda: entry_widget.event_generate("<<Cut>>"),
    )
    menu.add_command(
        label="Копировать",
        command=lambda: entry_widget.event_generate("<<Copy>>"),
    )
    menu.add_command(
        label="Вставить",
        command=lambda: entry_widget.event_generate("<<Paste>>"),
    )
    menu.add_separator()
    menu.add_command(
        label="Выделить всё",
        command=lambda: entry_widget.select_range(0, "end"),
    )

    def show_menu(event):
      menu.tk_popup(event.x_root, event.y_root)

    entry_widget.bind("<Button-3>", show_menu)

  def create_widgets(self):
    # Шапка программы с логотипом
    header_frame = ttk.Frame(self.root)
    header_frame.pack(fill="x", padx=10, pady=(5, 0))

    if self.header_logo_ref:
      logo_label = ttk.Label(header_frame, image=self.header_logo_ref)
      logo_label.pack(side="left", padx=(0, 10))

    title_frame = ttk.Frame(header_frame)
    title_frame.pack(side="left", fill="y")

    title_label = ttk.Label(
        title_frame,
        text="ATYRAU TECHNICAL SOURCING",
        font=("Helvetica", 16, "bold"),
        foreground="#003399",
    )
    title_label.pack(anchor="w")

    subtitle_label = ttk.Label(
        title_frame,
        text="VENDOR AUDIT & LOGISTICS | DKS HUB VENDORS",
        font=("Helvetica", 9, "bold"),
        foreground="#444444",
    )
    subtitle_label.pack(anchor="w")

    # Форма ввода
    input_frame = ttk.LabelFrame(
        self.root, text=" Добавить / Управлять вендором "
    )
    input_frame.pack(fill="x", padx=10, pady=10)

    ttk.Label(input_frame, text="Название компании:").grid(
        row=0, column=0, sticky="w", padx=5, pady=5
    )
    self.entry_name = ttk.Entry(input_frame, width=35)
    self.entry_name.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    self.create_right_click_menu(self.entry_name)

    ttk.Label(input_frame, text="Направление:").grid(
        row=0, column=2, sticky="w", padx=5, pady=5
    )
    self.combo_category = ttk.Combobox(
        input_frame,
        values=[
            "1. Industrial (Промышленное)",
            "2. Commercial & Infrastructure (Бытовое/Строй)",
            "3. Agro & Food Trade (Пищевое)",
        ],
        width=35,
        state="readonly",
    )
    self.combo_category.grid(row=0, column=3, padx=5, pady=5, sticky="w")
    self.combo_category.current(0)

    ttk.Label(input_frame, text="Страна / Адрес:").grid(
        row=1, column=0, sticky="w", padx=5, pady=5
    )
    self.entry_country = ttk.Entry(input_frame, width=35)
    self.entry_country.grid(row=1, column=1, padx=5, pady=5, sticky="w")
    self.create_right_click_menu(self.entry_country)

    ttk.Label(input_frame, text="Контактное лицо:").grid(
        row=1, column=2, sticky="w", padx=5, pady=5
    )
    self.entry_contact = ttk.Entry(input_frame, width=35)
    self.entry_contact.grid(row=1, column=3, padx=5, pady=5, sticky="w")
    self.create_right_click_menu(self.entry_contact)

    ttk.Label(input_frame, text="Email:").grid(
        row=2, column=0, sticky="w", padx=5, pady=5
    )
    self.entry_email = ttk.Entry(input_frame, width=35)
    self.entry_email.grid(row=2, column=1, padx=5, pady=5, sticky="w")
    self.create_right_click_menu(self.entry_email)

    ttk.Label(input_frame, text="Телефон:").grid(
        row=2, column=2, sticky="w", padx=5, pady=5
    )
    self.entry_phone = ttk.Entry(input_frame, width=35)
    self.entry_phone.grid(row=2, column=3, padx=5, pady=5, sticky="w")
    self.create_right_click_menu(self.entry_phone)

    ttk.Label(input_frame, text="Файл компании:").grid(
        row=3, column=0, sticky="w", padx=5, pady=5
    )
    file_frame = ttk.Frame(input_frame)
    file_frame.grid(
        row=3, column=1, columnspan=3, sticky="w", padx=5, pady=5
    )

    self.entry_file = ttk.Entry(file_frame, width=65)
    self.entry_file.pack(side="left", padx=(0, 5))
    self.create_right_click_menu(self.entry_file)
    ttk.Button(
        file_frame, text="📂 Обзор...", command=self.browse_file
    ).pack(side="left")

    ttk.Label(input_frame, text="Примечания:").grid(
        row=4, column=0, sticky="w", padx=5, pady=5
    )
    self.entry_notes = ttk.Entry(input_frame, width=80)
    self.entry_notes.grid(
        row=4, column=1, columnspan=3, sticky="w", padx=5, pady=5
    )
    self.create_right_click_menu(self.entry_notes)

    # Кнопки управления
    btn_frame = ttk.Frame(self.root)
    btn_frame.pack(fill="x", padx=10, pady=5)

    ttk.Button(
        btn_frame, text="➕ Добавить вендора", command=self.add_vendor
    ).pack(side="left", padx=5)
    ttk.Button(
        btn_frame, text="🔍 Просмотр (Карточка)", command=self.show_vendor_details
    ).pack(side="left", padx=5)
    ttk.Button(
        btn_frame, text="🗑 Удалить выбранное", command=self.delete_vendor
    ).pack(side="left", padx=5)
    ttk.Button(
        btn_frame, text="📎 Открыть файл вендора", command=self.open_vendor_file
    ).pack(side="left", padx=5)
    ttk.Button(
        btn_frame, text="🔄 Очистить форму", command=self.clear_entries
    ).pack(side="left", padx=5)
    ttk.Button(
        btn_frame, text="📊 Экспорт в Excel", command=self.export_to_excel
    ).pack(side="right", padx=5)

    # Таблица с увеличенными строками
    table_frame = ttk.LabelFrame(
        self.root,
        text=(
            " База данных вендоров DKS Hub (Офлайн) — Двойной клик по строке для"
            " подробного просмотра "
        ),
    )
    table_frame.pack(fill="both", expand=True, padx=10, pady=10)

    columns = (
        "ID",
        "Компания",
        "Направление",
        "Страна / Адрес",
        "Контактное лицо",
        "Email",
        "Телефон",
        "Файл",
        "Примечания",
    )
    self.tree = ttk.Treeview(
        table_frame, columns=columns, show="headings", selectmode="browse"
    )

    col_widths = {
        "ID": 40,
        "Компания": 250,
        "Направление": 220,
        "Страна / Адрес": 300,
        "Контактное лицо": 180,
        "Email": 180,
        "Телефон": 160,
        "Файл": 200,
        "Примечания": 250,
    }

    for col in columns:
      self.tree.heading(col, text=col)
      width = col_widths.get(col, 150)
      anchor = "center" if col == "ID" else "w"
      self.tree.column(col, width=width, minwidth=100, anchor=anchor)

    v_scrollbar = ttk.Scrollbar(
        table_frame, orient="vertical", command=self.tree.yview
    )
    h_scrollbar = ttk.Scrollbar(
        table_frame, orient="horizontal", command=self.tree.xview
    )
    self.tree.configure(
        yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
    )

    self.tree.grid(row=0, column=0, sticky="nsew")
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    h_scrollbar.grid(row=1, column=0, sticky="ew")

    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    self.tree.bind("<Double-1>", lambda event: self.show_vendor_details())

  def browse_file(self):
    filename = filedialog.askopenfilename(
        title="Выберите файл компании (анкета, опросный лист, КП)"
    )
    if filename:
      self.entry_file.delete(0, "end")
      self.entry_file.insert(0, filename)

  def clean_for_table(self, text):
    """Преобразует многострочный текст в чистую одну строку для красивого отображения в таблице"""
    if not text:
      return ""
    cleaned = str(text).replace("\r\n", " | ").replace("\n", " | ").strip()
    return cleaned

  def load_vendors(self):
    for row in self.tree.get_children():
      self.tree.delete(row)
    self.cursor.execute(
        "SELECT id, name, category, country, contact_person, email, phone,"
        " file_path, notes FROM vendors"
    )
    for row in self.cursor.fetchall():
      formatted_row = [
          row[0],
          self.clean_for_table(row[1]),
          self.clean_for_table(row[2]),
          self.clean_for_table(row[3]),
          self.clean_for_table(row[4]),
          self.clean_for_table(row[5]),
          self.clean_for_table(row[6]),
          os.path.basename(row[7]) if row[7] else "Нет файла",
          self.clean_for_table(row[8]),
      ]
      self.tree.insert("", "end", values=formatted_row, tags=(str(row[0]),))

  def show_vendor_details(self):
    selected_item = self.tree.selection()
    if not selected_item:
      messagebox.showwarning(
          "Внимание", "Выберите вендора в таблице для просмотра карточки."
      )
      return

    item_data = self.tree.item(selected_item)
    vendor_id = item_data["tags"][0]

    self.cursor.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,))
    row = self.cursor.fetchone()
    if not row:
      return

    detail_win = tk.Toplevel(self.root)
    detail_win.title(f"Карточка вендора: {row[1]}")
    detail_win.geometry("700x580")

    ttk.Label(
        detail_win,
        text=row[1],
        font=("Helvetica", 14, "bold"),
        foreground="#003399",
    ).pack(anchor="w", padx=15, pady=(15, 5))
    ttk.Label(
        detail_win,
        text=f"Категория: {row[2]}",
        font=("Helvetica", 10, "italic"),
    ).pack(anchor="w", padx=15, pady=(0, 10))

    fields_frame = ttk.Frame(detail_win)
    fields_frame.pack(fill="both", expand=True, padx=15, pady=5)

    info_list = [
        ("ID в базе:", str(row[0])),
        ("Страна / Подробный адрес:", str(row[3] or "—")),
        ("Контактное лицо:", str(row[4] or "—")),
        ("Email:", str(row[5] or "—")),
        ("Телефон:", str(row[6] or "—")),
        ("Прикрепленный файл:", os.path.basename(row[7]) if row[7] else "—"),
        ("Примечания / Сайт:", str(row[8] or "—")),
    ]

    for i, (label_text, val_text) in enumerate(info_list):
      ttk.Label(
          fields_frame, text=label_text, font=("Helvetica", 9, "bold")
      ).grid(row=i, column=0, sticky="nw", pady=6)

      txt_box = tk.Text(fields_frame, height=3, width=52, wrap="word")
      txt_box.insert("1.0", val_text)
      txt_box.configure(state="normal")
      self.create_right_click_menu(txt_box)
      txt_box.grid(row=i, column=1, sticky="w", padx=10, pady=4)

    btn_close = ttk.Button(
        detail_win, text="Закрыть", command=detail_win.destroy
    )
    btn_close.pack(pady=10)

  def add_vendor(self):
    name = self.entry_name.get().strip()
    category = self.combo_category.get()
    country = self.entry_country.get().strip()
    contact = self.entry_contact.get().strip()
    email = self.entry_email.get().strip()
    phone = self.entry_phone.get().strip()
    src_file = self.entry_file.get().strip()
    notes = self.entry_notes.get().strip()

    if not name:
      messagebox.showerror("Ошибка", "Введите название компании-вендора!")
      return

    saved_file_path = ""
    if src_file and os.path.exists(src_file):
      base_name = os.path.basename(src_file)
      saved_file_path = os.path.join(self.files_dir, base_name)
      if not os.path.exists(saved_file_path):
        import shutil

        shutil.copy(src_file, saved_file_path)

    self.cursor.execute(
        """
            INSERT INTO vendors (name, category, country, contact_person, email, phone, file_path, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            category,
            country,
            contact,
            email,
            phone,
            saved_file_path,
            notes,
        ),
    )
    self.conn.commit()
    self.load_vendors()
    self.clear_entries()
    messagebox.showinfo(
        "Успешно", "Вендор и документы успешно добавлены в базу!"
    )

  def delete_vendor(self):
    selected_item = self.tree.selection()
    if not selected_item:
      messagebox.showwarning(
          "Внимание", "Выберите строку в таблице для удаления."
      )
      return

    item_data = self.tree.item(selected_item)
    vendor_id = item_data["tags"][0]

    if messagebox.askyesno(
        "Подтверждение",
        "Вы уверены, что хотите удалить этого вендора из базы?",
    ):
      self.cursor.execute("DELETE FROM vendors WHERE id = ?", (vendor_id,))
      self.conn.commit()
      self.load_vendors()
      self.clear_entries()
      messagebox.showinfo("Успешно", "Запись удалена.")

  def open_vendor_file(self):
    selected_item = self.tree.selection()
    if not selected_item:
      messagebox.showwarning(
          "Внимание", "Выберите вендора в таблице, чтобы открыть его файл."
      )
      return

    item_data = self.tree.item(selected_item)
    vendor_id = item_data["tags"][0]

    self.cursor.execute(
        "SELECT file_path FROM vendors WHERE id = ?", (vendor_id,)
    )
    res = self.cursor.fetchone()
    if res and res[0] and os.path.exists(res[0]):
      file_path = os.path.abspath(res[0])
      if sys.platform == "win32":
        os.startfile(file_path)
      elif sys.platform == "darwin":
        subprocess.call(["open", file_path])
      else:
        subprocess.call(["xdg-open", file_path])
    else:
      messagebox.showerror(
          "Ошибка",
          "У этого вендора не прикреплен файл или файл был удален с диска.",
      )

  def export_to_excel(self):
    try:
      wb = openpyxl.Workbook()
      ws = wb.active
      ws.title = "DKS Hub Vendors"

      headers = [
          "ID",
          "Компания",
          "Направление",
          "Страна / Адрес",
          "Контактное лицо",
          "Email",
          "Телефон",
          "Путь к файлу",
          "Примечания",
      ]
      ws.append(headers)

      self.cursor.execute("SELECT * FROM vendors")
      for row in self.cursor.fetchall():
        ws.append(row)

      export_filename = "DKS_Hub_Vendors_Export.xlsx"
      wb.save(export_filename)
      messagebox.showinfo(
          "Успешно",
          f"База данных успешно выгружена в файл:\n{export_filename}",
      )
    except Exception as e:
      messagebox.showerror("Ошибка", f"Не удалось выгрузить в Excel:\n{e}")

  def clear_entries(self):
    self.entry_name.delete(0, "end")
    self.entry_country.delete(0, "end")
    self.entry_contact.delete(0, "end")
    self.entry_email.delete(0, "end")
    self.entry_phone.delete(0, "end")
    self.entry_file.delete(0, "end")
    self.entry_notes.delete(0, "end")
    self.combo_category.current(0)


if __name__ == "__main__":
  root = tk.Tk()
  app = DKSHubApp(root)
  root.mainloop()
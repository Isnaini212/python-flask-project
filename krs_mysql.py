from flask import Flask, render_template_string, request, redirect, url_for, flash, make_response
import pymysql
import csv
import io
from html import escape


app = Flask(__name__)
app.secret_key = "12345"


# ==========================================================
# KONEKSI DATABASE MYSQL
# ==========================================================
def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",        # isi password jika MySQL menggunakan password
        database="AKADEMIKDB",
        port=3306,
        cursorclass=pymysql.cursors.DictCursor
    )


# ==========================================================
# MEMBUAT TABEL JIKA BELUM ADA
# ==========================================================
def buat_tabel():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mahasiswa (
            nim INT PRIMARY KEY,
            nama VARCHAR(100) NOT NULL,
            jurusan VARCHAR(50) NOT NULL,
            fakultas VARCHAR(50) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matakuliah (
            kodemk VARCHAR(4) PRIMARY KEY,
            namamk VARCHAR(100) NOT NULL,
            sks INT NOT NULL,
            biaya DECIMAL(12,2) DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS krs (
            thn_ajar INT NOT NULL,
            semester VARCHAR(4) NOT NULL,
            nim INT NOT NULL,
            kodemk VARCHAR(4) NOT NULL,

            PRIMARY KEY (thn_ajar, semester, nim, kodemk),

            CONSTRAINT fk_krs_mahasiswa
                FOREIGN KEY (nim) REFERENCES mahasiswa(nim)
                ON UPDATE CASCADE ON DELETE RESTRICT,

            CONSTRAINT fk_krs_matakuliah
                FOREIGN KEY (kodemk) REFERENCES matakuliah(kodemk)
                ON UPDATE CASCADE ON DELETE RESTRICT
        )
    """)

    # Data contoh agar form KRS bisa langsung diuji.
    cursor.execute("SELECT COUNT(*) AS jumlah FROM mahasiswa")
    if cursor.fetchone()["jumlah"] == 0:
        cursor.executemany("""
            INSERT INTO mahasiswa (nim, nama, jurusan, fakultas)
            VALUES (%s, %s, %s, %s)
        """, (
            (231150001, "Andi Saputra", "Sistem Informasi", "Teknologi Informasi"),
            (231150002, "Siti Aminah", "Informatika", "Teknologi Informasi"),
            (231150003, "Budi Santoso", "Sistem Informasi", "Teknologi Informasi"),
        ))

    cursor.execute("SELECT COUNT(*) AS jumlah FROM matakuliah")
    if cursor.fetchone()["jumlah"] == 0:
        cursor.executemany("""
            INSERT INTO matakuliah (kodemk, namamk, sks, biaya)
            VALUES (%s, %s, %s, %s)
        """, (
            ("MK01", "Algoritma", 3, 450000),
            ("MK02", "Basis Data", 3, 450000),
            ("MK03", "Pemrograman Web", 3, 500000),
            ("MK04", "Analisis Sistem", 3, 450000),
        ))

    conn.commit()
    cursor.close()
    conn.close()


# ==========================================================
# FUNGSI BANTUAN DATA
# ==========================================================
def ambil_mahasiswa():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mahasiswa ORDER BY nim")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data


def ambil_matakuliah():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM matakuliah ORDER BY kodemk")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data


def label_semester(kode):
    daftar = {
        "1": "1 - Ganjil",
        "2": "2 - Genap",
        "3": "3 - Pendek"
    }
    return daftar.get(str(kode), str(kode))



def ambil_data_krs(keyword=""):
    conn = get_connection()
    cursor = conn.cursor()
    cari = "%" + keyword + "%"

    sql = """
        SELECT
            k.thn_ajar,
            k.semester,
            k.nim,
            m.nama,
            m.jurusan,
            m.fakultas,
            k.kodemk,
            mk.namamk,
            mk.sks,
            IFNULL(mk.biaya, 0) AS biaya
        FROM krs k
        JOIN mahasiswa m ON k.nim = m.nim
        JOIN matakuliah mk ON k.kodemk = mk.kodemk
    """

    if keyword:
        sql += """
            WHERE CAST(k.thn_ajar AS CHAR) LIKE %s
               OR k.semester LIKE %s
               OR CAST(k.nim AS CHAR) LIKE %s
               OR m.nama LIKE %s
               OR m.jurusan LIKE %s
               OR m.fakultas LIKE %s
               OR k.kodemk LIKE %s
               OR mk.namamk LIKE %s
        """
        parameter = (cari, cari, cari, cari, cari, cari, cari, cari)
    else:
        parameter = ()

    sql += " ORDER BY k.thn_ajar, k.semester, k.nim, k.kodemk"
    cursor.execute(sql, parameter)
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


KOLOM_CETAK = [
    "Tahun Ajar", "Semester", "NIM", "Nama", "Jurusan", "Fakultas",
    "Kode MK", "Nama MK", "SKS", "Biaya"
]


def buat_pdf_sederhana(rows):
    def escape_pdf_text(text):
        return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def format_baris(row):
        teks = " | ".join(str(value) for value in row)
        if len(teks) > 170:
            teks = teks[:167] + "..."
        return teks

    isi_baris = [
        "LAPORAN DATA KRS",
        "",
        format_baris(KOLOM_CETAK),
        "-" * 170
    ]

    for row in rows:
        isi_baris.append(format_baris([
            row["thn_ajar"], label_semester(row["semester"]), row["nim"], row["nama"],
            row["jurusan"], row["fakultas"], row["kodemk"], row["namamk"],
            row["sks"], row["biaya"]
        ]))

    total_sks = sum(int(row["sks"] or 0) for row in rows)
    total_biaya = sum(float(row["biaya"] or 0) for row in rows)
    isi_baris += ["-" * 170, f"Total SKS: {total_sks} | Total Biaya: {total_biaya:,.0f}"]

    baris_per_halaman = 34
    halaman = [isi_baris[i:i + baris_per_halaman] for i in range(0, len(isi_baris), baris_per_halaman)]

    objects = [
        (1, "<< /Type /Catalog /Pages 2 0 R >>"),
        (3, "<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>"),
    ]
    page_ids = []
    next_id = 4

    for lines in halaman:
        content_id = next_id
        page_id = next_id + 1
        next_id += 2
        page_ids.append(page_id)

        content = ["BT", "/F1 8 Tf", "40 555 Td", "12 TL"]
        for line in lines:
            content.append(f"({escape_pdf_text(line)}) Tj")
            content.append("T*")
        content.append("ET")
        stream = "\n".join(content).encode("latin-1", "replace")

        objects.append((content_id, f"<< /Length {len(stream)} >>\nstream\n{stream.decode('latin-1')}\nendstream"))
        objects.append((page_id, f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"))

    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects.insert(1, (2, f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"))
    objects.sort(key=lambda x: x[0])

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for object_id, obj in objects:
        offsets.append(len(pdf))
        pdf.extend(f"{object_id} 0 obj\n".encode("latin-1"))
        pdf.extend(obj.encode("latin-1", "replace"))
        pdf.extend(b"\nendobj\n")

    xref_pos = len(pdf)
    max_id = max(obj[0] for obj in objects)
    pdf.extend(f"xref\n0 {max_id + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    offset_map = {object_id: offset for (object_id, _), offset in zip(objects, offsets)}
    for object_id in range(1, max_id + 1):
        pdf.extend(f"{offset_map.get(object_id, 0):010d} 00000 n \n".encode("latin-1"))
    pdf.extend(f"trailer\n<< /Size {max_id + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode("latin-1"))
    return bytes(pdf)


# ==========================================================
# TEMPLATE HTML UTAMA
# ==========================================================
HTML_INDEX = """
<!DOCTYPE html>
<html>
<head>
    <title>Data KRS</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container mt-4 mb-5">
    <h3>Form Transaksi Kartu Rencana Studi - Flask dan MySQL</h3>
    <p class="text-muted">
        CRUD tabel KRS menggunakan primary key gabungan:
        thn_ajar, semester, nim, dan kodemk.
    </p>

    {% with messages = get_flashed_messages() %}
        {% if messages %}
            {% for msg in messages %}
                <div class="alert alert-info">{{ msg }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <div class="card mb-3">
        <div class="card-header bg-primary text-white">Input Data KRS</div>
        <div class="card-body">
            <form method="POST" action="{{ url_for('simpan') }}">
                <div class="row">
                    <div class="col-md-3 mb-2">
                        <label>Tahun Ajar</label>
                        <input type="number" name="thn_ajar" class="form-control" placeholder="2025" required>
                    </div>

                    <div class="col-md-3 mb-2">
                        <label>Semester</label>
                        <select name="semester" class="form-select" required>
                            <option value="">-- Pilih Semester --</option>
                            <option value="1">1 - Ganjil</option>
                            <option value="2">2 - Genap</option>
                            <option value="3">3 - Pendek</option>
                        </select>
                    </div>

                    <div class="col-md-6 mb-2">
                        <label>Mahasiswa</label>
                        <select name="nim" class="form-select" required>
                            <option value="">-- Pilih Mahasiswa --</option>
                            {% for m in mahasiswa %}
                            <option value="{{ m.nim }}">{{ m.nim }} - {{ m.nama }} - {{ m.jurusan }}</option>
                            {% endfor %}
                        </select>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-8 mb-2">
                        <label>Matakuliah</label>
                        <select name="kodemk" class="form-select" required>
                            <option value="">-- Pilih Matakuliah --</option>
                            {% for mk in matakuliah %}
                            <option value="{{ mk.kodemk }}">
                                {{ mk.kodemk }} - {{ mk.namamk }} - {{ mk.sks }} SKS - Rp {{ "{:,.0f}".format(mk.biaya or 0) }}
                            </option>
                            {% endfor %}
                        </select>
                    </div>

                    <div class="col-md-4 mb-2 d-flex align-items-end">
                        <button type="submit" class="btn btn-primary me-2">Simpan</button>
                        <a href="{{ url_for('index') }}" class="btn btn-secondary">Reset</a>
                    </div>
                </div>
            </form>
        </div>
    </div>

    <form method="GET" action="{{ url_for('index') }}" class="mb-3">
        <div class="input-group">
            <input type="text" name="keyword" class="form-control"
                   placeholder="Cari tahun ajar, semester, NIM, nama, kode MK, atau nama MK"
                   value="{{ keyword }}">
            <button class="btn btn-success" type="submit">Cari</button>
            <a href="{{ url_for('index') }}" class="btn btn-outline-secondary">Tampil Semua</a>
        </div>
    </form>

    <div class="mb-3">
        <a href="{{ url_for('cetak_pdf', keyword=keyword) }}" class="btn btn-danger btn-sm">Cetak PDF</a>
        <a href="{{ url_for('cetak_excel', keyword=keyword) }}" class="btn btn-success btn-sm">Cetak Excel</a>
        <a href="{{ url_for('cetak_csv', keyword=keyword) }}" class="btn btn-info btn-sm">Cetak CSV</a>
    </div>

    <div class="card mb-3">
        <div class="card-header bg-dark text-white">Daftar KRS</div>
        <div class="card-body table-responsive">
            <table class="table table-bordered table-striped align-middle">
                <thead class="table-dark">
                    <tr>
                        <th>No</th>
                        <th>Tahun Ajar</th>
                        <th>Semester</th>
                        <th>NIM</th>
                        <th>Nama</th>
                        <th>Jurusan</th>
                        <th>Kode MK</th>
                        <th>Nama MK</th>
                        <th>SKS</th>
                        <th>Biaya</th>
                        <th width="160">Aksi</th>
                    </tr>
                </thead>

                <tbody>
                    {% for row in data %}
                    <tr>
                        <td>{{ loop.index }}</td>
                        <td>{{ row.thn_ajar }}</td>
                        <td>{{ label_semester(row.semester) }}</td>
                        <td>{{ row.nim }}</td>
                        <td>{{ row.nama }}</td>
                        <td>{{ row.jurusan }}</td>
                        <td>{{ row.kodemk }}</td>
                        <td>{{ row.namamk }}</td>
                        <td>{{ row.sks }}</td>
                        <td>Rp {{ "{:,.0f}".format(row.biaya or 0) }}</td>
                        <td>
                            <a href="{{ url_for('edit',
                                thn_ajar=row.thn_ajar,
                                semester=row.semester,
                                nim=row.nim,
                                kodemk=row.kodemk) }}"
                                class="btn btn-warning btn-sm">Edit</a>

                            <a href="{{ url_for('hapus',
                                thn_ajar=row.thn_ajar,
                                semester=row.semester,
                                nim=row.nim,
                                kodemk=row.kodemk) }}"
                                class="btn btn-danger btn-sm"
                                onclick="return confirm('Yakin ingin menghapus data KRS ini?')">Hapus</a>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="11" class="text-center">Data KRS belum tersedia</td>
                    </tr>
                    {% endfor %}
                </tbody>

                <tfoot>
                    <tr class="table-secondary">
                        <th colspan="8" class="text-end">Total</th>
                        <th>{{ total_sks }}</th>
                        <th>Rp {{ "{:,.0f}".format(total_biaya) }}</th>
                        <th></th>
                    </tr>
                </tfoot>
            </table>
        </div>
    </div>
</div>
</body>
</html>
"""


# ==========================================================
# TEMPLATE HTML EDIT
# ==========================================================
HTML_EDIT = """
<!DOCTYPE html>
<html>
<head>
    <title>Edit KRS</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container mt-4">
    <h3>Edit Data KRS</h3>

    <div class="alert alert-warning">
        Data KRS tidak memakai id_krs. Proses update menggunakan key lama:
        {{ old.thn_ajar }}, {{ old.semester }}, {{ old.nim }}, {{ old.kodemk }}.
    </div>

    <div class="card">
        <div class="card-header bg-warning">Form Edit KRS</div>
        <div class="card-body">
            <form method="POST" action="{{ url_for('update',
                old_thn_ajar=old.thn_ajar,
                old_semester=old.semester,
                old_nim=old.nim,
                old_kodemk=old.kodemk) }}">

                <div class="row">
                    <div class="col-md-3 mb-2">
                        <label>Tahun Ajar</label>
                        <input type="number" name="thn_ajar" value="{{ data.thn_ajar }}" class="form-control" required>
                    </div>

                    <div class="col-md-3 mb-2">
                        <label>Semester</label>
                        <select name="semester" class="form-select" required>
                            <option value="1" {% if data.semester|string == '1' %}selected{% endif %}>1 - Ganjil</option>
                            <option value="2" {% if data.semester|string == '2' %}selected{% endif %}>2 - Genap</option>
                            <option value="3" {% if data.semester|string == '3' %}selected{% endif %}>3 - Pendek</option>
                        </select>
                    </div>

                    <div class="col-md-6 mb-2">
                        <label>Mahasiswa</label>
                        <select name="nim" class="form-select" required>
                            {% for m in mahasiswa %}
                            <option value="{{ m.nim }}" {% if m.nim == data.nim %}selected{% endif %}>
                                {{ m.nim }} - {{ m.nama }} - {{ m.jurusan }}
                            </option>
                            {% endfor %}
                        </select>
                    </div>
                </div>

                <div class="mb-2">
                    <label>Matakuliah</label>
                    <select name="kodemk" class="form-select" required>
                        {% for mk in matakuliah %}
                        <option value="{{ mk.kodemk }}" {% if mk.kodemk == data.kodemk %}selected{% endif %}>
                            {{ mk.kodemk }} - {{ mk.namamk }} - {{ mk.sks }} SKS
                        </option>
                        {% endfor %}
                    </select>
                </div>

                <button type="submit" class="btn btn-primary">Update</button>
                <a href="{{ url_for('index') }}" class="btn btn-secondary">Kembali</a>
            </form>
        </div>
    </div>
</div>
</body>
</html>
"""


# ==========================================================
# ROUTE HALAMAN UTAMA DAN PENCARIAN
# ==========================================================
@app.route("/")
def index():
    keyword = request.args.get("keyword", "")
    data = ambil_data_krs(keyword)
    total_sks = sum(int(row["sks"] or 0) for row in data)
    total_biaya = sum(float(row["biaya"] or 0) for row in data)

    return render_template_string(
        HTML_INDEX,
        data=data,
        keyword=keyword,
        mahasiswa=ambil_mahasiswa(),
        matakuliah=ambil_matakuliah(),
        total_sks=total_sks,
        total_biaya=total_biaya,
        label_semester=label_semester
    )


# ==========================================================
# CETAK DATA KRS KE CSV, EXCEL, DAN PDF
# ==========================================================
@app.route("/cetak_csv")
def cetak_csv():
    keyword = request.args.get("keyword", "")
    rows = ambil_data_krs(keyword)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(KOLOM_CETAK)

    for row in rows:
        writer.writerow([
            row["thn_ajar"], label_semester(row["semester"]), row["nim"], row["nama"],
            row["jurusan"], row["fakultas"], row["kodemk"], row["namamk"],
            row["sks"], row["biaya"]
        ])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=laporan_krs.csv"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response


@app.route("/cetak_excel")
def cetak_excel():
    keyword = request.args.get("keyword", "")
    rows = ambil_data_krs(keyword)

    html = """
    <html>
    <head><meta charset='utf-8'></head>
    <body>
    <h3>Laporan Data KRS</h3>
    <table border='1'>
        <tr>
    """

    for kolom in KOLOM_CETAK:
        html += "<th>" + escape(str(kolom)) + "</th>"

    html += "</tr>"

    total_sks = 0
    total_biaya = 0

    for row in rows:
        total_sks += int(row["sks"] or 0)
        total_biaya += float(row["biaya"] or 0)
        html += "<tr>"
        nilai = [
            row["thn_ajar"], label_semester(row["semester"]), row["nim"], row["nama"],
            row["jurusan"], row["fakultas"], row["kodemk"], row["namamk"],
            row["sks"], row["biaya"]
        ]
        for item in nilai:
            html += "<td>" + escape(str(item)) + "</td>"
        html += "</tr>"

    html += f"""
        <tr>
            <td colspan='8'><b>Total</b></td>
            <td><b>{total_sks}</b></td>
            <td><b>{total_biaya:,.0f}</b></td>
        </tr>
    </table>
    </body>
    </html>
    """

    response = make_response(html)
    response.headers["Content-Disposition"] = "attachment; filename=laporan_krs.xls"
    response.headers["Content-Type"] = "application/vnd.ms-excel; charset=utf-8"
    return response


@app.route("/cetak_pdf")
def cetak_pdf():
    keyword = request.args.get("keyword", "")
    rows = ambil_data_krs(keyword)
    pdf_data = buat_pdf_sederhana(rows)

    response = make_response(pdf_data)
    response.headers["Content-Disposition"] = "attachment; filename=laporan_krs.pdf"
    response.headers["Content-Type"] = "application/pdf"
    return response


# ==========================================================
# SIMPAN DATA KRS
# ==========================================================
@app.route("/simpan", methods=["POST"])
def simpan():
    thn_ajar = int(request.form["thn_ajar"])
    semester = request.form["semester"].strip()
    if semester not in ("1", "2", "3"):
        flash("Semester tidak valid. Pilih 1=Ganjil, 2=Genap, atau 3=Pendek")
        return redirect(url_for("index"))
    nim = int(request.form["nim"])
    kodemk = request.form["kodemk"].strip()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO krs (thn_ajar, semester, nim, kodemk)
            VALUES (%s, %s, %s, %s)
        """, (thn_ajar, semester, nim, kodemk))
        conn.commit()
        flash("Data KRS berhasil disimpan")
    except pymysql.err.IntegrityError:
        conn.rollback()
        flash("Data KRS gagal disimpan. Kemungkinan kombinasi KRS sudah ada atau NIM/Kode MK tidak valid")

    cursor.close()
    conn.close()
    return redirect(url_for("index"))


# ==========================================================
# EDIT DATA KRS BERDASARKAN PRIMARY KEY GABUNGAN
# ==========================================================
@app.route("/edit/<int:thn_ajar>/<semester>/<int:nim>/<kodemk>")
def edit(thn_ajar, semester, nim, kodemk):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM krs
        WHERE thn_ajar=%s
          AND semester=%s
          AND nim=%s
          AND kodemk=%s
    """, (thn_ajar, semester, nim, kodemk))

    data = cursor.fetchone()

    cursor.close()
    conn.close()

    if data is None:
        flash("Data KRS tidak ditemukan")
        return redirect(url_for("index"))

    old = {
        "thn_ajar": thn_ajar,
        "semester": semester,
        "nim": nim,
        "kodemk": kodemk
    }

    return render_template_string(
        HTML_EDIT,
        data=data,
        old=old,
        mahasiswa=ambil_mahasiswa(),
        matakuliah=ambil_matakuliah()
    )


# ==========================================================
# UPDATE DATA KRS BERDASARKAN PRIMARY KEY GABUNGAN
# ==========================================================
@app.route("/update/<int:old_thn_ajar>/<old_semester>/<int:old_nim>/<old_kodemk>", methods=["POST"])
def update(old_thn_ajar, old_semester, old_nim, old_kodemk):
    thn_ajar = int(request.form["thn_ajar"])
    semester = request.form["semester"].strip()
    if semester not in ("1", "2", "3"):
        flash("Semester tidak valid. Pilih 1=Ganjil, 2=Genap, atau 3=Pendek")
        return redirect(url_for("index"))
    nim = int(request.form["nim"])
    kodemk = request.form["kodemk"].strip()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE krs
            SET thn_ajar=%s,
                semester=%s,
                nim=%s,
                kodemk=%s
            WHERE thn_ajar=%s
              AND semester=%s
              AND nim=%s
              AND kodemk=%s
        """, (
            thn_ajar, semester, nim, kodemk,
            old_thn_ajar, old_semester, old_nim, old_kodemk
        ))
        conn.commit()
        flash("Data KRS berhasil diupdate")
    except pymysql.err.IntegrityError:
        conn.rollback()
        flash("Data KRS gagal diupdate. Kemungkinan kombinasi KRS sudah ada atau NIM/Kode MK tidak valid")

    cursor.close()
    conn.close()
    return redirect(url_for("index"))


# ==========================================================
# HAPUS DATA KRS BERDASARKAN PRIMARY KEY GABUNGAN
# ==========================================================
@app.route("/hapus/<int:thn_ajar>/<semester>/<int:nim>/<kodemk>")
def hapus(thn_ajar, semester, nim, kodemk):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM krs
        WHERE thn_ajar=%s
          AND semester=%s
          AND nim=%s
          AND kodemk=%s
    """, (thn_ajar, semester, nim, kodemk))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Data KRS berhasil dihapus")
    return redirect(url_for("index"))


# ==========================================================
# PROGRAM UTAMA
# ==========================================================
if __name__ == "__main__":
    buat_tabel()
    app.run(debug=True, port=6002)
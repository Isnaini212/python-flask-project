from flask import Flask, render_template_string, request, redirect, url_for, flash
import pymysql

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
        database="akademikdb",
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
            nim VARCHAR(15) PRIMARY KEY,
            nama VARCHAR(100) NOT NULL,
            jurusan VARCHAR(50) NOT NULL,
            fakultas VARCHAR(50) NOT NULL
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


# ==========================================================
# TEMPLATE HTML
# ==========================================================
HTML_INDEX = """
<!DOCTYPE html>
<html>
<head>
    <title>Data Mahasiswa</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">

<div class="container mt-4">
    <h3>Form Data Mahasiswa - Flask dan MySQL</h3>

    {% with messages = get_flashed_messages() %}
        {% if messages %}
            {% for msg in messages %}
                <div class="alert alert-info">{{ msg }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <div class="card mb-3">
        <div class="card-header">Input Data Mahasiswa</div>
        <div class="card-body">
            <form method="POST" action="{{ url_for('simpan') }}">
                <div class="mb-2">
                    <label>NIM</label>
                    <input type="text" name="nim" class="form-control" required>
                </div>

                <div class="mb-2">
                    <label>Nama</label>
                    <input type="text" name="nama" class="form-control" required>
                </div>

                <div class="mb-2">
                    <label>Jurusan</label>
                    <input type="text" name="jurusan" class="form-control" required>
                </div>

                <div class="mb-2">
                    <label>Fakultas</label>
                    <input type="text" name="fakultas" class="form-control" required>
                </div>

                <button type="submit" class="btn btn-primary">Simpan</button>
                <a href="{{ url_for('index') }}" class="btn btn-secondary">Reset</a>
            </form>
        </div>
    </div>

    <form method="GET" action="{{ url_for('index') }}" class="mb-3">
        <div class="input-group">
            <input type="text" name="keyword" class="form-control"
                   placeholder="Cari NIM, Nama, Jurusan, atau Fakultas"
                   value="{{ keyword }}">
            <button class="btn btn-success" type="submit">Cari</button>
            <a href="{{ url_for('index') }}" class="btn btn-outline-secondary">Tampil Semua</a>
        </div>
    </form>

    <table class="table table-bordered table-striped">
        <thead class="table-dark">
            <tr>
                <th>NIM</th>
                <th>Nama</th>
                <th>Jurusan</th>
                <th>Fakultas</th>
                <th width="200">Aksi</th>
            </tr>
        </thead>

        <tbody>
            {% for row in data %}
            <tr>
                <td>{{ row.nim }}</td>
                <td>{{ row.nama }}</td>
                <td>{{ row.jurusan }}</td>
                <td>{{ row.fakultas }}</td>
                <td>
                    <a href="{{ url_for('edit', nim=row.nim) }}" class="btn btn-warning btn-sm">Edit</a>
                    <a href="{{ url_for('hapus', nim=row.nim) }}"
                       class="btn btn-danger btn-sm"
                       onclick="return confirm('Yakin ingin menghapus data ini?')">
                       Hapus
                    </a>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="5" class="text-center">Data belum tersedia</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

</body>
</html>
"""


HTML_EDIT = """
<!DOCTYPE html>
<html>
<head>
    <title>Edit Mahasiswa</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">

<div class="container mt-4">
    <h3>Edit Data Mahasiswa</h3>

    <div class="card">
        <div class="card-header">Form Edit Mahasiswa</div>
        <div class="card-body">
            <form method="POST" action="{{ url_for('update', nim=data.nim) }}">
                <div class="mb-2">
                    <label>NIM</label>
                    <input type="text" value="{{ data.nim }}" class="form-control" readonly>
                </div>

                <div class="mb-2">
                    <label>Nama</label>
                    <input type="text" name="nama" value="{{ data.nama }}" class="form-control" required>
                </div>

                <div class="mb-2">
                    <label>Jurusan</label>
                    <input type="text" name="jurusan" value="{{ data.jurusan }}" class="form-control" required>
                </div>

                <div class="mb-2">
                    <label>Fakultas</label>
                    <input type="text" name="fakultas" value="{{ data.fakultas }}" class="form-control" required>
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

    conn = get_connection()
    cursor = conn.cursor()

    if keyword:
        sql = """
            SELECT * FROM mahasiswa
            WHERE nim LIKE %s
               OR nama LIKE %s
               OR jurusan LIKE %s
               OR fakultas LIKE %s
            ORDER BY nim
        """
        cari = "%" + keyword + "%"
        cursor.execute(sql, (cari, cari, cari, cari))
    else:
        cursor.execute("SELECT * FROM mahasiswa ORDER BY nim")

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template_string(HTML_INDEX, data=data, keyword=keyword)


# ==========================================================
# SIMPAN DATA
# ==========================================================
@app.route("/simpan", methods=["POST"])
def simpan():
    nim = request.form["nim"]
    nama = request.form["nama"]
    jurusan = request.form["jurusan"]
    fakultas = request.form["fakultas"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM mahasiswa WHERE nim=%s", (nim,))
    cek = cursor.fetchone()

    if cek:
        flash("NIM sudah terdaftar")
        cursor.close()
        conn.close()
        return redirect(url_for("index"))

    cursor.execute("""
        INSERT INTO mahasiswa (nim, nama, jurusan, fakultas)
        VALUES (%s, %s, %s, %s)
    """, (nim, nama, jurusan, fakultas))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Data mahasiswa berhasil disimpan")
    return redirect(url_for("index"))


# ==========================================================
# EDIT DATA
# ==========================================================
@app.route("/edit/<nim>")
def edit(nim):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM mahasiswa WHERE nim=%s", (nim,))
    data = cursor.fetchone()

    cursor.close()
    conn.close()

    if data is None:
        flash("Data tidak ditemukan")
        return redirect(url_for("index"))

    return render_template_string(HTML_EDIT, data=data)


# ==========================================================
# UPDATE DATA
# ==========================================================
@app.route("/update/<nim>", methods=["POST"])
def update(nim):
    nama = request.form["nama"]
    jurusan = request.form["jurusan"]
    fakultas = request.form["fakultas"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE mahasiswa
        SET nama=%s, jurusan=%s, fakultas=%s
        WHERE nim=%s
    """, (nama, jurusan, fakultas, nim))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Data mahasiswa berhasil diupdate")
    return redirect(url_for("index"))


# ==========================================================
# HAPUS DATA
# ==========================================================
@app.route("/hapus/<nim>")
def hapus(nim):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM mahasiswa WHERE nim=%s", (nim,))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Data mahasiswa berhasil dihapus")
    return redirect(url_for("index"))


# ==========================================================
# PROGRAM UTAMA
# ==========================================================
if __name__ == "__main__":
    buat_tabel()
    app.run(debug=True, port=6000)

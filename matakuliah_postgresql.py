from flask import Flask, render_template_string, request, redirect, url_for, flash
import psycopg2
import psycopg2.extras

app = Flask(__name__)
app.secret_key = "12345"

DB_HOST = "localhost"
DB_NAME = "AKADEMIKDB"
DB_USER = "postgres"
DB_PASSWORD = "admin123"
DB_PORT = 5432


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        cursor_factory=psycopg2.extras.RealDictCursor
    )


def buat_tabel():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matakuliah (
            kodemk VARCHAR(15) PRIMARY KEY,
            namamk VARCHAR(100) NOT NULL,
            sks VARCHAR(50) NOT NULL,
            biaya DECIMAL(12,2) DEFAULT 0
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


HTML_INDEX = """
<!DOCTYPE html>
<html>
<head>
    <title>Data matakuliah</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">

<div class="container mt-4">
    <h3>Form Data matakuliah - Flask dan PostgreSQL</h3>

    {% with messages = get_flashed_messages() %}
        {% if messages %}
            {% for msg in messages %}
                <div class="alert alert-info">{{ msg }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <div class="card mb-3">
        <div class="card-header">Input Data matakuliah</div>
        <div class="card-body">
            <form method="POST" action="{{ url_for('simpan') }}">
                <div class="mb-2">
                    <label>Kode Matakuliah</label>
                    <input type="text" name="kodemk" class="form-control" required>
                </div>

                <div class="mb-2">
                    <label>Nama Matakuliah</label>
                    <input type="text" name="namamk" class="form-control" required>
                </div>

                <div class="mb-2">
                    <label>SKS</label>
                    <input type="text" name="sks" class="form-control" required>
                </div>

                <div class="mb-2">
                    <label>Biaya</label>
                    <input type="text" name="biaya" class="form-control" required>
                </div>

                <button type="submit" class="btn btn-primary">Simpan</button>
                <a href="{{ url_for('index') }}" class="btn btn-secondary">Reset</a>
            </form>
        </div>
    </div>

    <form method="GET" action="{{ url_for('index') }}" class="mb-3">
        <div class="input-group">
            <input type="text" name="keyword" class="form-control"
                   placeholder="Cari kodemk, namamk, sks, atau biaya"
                   value="{{ keyword }}">
            <button class="btn btn-success" type="submit">Cari</button>
            <a href="{{ url_for('index') }}" class="btn btn-outline-secondary">Tampil Semua</a>
        </div>
    </form>

    <table class="table table-bordered table-striped">
        <thead class="table-dark">
            <tr>
                <th>kodemk</th>
                <th>namamk</th>
                <th>sks</th>
                <th>biaya</th>
                <th width="200">Aksi</th>
            </tr>
        </thead>

        <tbody>
            {% for row in data %}
            <tr>
                <td>{{ row["kodemk"] }}</td>
                <td>{{ row["namamk"] }}</td>
                <td>{{ row["sks"] }}</td>
                <td>{{ row["biaya"] }}</td>
                <td>
                    <a href="{{ url_for('edit', kodemk=row['kodemk']) }}" class="btn btn-warning btn-sm">Edit</a>
                    <a href="{{ url_for('hapus', kodemk=row['kodemk']) }}"
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
    <title>Edit matakuliah</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">

<div class="container mt-4">
    <h3>Edit Data matakuliah</h3>

    <div class="card">
        <div class="card-header">Form Edit matakuliah</div>
        <div class="card-body">
            <form method="POST" action="{{ url_for('update', kodemk=data['kodemk']) }}">
                <div class="mb-2">
                    <label>kodemk</label>
                    <input type="text" value="{{ data['kodemk'] }}" class="form-control" readonly>
                </div>

                <div class="mb-2">
                    <label>namamk</label>
                    <input type="text" name="namamk" value="{{ data['namamk'] }}" class="form-control" required>
                </div>

                <div class="mb-2">
                    <label>sks</label>
                    <input type="text" name="sks" value="{{ data['sks'] }}" class="form-control" required>
                </div>

                <div class="mb-2">
                    <label>biaya</label>
                    <input type="text" name="biaya" value="{{ data['biaya'] }}" class="form-control" required>
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


@app.route("/")
def index():
    keyword = request.args.get("keyword", "")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        if keyword:
            cari = "%" + keyword + "%"
            cursor.execute("""
                SELECT kodemk, namamk, sks, biaya
                FROM matakuliah
                WHERE kodemk ILIKE %s
                   OR namamk ILIKE %s
                   OR sks ILIKE %s
                   OR biaya ILIKE %s
                ORDER BY kodemk
            """, (cari, cari, cari, cari))
        else:
            cursor.execute("""
                SELECT kodemk, namamk, sks, biaya
                FROM matakuliah
                ORDER BY kodemk
            """)

        data = cursor.fetchall()

        cursor.close()
        conn.close()

    except Exception as error:
        data = []
        flash("Terjadi error saat mengambil data: " + str(error))

    return render_template_string(HTML_INDEX, data=data, keyword=keyword)


@app.route("/simpan", methods=["POST"])
def simpan():
    kodemk = request.form.get("kodemk", "").strip()
    namamk = request.form.get("namamk", "").strip()
    sks = request.form.get("sks", "").strip()
    biaya = request.form.get("biaya", "").strip()

    if kodemk == "" or namamk == "" or sks == "" or biaya == "":
        flash("Semua data wajib diisi")
        return redirect(url_for("index"))

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT kodemk FROM matakuliah WHERE kodemk=%s", (kodemk,))
        cek = cursor.fetchone()

        if cek:
            flash("kodemk sudah terdaftar")
            cursor.close()
            conn.close()
            return redirect(url_for("index"))

        cursor.execute("""
            INSERT INTO matakuliah (kodemk, namamk, sks, biaya)
            VALUES (%s, %s, %s, %s)
        """, (kodemk, namamk, sks, biaya))

        conn.commit()
        cursor.close()
        conn.close()

        flash("Data matakuliah berhasil disimpan")

    except Exception as error:
        flash("Gagal menyimpan data: " + str(error))

    return redirect(url_for("index"))


@app.route("/edit/<kodemk>")
def edit(kodemk):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT kodemk, namamk, sks, biaya
            FROM matakuliah
            WHERE kodemk=%s
        """, (kodemk,))

        data = cursor.fetchone()

        cursor.close()
        conn.close()

        if data is None:
            flash("Data matakuliah tidak ditemukan")
            return redirect(url_for("index"))

        return render_template_string(HTML_EDIT, data=data)

    except Exception as error:
        flash("Gagal membuka data edit: " + str(error))
        return redirect(url_for("index"))


@app.route("/update/<kodemk>", methods=["POST"])
def update(kodemk):
    namamk = request.form.get("namamk", "").strip()
    sks = request.form.get("sks", "").strip()
    biaya = request.form.get("biaya", "").strip()

    if namamk == "" or sks == "" or biaya == "":
        flash("namamk, sks, dan biaya wajib diisi")
        return redirect(url_for("edit", kodemk=kodemk))

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE matakuliah
            SET namamk=%s, sks=%s, biaya=%s
            WHERE kodemk=%s
        """, (namamk, sks, biaya, kodemk))

        conn.commit()
        cursor.close()
        conn.close()

        flash("Data matakuliah berhasil diupdate")

    except Exception as error:
        flash("Gagal mengupdate data: " + str(error))

    return redirect(url_for("index"))


@app.route("/hapus/<kodemk>")
def hapus(kodemk):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM matakuliah WHERE kodemk=%s", (kodemk,))

        conn.commit()
        cursor.close()
        conn.close()

        flash("Data matakuliah berhasil dihapus")

    except Exception as error:
        flash("Gagal menghapus data: " + str(error))

    return redirect(url_for("index"))


if __name__ == "__main__":
    try:
        buat_tabel()
        print("Aplikasi berhasil dijalankan.")
        print("Buka browser: http://127.0.0.1:5001")
        app.run(debug=True, port=5001)
    except Exception as error:
        print("Aplikasi gagal dijalankan.")
        print("Penyebab error:", error)
        print("Pastikan PostgreSQL aktif, database akademikdb sudah dibuat,")
        print("dan konfigurasi user/password PostgreSQL sudah benar.")

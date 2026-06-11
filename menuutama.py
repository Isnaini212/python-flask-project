from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Menu Utama Akademik</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">

<div class="container mt-5">
    <div class="card shadow">
        <div class="card-header bg-primary text-white">
            <h3>MENU UTAMA SISTEM AKADEMIK</h3>
        </div>

        <div class="card-body">

            <div class="d-grid gap-3">

                <a href="http://127.0.0.1:5000"
                   class="btn btn-success btn-lg">
                   DATA MAHASISWA
                </a>

                <a href="http://127.0.0.1:5001"
                   class="btn btn-warning btn-lg">
                   DATA MATAKULIAH
                </a>

                <a href="http://127.0.0.1:5002"
                   class="btn btn-danger btn-lg">
                   DATA KRS
                </a>

            </div>

        </div>

        <div class="card-footer text-center">
            Sistem Informasi Akademik Flask + MySQL
        </div>
    </div>
</div>

</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(debug=True, port=5004)
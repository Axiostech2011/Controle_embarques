from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import sqlite3
from datetime import datetime
from flask import send_file
app = Flask(__name__)
app.secret_key = "AxiosSecret2026"

# =====================================
# USUÁRIOS
# =====================================

ADMIN_USUARIO = "Axios"
ADMIN_SENHA = "AxiosSecret"

USUARIOS_CONSULTA = {
    "Whiteplas": "Axios2011",
    "cliente2": "cliente123",
    "cliente3": "cliente123",
    "cliente4": "cliente123"
}

# =====================================
# BANCO DE DADOS
# =====================================

def init_db():

    with sqlite3.connect("embarques.db") as conn:

        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS embarques (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            etd TEXT NOT NULL,
            eta TEXT NOT NULL,

            exportador TEXT NOT NULL,
            produto TEXT NOT NULL,

            navio TEXT NOT NULL,
            cia_maritima TEXT NOT NULL,

            ref TEXT NOT NULL,
            fatura TEXT NOT NULL,

            porto TEXT NOT NULL,

            container INTEGER NOT NULL,

            status TEXT NOT NULL,

            data_finalizacao TEXT

        )
        """)

        conn.commit()

init_db()

# =====================================
# LOGIN OBRIGATÓRIO
# =====================================

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not session.get("logado"):
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return decorated_function

# =====================================
# SOMENTE ADMIN
# =====================================

def admin_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if session.get("perfil") != "admin":

            flash("Acesso restrito.")

            return redirect(url_for("todos_embarques"))

        return f(*args, **kwargs)

    return decorated_function

# =====================================
# FORMATAR DATA
# =====================================

def formatar_data(data):

    try:

        return datetime.strptime(
            data,
            "%Y-%m-%d"
        ).strftime("%d/%m/%Y")

    except:

        return data
    # =====================================
# LOGIN
# =====================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = request.form["usuario"]
        senha = request.form["senha"]

        # ADMIN

        if (
            usuario == ADMIN_USUARIO and
            senha == ADMIN_SENHA
        ):

            session["logado"] = True
            session["perfil"] = "admin"
            session["usuario"] = usuario

            return redirect(url_for("todos_embarques"))

        # CLIENTES

        elif (
            usuario in USUARIOS_CONSULTA and
            senha == USUARIOS_CONSULTA[usuario]
        ):

            session["logado"] = True
            session["perfil"] = "consulta"
            session["usuario"] = usuario

            return redirect(url_for("todos_embarques"))

        flash("Usuário ou senha inválidos")

    return render_template("login.html")


# =====================================
# LOGOUT
# =====================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =====================================
# PÁGINA INICIAL
# =====================================

@app.route("/")
@login_required
@admin_required
def index():

    return render_template("index.html")


# =====================================
# ADICIONAR EMBARQUE
# =====================================

@app.route("/adicionar", methods=["POST"])
@login_required
@admin_required
def adicionar():

    etd = request.form["etd"]
    eta = request.form["eta"]

    exportador = request.form["exportador"].upper()
    produto = request.form["produto"].upper()

    navio = request.form["navio"].upper()
    cia_maritima = request.form["cia_maritima"].upper()

    ref = request.form["ref"].upper()
    fatura = request.form["fatura"].upper()

    porto = request.form["porto"].upper()

    container = int(request.form["container"])

    status = request.form["status"]

    data_finalizacao = None

    if status == "Finalizado":

        data_finalizacao = datetime.now().strftime("%d/%m/%Y")

    with sqlite3.connect("embarques.db") as conn:

        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO embarques (
            etd,
            eta,
            exportador,
            produto,
            navio,
            cia_maritima,
            ref,
            fatura,
            porto,
            container,
            status,
            data_finalizacao
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            etd,
            eta,
            exportador,
            produto,
            navio,
            cia_maritima,
            ref,
            fatura,
            porto,
            container,
            status,
            data_finalizacao
        ))

        conn.commit()

    flash("Embarque cadastrado com sucesso!")

    return redirect(url_for("todos_embarques"))
# =====================================
# EMBARQUES ATIVOS
# =====================================

@app.route("/todos_embarques")
@login_required
def todos_embarques():

    with sqlite3.connect("embarques.db") as conn:

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM embarques
        WHERE status <> 'Finalizado'
        ORDER BY eta ASC
        """)

        dados = cursor.fetchall()

    embarques = []

    total_containers = 0

    for e in dados:

        embarques.append({

            "id": e["id"],

            "etd": formatar_data(e["etd"]),
            "eta": formatar_data(e["eta"]),

            "exportador": e["exportador"],
            "produto": e["produto"],

            "navio": e["navio"],
            "cia_maritima": e["cia_maritima"],

            "ref": e["ref"],
            "fatura": e["fatura"],

            "porto": e["porto"],

            "container": e["container"],

            "status": e["status"]

        })

        total_containers += e["container"]

    return render_template(
        "todos_embarques.html",
        embarques=embarques,
        total_containers=total_containers,
        perfil=session.get("perfil"),
        usuario=session.get("usuario")
    )


# =====================================
# HISTÓRICO
# =====================================

@app.route("/historico")
@login_required
def historico():

    with sqlite3.connect("embarques.db") as conn:

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM embarques
        WHERE status = 'Finalizado'
        ORDER BY id DESC
        """)

        dados = cursor.fetchall()

    embarques = []

    for e in dados:

        embarques.append({

            "id": e["id"],

            "etd": formatar_data(e["etd"]),
            "eta": formatar_data(e["eta"]),

            "exportador": e["exportador"],
            "produto": e["produto"],

            "navio": e["navio"],

            "ref": e["ref"],
            "fatura": e["fatura"],

            "porto": e["porto"],

            "container": e["container"],

            "status": e["status"],

            "data_finalizacao": e["data_finalizacao"]

        })

    return render_template(
        "historico.html",
        embarques=embarques,
        perfil=session.get("perfil"),
        usuario=session.get("usuario")
    )


# =====================================
# ALTERAR STATUS
# =====================================

@app.route("/alterar_status/<int:id>", methods=["POST"])
@login_required
@admin_required
def alterar_status(id):

    novo_status = request.form["status"]

    data_finalizacao = None

    if novo_status == "Finalizado":

        data_finalizacao = datetime.now().strftime("%d/%m/%Y")

    with sqlite3.connect("embarques.db") as conn:

        cursor = conn.cursor()

        cursor.execute("""
        UPDATE embarques
        SET
            status=?,
            data_finalizacao=?
        WHERE id=?
        """,
        (
            novo_status,
            data_finalizacao,
            id
        ))

        conn.commit()

    return redirect(url_for("todos_embarques"))
# =====================================
# EDITAR EMBARQUE
# =====================================

@app.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def editar(id):

    if request.method == "POST":

        etd = request.form["etd"]
        eta = request.form["eta"]

        exportador = request.form["exportador"].upper()
        produto = request.form["produto"].upper()

        navio = request.form["navio"].upper()
        cia_maritima = request.form["cia_maritima"].upper()

        ref = request.form["ref"].upper()
        fatura = request.form["fatura"].upper()

        porto = request.form["porto"].upper()

        container = int(request.form["container"])

        with sqlite3.connect("embarques.db") as conn:

            cursor = conn.cursor()

            cursor.execute("""
            UPDATE embarques
            SET
                etd=?,
                eta=?,
                exportador=?,
                produto=?,
                navio=?,
                cia_maritima=?,
                ref=?,
                fatura=?,
                porto=?,
                container=?
            WHERE id=?
            """,
            (
                etd,
                eta,
                exportador,
                produto,
                navio,
                cia_maritima,
                ref,
                fatura,
                porto,
                container,
                id
            ))

            conn.commit()

        flash("Embarque atualizado com sucesso!")

        return redirect(url_for("todos_embarques"))

    with sqlite3.connect("embarques.db") as conn:

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM embarques WHERE id=?",
            (id,)
        )

        embarque = cursor.fetchone()

    return render_template(
        "editar.html",
        embarque=embarque,
        perfil=session.get("perfil"),
        usuario=session.get("usuario")
    )

# =====================================
# BACKUP BANCO
# =====================================

@app.route("/backup")
@login_required
@admin_required
def backup():

    return send_file(
        "embarques.db",
        as_attachment=True,
        download_name="backup_embarques.db"
    )
# =====================================
# EXECUTAR
# =====================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

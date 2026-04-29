from flask import Flask, render_template, request, redirect,session
import sqlite3
import matplotlib.pyplot as plt
import os
import csv
import io
import base64

app = Flask(__name__)
app.secret_key = "football_secret_key_2026"

ADMIN_PASSWORD = "1234"

def init_db():
    conn = sqlite3.connect("players.db")
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS players(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        position TEXT,
        speed INTEGER
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
    )
    ''')
    conn.commit()
    conn.close()
@app.route("/boxplot-all")
def boxplot_all():

    conn = sqlite3.connect("players.db")
    c = conn.cursor()
    c.execute("SELECT position, speed FROM players")
    data = c.fetchall()
    conn.close()

    positions = {
        "GK": [],
        "CB": [],
        "RB": [],
        "CDM": [],
        "CM": [],
        "CAM": [],
        "LW": [],
        "RW": [],
        "ST": []
    }

    # remplir les listes
    for pos, speed in data:
        if pos in positions:
            positions[pos].append(speed)

    # préparer données pour boxplot
    labels = list(positions.keys())
    values = list(positions.values())

    # supprimer postes vides (important)
    labels_clean = []
    values_clean = []

    for l, v in zip(labels, values):
        if len(v) > 0:
            labels_clean.append(l)
            values_clean.append(v)

    plt.figure(figsize=(10,5))

    plt.boxplot(values_clean, labels=labels_clean)

    plt.title("Speed distribution by position")
    plt.ylabel("Speed (km/h)")
    plt.xticks(rotation=45)

    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)

    graph = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return render_template("boxplot.html", graph=graph)

def create_graph(players):
    # TOP 10 joueurs les plus rapides
    players = sorted(players, key=lambda x: x[4], reverse=True)[:10]

    names = [p[1] for p in players]
    speeds = [p[4] for p in players]

    plt.figure(figsize=(10,5))

    plt.barh(names, speeds)  # graphique horizontal

    plt.title("Top 10 Player Speed Analysis")
    plt.xlabel("Speed (km/h)")
    plt.ylabel("Players")

    plt.tight_layout()
    plt.savefig("static/graph.png")
    plt.close()

def graph_scatter(players):
    ages = [p[2] for p in players]
    speeds = [p[4] for p in players]

    plt.figure(figsize=(8,4))
    plt.scatter(ages, speeds)

    plt.title("Nuage de points Âge - Vitesse")
    plt.xlabel("Âge")
    plt.ylabel("Speed en km/h")

    plt.tight_layout()
    plt.savefig("static/scatter.png")
    plt.close()

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("players.db")
        c = conn.cursor()

        try:
            c.execute("INSERT INTO users(username, password) VALUES (?, ?)",
                      (username, password))
            conn.commit()
        except:
            return "Utilisateur déjà existant ❌"

        conn.close()

        return redirect("/login")

    return render_template("register.html")
@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")

    return render_template("index.html", user=session["user"])

#Route login / logout

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("players.db")
        c = conn.cursor()

        c.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        )

        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = username

            # Si c'est toi = admin
            if username == "admin":
                session["admin"] = True

            return redirect("/")
        else:
            return "Login incorrect ❌"

    return render_template("login.html")


# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# DELETE PLAYER (admin seulement)
@app.route("/delete/<int:id>", methods=["POST"])
def delete_player(id):

    if "admin" not in session:
        return "Accès réservé à l'administrateur ❌"

    conn = sqlite3.connect("players.db")
    c = conn.cursor()

    c.execute("DELETE FROM players WHERE id = ?", (id,))


    conn.commit()
    conn.close()

    return redirect("/stats")

    
@app.route("/home")
def Accueil():
    if "user" not in session:
        return redirect("/login")

    return render_template("home.html")

@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    age = request.form["age"]
    position = request.form["position"]
    speed = request.form["speed"]

    conn = sqlite3.connect("players.db")
    c = conn.cursor()
    c.execute("INSERT INTO players(name, age, position, speed) VALUES (?, ?, ?, ?)",
              (name, age, position, speed))
    conn.commit()
    conn.close()

    return redirect("/stats")

@app.route("/addplayer")
def addplayer():
    return render_template("index.html")

@app.route("/stats")
def stats():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("players.db")

    c = conn.cursor()
    c.execute("SELECT * FROM players")
    players = c.fetchall()
    conn.close()

    # classement
    players_sorted = sorted(players,
    key=lambda x: x[4], reverse=True)

    # graphique basé sur classement ou données brutes
    create_graph(players_sorted)
    graph_scatter(players_sorted)

    total = len(players_sorted)

    if total > 0:
        ages = [p[2] for p in players_sorted]
        speeds = [p[4] for p in players_sorted]

        age_moy = sum(ages) / total
        speed_moy = sum(speeds) / total

        best_player = players_sorted[0]  # déjà trié
    else:
        age_moy = 0
        speed_moy = 0
        best_player = None

    return render_template(
        "stats.html",
        players=players_sorted,
        total=total,
        age_moy=round(age_moy, 2),
        speed_moy=round(speed_moy, 2),
        best_player=best_player
    )

@app.route("/export")
def export():
    

    conn = sqlite3.connect("players.db")
    c = conn.cursor()
    c.execute("SELECT * FROM players")
    players = c.fetchall()
    conn.close()

    with open("players.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name",
        "Age", "Position", "Speed"])
        writer.writerows(players)

    return "CSV exporté"



if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

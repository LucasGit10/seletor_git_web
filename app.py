from flask import Flask, render_template, request, Response, redirect, url_for, flash
import requests
import subprocess

app = Flask(__name__)
app.secret_key = "sua_chave_secreta_aqui"  # necessário para flash messages

def listar_repos_github(usuario):
    url = f"https://api.github.com/users/{usuario}/repos"
    resposta = requests.get(url)
    if resposta.status_code == 200:
        dados = resposta.json()
        return [
            {
                "name": repo["name"],
                "html_url": repo["html_url"],
                "clone_url": repo["clone_url"],
                "description": repo.get("description") or "Sem descrição"
            }
            for repo in dados
        ]
    return None

def gerar_workflow_yaml(repo_name, app_type):
    if app_type == "dotnet":
        return f"""\
name: CI/CD .NET para {repo_name}
on:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '8.0.300'
      - run: dotnet build
        working-directory: ./src
"""
    elif app_type == "node":
        return f"""\
name: CI/CD Node.js para {repo_name}
on:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install
      - run: npm run build
"""
    elif app_type == "python":
        return f"""\
name: CI/CD Python para {repo_name}
on:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest
"""
    elif app_type == "java":
        return f"""\
name: CI/CD Java para {repo_name}
on:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v3
        with:
          java-version: '21'
      - run: ./gradlew build
"""
    else:
        return "# Tipo de aplicação não suportado."

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        repos = listar_repos_github(usuario)
        if repos is None:
            erro = f"Erro ao acessar GitHub para o usuário '{usuario}'"
            return render_template("index.html", erro=erro)
        return render_template("selecionar.html", usuario=usuario, repositorios=repos)
    return render_template("index.html")

@app.route("/gerar_workflow", methods=["POST"])
def gerar_workflow():
    repo_name = request.form.get("repo")
    app_type = request.form.get("app_type")

    yaml_content = gerar_workflow_yaml(repo_name, app_type)

    return Response(
        yaml_content,
        mimetype="text/yaml",
        headers={"Content-Disposition": f"attachment;filename=ci-cd-{repo_name}.yml"},
    )

@app.route("/clonar", methods=["POST"])
def clonar():
    clone_url = request.form.get("clone_url")
    repo_name = request.form.get("repo_name")
    if not clone_url or not repo_name:
        flash("URL ou nome do repositório não fornecido.", "danger")
        return redirect(url_for("index"))
    
    try:
        # Atenção: o caminho de destino pode ser alterado conforme seu ambiente
        destino = f"./repos/{repo_name}"
        
        # Comando git clone (garanta que pasta ./repos exista e tenha permissão)
        resultado = subprocess.run(
            ["git", "clone", clone_url, destino],
            capture_output=True,
            text=True,
            check=True,
        )
        flash(f"Repositório '{repo_name}' clonado com sucesso em {destino}.", "success")
    except subprocess.CalledProcessError as e:
        flash(f"Erro ao clonar repositório: {e.stderr}", "danger")

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)

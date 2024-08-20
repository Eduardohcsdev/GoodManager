from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# INCIALIZAÇÃO
app = Flask(__name__)
app.secret_key = '12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mybase.sqlite3'
db = SQLAlchemy(app)
app.app_context().push()


# BANCO DE DADOS
class Usuario(db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, unique=True)
    senha = db.Column(db.String)

    def __init__(self, nome, senha):
        self.nome = nome
        self.senha = senha
class Tarefa(db.Model):
    __tablename__ = "tarefas"
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    status = db.Column(db.String, default='a_fazer')  # Status inicial

    def __init__(self, descricao, usuario_id, data_vencimento=None, status='a_fazer'):
        self.descricao = descricao
        self.usuario_id = usuario_id
        self.data_vencimento = data_vencimento
        self.status = status

# PRA NÃO BUGAR O BD
with app.app_context():
    db.create_all()


# FUNÇÃO:
def verificar_crendenciais(request):
    usuario = Usuario.query.filter_by(nome=request.form.get('username')).first()
    if usuario and usuario.senha == request.form['password']:  # Verifica a senha
        return True
    return False


@app.route('/')
def home():
    if 'username' not in session:
        return render_template('login.html')
    usuario = Usuario.query.filter_by(nome=session['username']).first()
    tarefas = Tarefa.query.filter_by(usuario_id=usuario.id).all()
    return render_template('home.html', usuario=usuario, tarefas=tarefas)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # Se o método for POST e se ele verifiar as credenciais
        if verificar_crendenciais(request):
            session['username'] = request.form.get('username')
            return redirect(url_for('home'))
        else:
            flash('Usuário ou senha errados, tente novamente', 'danger')
            return redirect(url_for('home'))

@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        nome = request.form.get('username')
        senha = request.form.get('password')
        if nome and senha:
            usuario = Usuario(nome, senha)
            db.session.add(usuario)
            db.session.commit()
            usuarios = Usuario.query.all()
            flash('Usuário adicionado com sucesso!')
            return redirect(url_for('home'))

@app.route("/admin")
def admin():
    if 'username'in session:
        if session['username'] == 'admin':
            usuarios = Usuario.query.all()
            return render_template('admin.html', usuarios=usuarios)
    return 'Você não está autorizado para ver essa página. Por favor, faça login'

@app.route('/add_tarefa', methods=['POST'])
def add_tarefa():
    if 'username' in session:
        descricao = request.form.get('descricao')
        data_vencimento = request.form.get('data_vencimento')
        usuario = Usuario.query.filter_by(nome=session['username']).first()
        if descricao:
            tarefa = Tarefa(descricao=descricao, usuario_id=usuario.id, data_vencimento=datetime.strptime(
                data_vencimento, '%Y-%m-%d').date())
            db.session.add(tarefa)
            db.session.commit()
            flash('Tarefa adicionada com sucesso!')
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/edit_tarefa/<int:tarefa_id>', methods=['GET', 'POST'])
def edit_tarefa(tarefa_id):
    tarefa = Tarefa.query.get(tarefa_id)
    if request.method == 'POST':
        nova_descricao = request.form.get('descricao')
        nova_data_vencimento = request.form.get('data_vencimento')
        if nova_descricao:
            tarefa.descricao = nova_descricao
        if nova_data_vencimento:
            tarefa.data_vencimento = datetime.strptime(nova_data_vencimento, '%Y-%m-%d').date()
        db.session.commit()
        flash('Tarefa atualizada com sucesso!')
        return redirect(url_for('home'))
    return render_template('edit_tarefa.html', tarefa=tarefa)

@app.route('/delete_tarefa/<int:tarefa_id>', methods=['POST'])
def delete_tarefa(tarefa_id):
    tarefa = Tarefa.query.get(tarefa_id)
    if tarefa:
        db.session.delete(tarefa)
        db.session.commit()
        flash('Tarefa excluída com sucesso!')
        return redirect(url_for('home'))
    return render_template('delete_tarefa')

@app.route('/update_task_status', methods=['POST'])
def update_task_status():
    data = request.get_json()
    tarefa = Tarefa.query.get(data['id'])
    if tarefa:
        tarefa.status = data['status']
        db.session.commit()
    return '', 204

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    usuario = Usuario.query.get(user_id)
    if usuario:
        db.session.delete(usuario)
        db.session.commit()
        flash('você deletou um usuário')
    return redirect(url_for('admin'))

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    usuario = Usuario.query.get(user_id)
    if request.method == 'POST':
        novo_nome = request.form.get('username')
        nova_senha = request.form.get('password')
        if novo_nome:
            usuario.nome = novo_nome
        if nova_senha:
            usuario.senha = nova_senha
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('edit_user.html', usuario=usuario)



@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))  # Redireciona para a página de login após logout


if __name__ == "__main__":
    app.run(debug=True)

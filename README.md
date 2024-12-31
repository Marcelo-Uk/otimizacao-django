# 🛠️ Projeto Django - Otimização Linear

Este projeto Django implementa um sistema de otimização linear com interface gráfica e geração de gráficos.


## 🚀 **1. Pré-requisitos**

Antes de iniciar, certifique-se de ter os seguintes itens instalados:

- **Python 3.8+**
- **pip** (gerenciador de pacotes Python)
- **virtualenv** (opcional, mas recomendado)


## 🛠️ **2. Clonando o Projeto**

Clone este repositório para o seu computador:

> git clone https://github.com/seu-usuario/seu-repositorio.git
> cd seu-repositorio


## 🐍 3. Configurando o Ambiente Virtual

Crie um ambiente virtual:

Windows:
> python -m venv venv

Ative o ambiente virtual:
> venv\Scripts\activate

Linux/MacOS:
> python -m venv venv
> 
Ative o ambiente virtual:
> source venv/bin/activate


## 📦 4. Instalando Dependências

Instale as bibliotecas necessárias:

> pip install -r requirements.txt


## 🗄️ 5. Configurando o Banco de Dados

Crie as tabelas do banco de dados:

> python manage.py makemigrations
> python manage.py migrate


## 🔑 6. Criar Superusuário (opcional)

Para acessar o painel administrativo:

> python manage.py createsuperuser


## 🚦 7. Executando o Servidor Local

Inicie o servidor Django:

> python manage.py runserver

Acesse no navegador:
👉 http://127.0.0.1:8000/


## 📊 8. Testando a Aplicação

> Vá para /solver/.
> Preencha os campos e execute a otimização linear.
> Visualize os resultados e gráficos gerados.


## 🎓 9. Tecnologias Utilizadas

> Django: Framework Web Python
> Pulp: Biblioteca para Programação Linear
> Matplotlib: Geração de Gráficos
> HTML5, CSS3, JavaScript: Interface Gráfica

from flask import Flask, render_template, request, redirect, url_for, flash, session
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_segura'

# Configuración de sesión
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# Ruta para el login
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == 'alumno' and password == 'amrd':
        session['logged_in'] = True
        return redirect(url_for('index'))
    else:
        flash('Usuario o contraseña incorrectos')
        return redirect(url_for('index'))

# Ruta para logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

# Funciones para resolver triángulos (senos y cosenos)
def calcular_triangulo_sen(angulo_A=None, angulo_B=None, angulo_C=None, lado_a=None, lado_b=None, lado_c=None):
    # Implementación existente...
    pass

def graficar_triangulo_sen(lado_a, lado_b, lado_c, angulo_A, angulo_B, angulo_C):
    # Implementación existente...
    pass

def calcular_triangulo_cos(a=None, b=None, c=None, A=None, B=None, C=None):
    # Implementación existente...
    pass

def graficar_triangulo_cos(a, b, c, A, B, C):
    # Implementación existente...
    pass

def resolver_triangulo(a, b, c, A, B, C):
    # Implementación existente...
    pass

# Ruta principal
@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('logged_in'):
        return render_template("login.html")
    
    if request.method == 'POST':
        try:
            def get_val(field):
                val = request.form.get(field)
                return float(val) if val and val.strip() != "" else None

            a_val = get_val("lado_a")
            b_val = get_val("lado_b")
            c_val = get_val("lado_c")
            A_val = get_val("angulo_A")
            B_val = get_val("angulo_B")
            C_val = get_val("angulo_C")
            
            (res_a, res_b, res_c, res_A, res_B, res_C), metodo = resolver_triangulo(a_val, b_val, c_val, A_val, B_val, C_val)
            
            perimetro = res_a + res_b + res_c
            s = perimetro / 2
            area = math.sqrt(s * (s - res_a) * (s - res_b) * (s - res_c))
            
            if metodo == "senos":
                imagen = graficar_triangulo_sen(res_a, res_b, res_c, res_A, res_B, res_C)
            else:
                imagen = graficar_triangulo_cos(res_a, res_b, res_c, res_A, res_B, res_C)
            
            resultados = {
                'lado_a': f"{res_a:.2f}",
                'lado_b': f"{res_b:.2f}",
                'lado_c': f"{res_c:.2f}",
                'angulo_A': f"{res_A:.2f}",
                'angulo_B': f"{res_B:.2f}",
                'angulo_C': f"{res_C:.2f}",
                'perimetro': f"{perimetro:.2f}",
                'area': f"{area:.2f}",
                'metodo': metodo
            }
            
            return render_template("index.html", resultados=resultados, imagen=imagen)
        except Exception as e:
            flash(str(e))
            return redirect(url_for('index'))
    return render_template("index.html", resultados=None)

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, flash, session
import math
import matplotlib
matplotlib.use('Agg')  # Backend no interactivo
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'  # Cambia esto por una clave más segura en producción

# Configuración de sesión (para mantener el login activo)
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora en segundos

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

# ---------------------------
# Funciones para ley de senos (sin cambios)
# ---------------------------
def calcular_triangulo_sen(angulo_A=None, angulo_B=None, angulo_C=None, 
                             lado_a=None, lado_b=None, lado_c=None):
    known_angles = [angulo_A, angulo_B, angulo_C]
    num_angles = sum(1 for x in known_angles if x is not None)
    known_sides = [lado_a, lado_b, lado_c]
    num_sides = sum(1 for x in known_sides if x is not None)
    if num_angles + num_sides < 3 or num_sides < 1:
        raise ValueError("Información insuficiente para resolver el triángulo.")
    if num_angles >= 2:
        if angulo_A is None:
            angulo_A = 180 - (angulo_B + angulo_C)
        elif angulo_B is None:
            angulo_B = 180 - (angulo_A + angulo_C)
        elif angulo_C is None:
            angulo_C = 180 - (angulo_A + angulo_B)
    if angulo_A is not None and angulo_B is not None and angulo_C is not None:
        if abs(angulo_A + angulo_B + angulo_C - 180) > 1e-5:
            raise ValueError("Los ángulos no suman 180 grados.")
        if angulo_A <= 0 or angulo_B <= 0 or angulo_C <= 0:
            raise ValueError("Los ángulos deben ser mayores que 0.")
    if num_angles >= 2 and num_sides >= 1:
        if lado_a is not None:
            ratio = lado_a / math.sin(math.radians(angulo_A))
            if lado_b is None:
                lado_b = ratio * math.sin(math.radians(angulo_B))
            if lado_c is None:
                lado_c = ratio * math.sin(math.radians(angulo_C))
            return lado_a, lado_b, lado_c, angulo_A, angulo_B, angulo_C
        elif lado_b is not None:
            ratio = lado_b / math.sin(math.radians(angulo_B))
            if lado_a is None:
                lado_a = ratio * math.sin(math.radians(angulo_A))
            if lado_c is None:
                lado_c = ratio * math.sin(math.radians(angulo_C))
            return lado_a, lado_b, lado_c, angulo_A, angulo_B, angulo_C
        elif lado_c is not None:
            ratio = lado_c / math.sin(math.radians(angulo_C))
            if lado_a is None:
                lado_a = ratio * math.sin(math.radians(angulo_A))
            if lado_b is None:
                lado_b = ratio * math.sin(math.radians(angulo_B))
            return lado_a, lado_b, lado_c, angulo_A, angulo_B, angulo_C
    # Caso SSA: 2 lados y 1 ángulo
    if num_angles == 1 and num_sides == 2:
        if angulo_A is not None and lado_a is not None:
            if lado_b is not None:
                sinB = lado_b * math.sin(math.radians(angulo_A)) / lado_a
                if sinB < -1 or sinB > 1:
                    raise ValueError("No hay solución, ya que sin(β) está fuera de rango.")
                angulo_B = math.degrees(math.asin(sinB))
                angulo_C = 180 - angulo_A - angulo_B
                lado_c = lado_a * math.sin(math.radians(angulo_C)) / math.sin(math.radians(angulo_A))
                return lado_a, lado_b, lado_c, angulo_A, angulo_B, angulo_C
            elif lado_c is not None:
                sinC = lado_c * math.sin(math.radians(angulo_A)) / lado_a
                if sinC < -1 or sinC > 1:
                    raise ValueError("No hay solución, ya que sin(γ) está fuera de rango.")
                angulo_C = math.degrees(math.asin(sinC))
                angulo_B = 180 - angulo_A - angulo_C
                lado_b = lado_a * math.sin(math.radians(angulo_B)) / math.sin(math.radians(angulo_A))
                return lado_a, lado_b, lado_c, angulo_A, angulo_B, angulo_C
        if angulo_B is not None and lado_b is not None:
            if lado_a is not None:
                sinA = lado_a * math.sin(math.radians(angulo_B)) / lado_b
                if sinA < -1 or sinA > 1:
                    raise ValueError("No hay solución, ya que sin(α) está fuera de rango.")
                angulo_A = math.degrees(math.asin(sinA))
                angulo_C = 180 - angulo_A - angulo_B
                lado_c = lado_b * math.sin(math.radians(angulo_C)) / math.sin(math.radians(angulo_B))
                return lado_a, lado_b, lado_c, angulo_A, angulo_B, angulo_C
            elif lado_c is not None:
                sinC = lado_c * math.sin(math.radians(angulo_B)) / lado_b
                if sinC < -1 or sinC > 1:
                    raise ValueError("No hay solución, ya que sin(γ) está fuera de rango.")
                angulo_C = math.degrees(math.asin(sinC))
                angulo_A = 180 - angulo_B - angulo_C
                lado_a = lado_b * math.sin(math.radians(angulo_A)) / math.sin(math.radians(angulo_B))
                return lado_a, lado_b, lado_c, angulo_A, angulo_B, angulo_C
        if angulo_C is not None and lado_c is not None:
            if lado_a is not None:
                sinA = lado_a * math.sin(math.radians(angulo_C)) / lado_c
                if sinA < -1 or sinA > 1:
                    raise ValueError("No hay solución, ya que sin(α) está fuera de rango.")
                angulo_A = math.degrees(math.asin(sinA))
                angulo_B = 180 - angulo_A - angulo_C
                lado_b = lado_a * math.sin(math.radians(angulo_B)) / math.sin(math.radians(angulo_A))
                return lado_a, lado_b, lado_c, angulo_A, angulo_B, angulo_C
            elif lado_b is not None:
                sinB = lado_b * math.sin(math.radians(angulo_C)) / lado_c
                if sinB < -1 or sinB > 1:
                    raise ValueError("No hay solución, ya que sin(β) está fuera de rango.")
                angulo_B = math.degrees(math.asin(sinB))
                angulo_A = 180 - angulo_B - angulo_C
                lado_a = lado_b * math.sin(math.radians(angulo_A)) / math.sin(math.radians(angulo_B))
                return lado_a, lado_b, lado_c, angulo_A, angulo_B, angulo_C
    raise ValueError("No se pudo determinar el triángulo con la información proporcionada.")

def graficar_triangulo_sen(lado_a, lado_b, lado_c, angulo_A, angulo_B, angulo_C):
    A_point = (0, 0)
    B_point = (lado_c, 0)
    C_point = (lado_b * math.cos(math.radians(angulo_A)), lado_b * math.sin(math.radians(angulo_A)))
    
    plt.figure()
    plt.plot([A_point[0], B_point[0]], [A_point[1], B_point[1]], 'b-', label='Lado c')
    plt.plot([A_point[0], C_point[0]], [A_point[1], C_point[1]], 'r-', label='Lado b')
    plt.plot([B_point[0], C_point[0]], [B_point[1], C_point[1]], 'g-', label='Lado a')
    
    plt.text(A_point[0], A_point[1], 'α', fontsize=12, ha='right')
    plt.text(B_point[0], B_point[1], 'β', fontsize=12, ha='left')
    plt.text(C_point[0], C_point[1], 'γ', fontsize=12, ha='center')
    
    plt.xlim(-1, lado_c + 1)
    plt.ylim(-1, max(lado_a, lado_b) + 1)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.title('Triángulo Resuelto (Ley de Senos)')
    plt.grid()
    plt.legend()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()
    return image_base64

# ----------------------------
# Funciones para ley de cosenos (sin cambios)
# ----------------------------
def calcular_triangulo_cos(a=None, b=None, c=None, A=None, B=None, C=None):
    # Si se conocen 2 ángulos, calcular el tercero
    if sum(x is not None for x in [A, B, C]) == 2:
        if A is None:
            A = 180 - B - C
        elif B is None:
            B = 180 - A - C
        elif C is None:
            C = 180 - A - B

    # Caso SSS: tres lados conocidos
    if all(x is not None for x in [a, b, c]):
        A = math.degrees(math.acos((b**2 + c**2 - a**2) / (2 * b * c)))
        B = math.degrees(math.acos((a**2 + c**2 - b**2) / (2 * a * c)))
        C = 180 - A - B
        return a, b, c, A, B, C

    # Caso SAS: dos lados y el ángulo incluido
    if a is not None and b is not None and C is not None:
        c = math.sqrt(a**2 + b**2 - 2 * a * b * math.cos(math.radians(C)))
        A = math.degrees(math.asin(a * math.sin(math.radians(C)) / c))
        B = 180 - C - A
        return a, b, c, A, B, C
    if a is not None and c is not None and B is not None:
        b = math.sqrt(a**2 + c**2 - 2 * a * c * math.cos(math.radians(B)))
        A = math.degrees(math.asin(a * math.sin(math.radians(B)) / b))
        C = 180 - B - A
        return a, b, c, A, B, C
    if b is not None and c is not None and A is not None:
        a = math.sqrt(b**2 + c**2 - 2 * b * c * math.cos(math.radians(A)))
        B = math.degrees(math.asin(b * math.sin(math.radians(A)) / a))
        C = 180 - A - B
        return a, b, c, A, B, C

    # Caso ASA/AAS: 2 ángulos y 1 lado
    if sum(x is not None for x in [A, B, C]) >= 2 and sum(x is not None for x in [a, b, c]) == 1:
        if a is not None:
            k = a / math.sin(math.radians(A))
            b = k * math.sin(math.radians(B))
            c = k * math.sin(math.radians(C))
        elif b is not None:
            k = b / math.sin(math.radians(B))
            a = k * math.sin(math.radians(A))
            c = k * math.sin(math.radians(C))
        elif c is not None:
            k = c / math.sin(math.radians(C))
            a = k * math.sin(math.radians(A))
            b = k * math.sin(math.radians(B))
        return a, b, c, A, B, C

    # Caso SSA: 2 lados y un ángulo opuesto a uno de ellos
    if a is not None and b is not None and A is not None:
        ratio = b * math.sin(math.radians(A)) / a
        if ratio > 1 or ratio < -1:
            raise ValueError("No hay solución real para el caso SSA (a, b, α).")
        B1 = math.degrees(math.asin(ratio))
        if A + B1 < 180:
            B = B1
            C = 180 - A - B
            c = a * math.sin(math.radians(C)) / math.sin(math.radians(A))
            return a, b, c, A, B, C
        else:
            B = 180 - B1
            C = 180 - A - B
            c = a * math.sin(math.radians(C)) / math.sin(math.radians(A))
            return a, b, c, A, B, C
    if a is not None and c is not None and A is not None:
        ratio = c * math.sin(math.radians(A)) / a
        if ratio > 1 or ratio < -1:
            raise ValueError("No hay solución real para el caso SSA (a, c, α).")
        C1 = math.degrees(math.asin(ratio))
        if A + C1 < 180:
            C = C1
            B = 180 - A - C
            b = a * math.sin(math.radians(B)) / math.sin(math.radians(A))
            return a, b, c, A, B, C
        else:
            C = 180 - C1
            B = 180 - A - C
            b = a * math.sin(math.radians(B)) / math.sin(math.radians(A))
            return a, b, c, A, B, C
    if b is not None and c is not None and B is not None:
        ratio = c * math.sin(math.radians(B)) / b
        if ratio > 1 or ratio < -1:
            raise ValueError("No hay solución real para el caso SSA (b, c, β).")
        C1 = math.degrees(math.asin(ratio))
        if B + C1 < 180:
            C = C1
            A = 180 - B - C
            a = b * math.sin(math.radians(A)) / math.sin(math.radians(B))
            return a, b, c, A, B, C
        else:
            C = 180 - C1
            A = 180 - B - C
            a = b * math.sin(math.radians(A)) / math.sin(math.radians(B))
            return a, b, c, A, B, C

    raise ValueError("No se pudo resolver el triángulo con la información dada.")

def graficar_triangulo_cos(a, b, c, A, B, C):
    A_point = (0, 0)
    B_point = (c, 0)
    C_point = (b * math.cos(math.radians(A)), b * math.sin(math.radians(A)))
    
    plt.figure()
    plt.plot([A_point[0], B_point[0]], [A_point[1], B_point[1]], 'g-', label='Lado c')
    plt.plot([A_point[0], C_point[0]], [A_point[1], C_point[1]], 'r-', label='Lado b')
    plt.plot([B_point[0], C_point[0]], [B_point[1], C_point[1]], 'b-', label='Lado a')
    
    plt.text(A_point[0], A_point[1], 'α', fontsize=12, ha='right')
    plt.text(B_point[0], B_point[1], 'β', fontsize=12, ha='left')
    plt.text(C_point[0], C_point[1], 'γ', fontsize=12, ha='center')
    
    x_vals = [A_point[0], B_point[0], C_point[0]]
    y_vals = [A_point[1], B_point[1], C_point[1]]
    plt.xlim(min(x_vals) - 1, max(x_vals) + 1)
    plt.ylim(min(y_vals) - 1, max(y_vals) + 1)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.title('Triángulo Resuelto (Ley de Cosenos)')
    plt.grid()
    plt.legend()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()
    return image_base64

# --------------------------------
# Función que detecta el método a usar (sin cambios)
# --------------------------------
def resolver_triangulo(a, b, c, A, B, C):
    count_sides = sum(x is not None for x in [a, b, c])
    count_angles = sum(x is not None for x in [A, B, C])
    
    if count_sides + count_angles < 3 or count_sides < 1:
        raise ValueError("Se requieren al menos 3 datos (con al menos 1 lado) para resolver el triángulo.")
    
    # Si se conocen 2 o más ángulos -> ASA/AAS -> Ley de Senos
    if count_angles >= 2:
        method = "senos"
    # Si se conocen los 3 lados -> SSS -> Ley de Cosenos
    elif count_sides == 3:
        method = "cosenos"
    # Caso SAS
    elif count_sides == 2 and count_angles == 1:
        if (a is not None and b is not None and C is not None) or \
           (a is not None and c is not None and B is not None) or \
           (b is not None and c is not None and A is not None):
            method = "cosenos"
        else:
            method = "senos"
    # Si se conoce 1 lado y 2 ángulos -> Ley de Senos
    elif count_sides == 1 and count_angles == 2:
        method = "senos"
    else:
        method = "senos"  # Por defecto
    
    if method == "senos":
        return calcular_triangulo_sen(angulo_A=A, angulo_B=B, angulo_C=C,
                                      lado_a=a, lado_b=b, lado_c=c), method
    else:
        return calcular_triangulo_cos(a=a, b=b, c=c, A=A, B=B, C=C), method

# ---------------------------
# Ruta principal de la aplicación (modificada para incluir login)
# ---------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    # Verificar si el usuario está logueado
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

@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('logged_in'):
        return render_template("login.html")
    
    # Variables para la calculadora
    calc_input = request.form.get('calc_input', '')
    calc_result = request.form.get('calc_result', '')
    
    # Variables para el triángulo
    resultados = None
    imagen = None
    
    if request.method == 'POST':
        # Manejar cálculo de la calculadora
        if 'calc_input' in request.form:
            try:
                calc_result = str(eval(calc_input))
            except:
                calc_result = "Error"
        
        # Manejar cálculo del triángulo
        else:
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
                
            except Exception as e:
                flash(str(e))

    return render_template("index.html",
                         resultados=resultados,
                         imagen=imagen,
                         calc_input=calc_input,
                         calc_result=calc_result)

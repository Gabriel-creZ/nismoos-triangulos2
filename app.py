from flask import Flask, render_template, request, redirect, url_for, flash, session
import math
import matplotlib
matplotlib.use('Agg')  # Backend no interactivo
import matplotlib.pyplot as plt
import io
import base64
import plotly.graph_objects as go

app = Flask(__name__)
app.secret_key = 'j350z271123r'

# Configuración de sesión
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# ============================
# Funciones para resolución de triángulos
# ============================

def calcular_triangulo_sen(angulo_A=None, angulo_B=None, angulo_C=None, 
                             lado_a=None, lado_b=None, lado_c=None):
    # Se requiere al menos 2 ángulos y 1 lado o 2 lados y 1 ángulo
    known_angles = [angulo_A, angulo_B, angulo_C]
    num_angles = sum(x is not None for x in known_angles)
    known_sides = [lado_a, lado_b, lado_c]
    num_sides = sum(x is not None for x in known_sides)
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
            raise ValueError("Los ángulos no suman 180°.")
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
    # Para casos SSA, se puede agregar el código existente si se desea.
    raise ValueError("No se pudo determinar el triángulo con la información proporcionada (SSA).")

def calcular_triangulo_cos(a=None, b=None, c=None, A=None, B=None, C=None):
    # Si se conocen los 3 lados, calcular ángulos con ley de cosenos:
    if a is not None and b is not None and c is not None:
        try:
            A = math.degrees(math.acos((b**2 + c**2 - a**2) / (2 * b * c)))
            B = math.degrees(math.acos((a**2 + c**2 - b**2) / (2 * a * c)))
            C = 180 - A - B
            return a, b, c, A, B, C
        except Exception as e:
            raise ValueError("Error al calcular ángulos con la ley de cosenos: " + str(e))
    # Si se conocen 2 lados y el ángulo incluido:
    if a is not None and b is not None and C is not None:
        c = math.sqrt(a**2 + b**2 - 2*a*b*math.cos(math.radians(C)))
        A = math.degrees(math.asin(a * math.sin(math.radians(C)) / c))
        B = 180 - C - A
        return a, b, c, A, B, C
    if a is not None and c is not None and B is not None:
        b = math.sqrt(a**2 + c**2 - 2*a*c*math.cos(math.radians(B)))
        A = math.degrees(math.asin(a * math.sin(math.radians(B)) / b))
        C = 180 - B - A
        return a, b, c, A, B, C
    if b is not None and c is not None and A is not None:
        a = math.sqrt(b**2 + c**2 - 2*b*c*math.cos(math.radians(A)))
        B = math.degrees(math.asin(b * math.sin(math.radians(A)) / a))
        C = 180 - A - B
        return a, b, c, A, B, C
    raise ValueError("No se pudo calcular el triángulo con la ley de cosenos.")

def calcular_triangulo_pitagoras(a=None, b=None, c=None, A=None, B=None, C=None):
    # Si se ingresa un ángulo de 90°, se resuelve como triángulo rectángulo.
    if A is not None and abs(A - 90) < 1e-2:
        a_calc = math.sqrt(b**2 + c**2)
        return a_calc, b, c, 90, math.degrees(math.asin(b/a_calc)), math.degrees(math.asin(c/a_calc))
    if B is not None and abs(B - 90) < 1e-2:
        b_calc = math.sqrt(a**2 + c**2)
        return a, b_calc, c, math.degrees(math.asin(a/b_calc)), 90, math.degrees(math.asin(c/b_calc))
    if C is not None and abs(C - 90) < 1e-2:
        c_calc = math.sqrt(a**2 + b**2)
        return a, b, c_calc, math.degrees(math.asin(a/c_calc)), math.degrees(math.asin(b/c_calc)), 90
    raise ValueError("No se pudo identificar un triángulo rectángulo.")

def resolver_triangulo_altura(base, altura):
    # Método basado en Altura y Área
    area = 0.5 * base * altura
    return {'base': base, 'altura': altura, 'area': area}

def resolver_triangulo(a, b, c, A, B, C, metodo_sel="auto", altura_input=None):
    # Si se selecciona el método "altura" y se ingresó una altura, usar ese método.
    if metodo_sel == "altura":
        if a is not None:
            # Usamos el lado a como base
            area = 0.5 * a * altura_input
            return {"base": a, "altura": altura_input, "area": area}, "altura"
        else:
            raise ValueError("Para el método Altura se requiere al menos un lado (base) y la altura.")
    # Si se selecciona el método "pitagoras"
    if metodo_sel == "pitagoras":
        return calcular_triangulo_pitagoras(a, b, c, A, B, C), "pitagoras"
    # Método automático: si se conocen 3 lados, se usa cosenos; sino, si hay 2 ángulos, se usa senos.
    count_sides = sum(x is not None for x in [a, b, c])
    count_angles = sum(x is not None for x in [A, B, C])
    if count_sides == 3:
        try:
            return calcular_triangulo_cos(a, b, c, A, B, C), "cosenos"
        except Exception as e:
            # En caso de error, intente pitagoras si corresponde
            if (A is not None and abs(A-90)<1e-2) or (B is not None and abs(B-90)<1e-2) or (C is not None and abs(C-90)<1e-2):
                return calcular_triangulo_pitagoras(a, b, c, A, B, C), "pitagoras"
            else:
                raise
    elif count_angles >= 2:
        return calcular_triangulo_sen(angulo_A=A, angulo_B=B, angulo_C=C, lado_a=a, lado_b=b, lado_c=c), "senos"
    elif count_sides == 2 and count_angles == 1:
        # Por defecto, usamos cosenos en este caso
        return calcular_triangulo_cos(a, b, c, A, B, C), "cosenos"
    else:
        # Caso mínimo, intenta ley de senos
        return calcular_triangulo_sen(angulo_A=A, angulo_B=B, angulo_C=C, lado_a=a, lado_b=b, lado_c=c), "senos"

# ============================
# Funciones de cálculos adicionales
# ============================

def calcular_medianas(a, b, c):
    m_a = 0.5 * math.sqrt(2*(b**2 + c**2) - a**2)
    m_b = 0.5 * math.sqrt(2*(a**2 + c**2) - b**2)
    m_c = 0.5 * math.sqrt(2*(a**2 + b**2) - c**2)
    return m_a, m_b, m_c

def calcular_circumradius(a, b, c, area):
    if area == 0:
        return None
    return (a * b * c) / (4 * area)

def determinar_tipo_triangulo(a, b, c):
    if abs(a - b) < 1e-5 and abs(b - c) < 1e-5:
        return "Equilátero"
    elif abs(a - b) < 1e-5 or abs(a - c) < 1e-5 or abs(b - c) < 1e-5:
        return "Isósceles"
    else:
        return "Escaleno"

def clasificar_triangulo_por_angulo(A, B, C):
    mayor = max(A, B, C)
    if abs(mayor - 90) < 1e-2:
        return "Rectángulo"
    elif mayor > 90:
        return "Obtuso"
    else:
        return "Acutángulo"

def convertir_unidades(valor, de="cm", a="m"):
    conversiones = {("cm", "m"): 0.01, ("m", "cm"): 100}
    return valor * conversiones.get((de, a), 1)

def calcular_puntos_notables(a, b, c, A, B, C):
    # Usando el mismo esquema que antes: A en (0,0), B en (c,0) y C calculado.
    A_point = (0, 0)
    B_point = (c, 0)
    C_point = (b * math.cos(math.radians(A)), b * math.sin(math.radians(A)))
    # Mediatrices para circuncentro
    def mediatriz(P, Q):
        mid = ((P[0]+Q[0])/2, (P[1]+Q[1])/2)
        if abs(P[0]-Q[0]) < 1e-5:
            slope = 0
        else:
            m = (Q[1]-P[1])/(Q[0]-P[0])
            slope = None if abs(m)<1e-5 else -1/m
        return mid, slope
    midAB, slopeAB = mediatriz(A_point, B_point)
    midAC, slopeAC = mediatriz(A_point, C_point)
    def interseccion(P1, m1, P2, m2):
        if m1 is None:
            x = P1[0]
            y = m2*(x-P2[0]) + P2[1]
        elif m2 is None:
            x = P2[0]
            y = m1*(x-P1[0]) + P1[1]
        else:
            x = (m1*P1[0] - m2*P2[0] + P2[1] - P1[1])/(m1-m2)
            y = m1*(x-P1[0]) + P1[1]
        return (x, y)
    circumcenter = interseccion(midAB, slopeAB, midAC, slopeAC)
    # Altitudes para ortocentro
    def altitud(P, Q, R):
        if abs(Q[0]-R[0]) < 1e-5:
            m_alt = 0
        else:
            m_qr = (R[1]-Q[1])/(R[0]-Q[0])
            m_alt = None if abs(m_qr)<1e-5 else -1/m_qr
        return P, m_alt
    alt_A = altitud(A_point, B_point, C_point)
    alt_B = altitud(B_point, A_point, C_point)
    ortocenter = interseccion(alt_A[0], alt_A[1], alt_B[0], alt_B[1])
    return circumcenter, ortocenter, A_point, B_point, C_point

# ================================
# Funciones de graficado (estático e interactivo)
# ================================

def graficar_triangulo_estatico(a, b, c, A, B, C):
    A_point = (0, 0)
    B_point = (c, 0)
    C_point = (b * math.cos(math.radians(A)), b * math.sin(math.radians(A)))
    
    plt.figure(figsize=(7,7))
    # Dibujar triángulo
    plt.plot([A_point[0], B_point[0]], [A_point[1], B_point[1]], 'b-', label=f"Lado c = {c:.2f}")
    plt.plot([A_point[0], C_point[0]], [A_point[1], C_point[1]], 'r-', label=f"Lado b = {b:.2f}")
    plt.plot([B_point[0], C_point[0]], [B_point[1], C_point[1]], 'g-', label=f"Lado a = {a:.2f}")
    # Dibujar medianas
    mAB = ((A_point[0]+B_point[0])/2, (A_point[1]+B_point[1])/2)
    mAC = ((A_point[0]+C_point[0])/2, (A_point[1]+C_point[1])/2)
    mBC = ((B_point[0]+C_point[0])/2, (B_point[1]+C_point[1])/2)
    plt.plot([C_point[0], mAB[0]], [C_point[1], mAB[1]], 'm--', label="Medianas")
    plt.plot([B_point[0], mAC[0]], [B_point[1], mAC[1]], 'm--')
    plt.plot([A_point[0], mBC[0]], [A_point[1], mBC[1]], 'm--')
    # Dibujar circuncentro y ortocentro
    circumcenter, ortocenter, _, _, _ = calcular_puntos_notables(a, b, c, A, B, C)
    plt.plot(circumcenter[0], circumcenter[1], 'ko', label="Circuncentro")
    plt.plot(ortocenter[0], ortocenter[1], 'ks', label="Ortocentro")
    # Etiquetas
    plt.text(A_point[0]-0.2, A_point[1]-0.2, "A", fontsize=12)
    plt.text(B_point[0]+0.2, B_point[1]-0.2, "B", fontsize=12)
    plt.text(C_point[0], C_point[1]+0.2, "C", fontsize=12)
    # Límites y aspecto
    plt.xlim(min(A_point[0], B_point[0], C_point[0]) - 1, max(A_point[0], B_point[0], C_point[0]) + 1)
    plt.ylim(min(A_point[1], B_point[1], C_point[1]) - 1, max(A_point[1], B_point[1], C_point[1]) + 1)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.title("Triángulo Resuelto")
    plt.grid()
    plt.legend()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_stat = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()
    return img_stat

def graficar_triangulo_interactivo(a, b, c, A, B, C):
    A_point = (0, 0)
    B_point = (c, 0)
    C_point = (b * math.cos(math.radians(A)), b * math.sin(math.radians(A)))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[A_point[0], B_point[0]], y=[A_point[1], B_point[1]],
                             mode='lines', name=f"Lado c = {c:.2f}", line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=[A_point[0], C_point[0]], y=[A_point[1], C_point[1]],
                             mode='lines', name=f"Lado b = {b:.2f}", line=dict(color='red')))
    fig.add_trace(go.Scatter(x=[B_point[0], C_point[0]], y=[B_point[1], C_point[1]],
                             mode='lines', name=f"Lado a = {a:.2f}", line=dict(color='green')))
    circumcenter, ortocenter, _, _, _ = calcular_puntos_notables(a, b, c, A, B, C)
    fig.add_trace(go.Scatter(x=[circumcenter[0]], y=[circumcenter[1]],
                             mode='markers', name="Circuncentro", marker=dict(color='black', size=10)))
    fig.add_trace(go.Scatter(x=[ortocenter[0]], y=[ortocenter[1]],
                             mode='markers', name="Ortocentro", marker=dict(color='black', size=10, symbol='square')))
    fig.update_layout(title="Gráfica Interactiva del Triángulo",
                      xaxis_title="Eje X",
                      yaxis_title="Eje Y",
                      template="plotly_white", showlegend=True)
    return fig.to_html(full_html=False)

# ================================
# Rutas y páginas adicionales
# ================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'alumno' and password == 'amrd':
            session['logged_in'] = True
            session['user'] = username
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos, intente de nuevo.')
            return render_template("login.html")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("Sesión cerrada correctamente.")
    return redirect(url_for('login'))

# Ruta principal (index) con selector de método
@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
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
            altura_val = get_val("altura")  # Campo adicional para el método Altura
            metodo_sel = request.form.get("metodo_sel", "auto")
            
            if metodo_sel == "altura":
                res = resolver_triangulo_altura(a_val if a_val is not None else b_val or c_val, altura_val)
                # Solo se calculan base, altura y área en este método.
                resultados = {
                    'base': f"{res['base']:.2f}",
                    'altura': f"{res['altura']:.2f}",
                    'area': f"{res['area']:.2f}"
                }
                # No se grafican triángulos completos.
                return render_template("resultado.html", resultados=resultados, imagen_est=None, imagen_int=None)
            else:
                res, metodo = resolver_triangulo(a_val, b_val, c_val, A_val, B_val, C_val, metodo_sel, altura_val)
                # Calcular área usando Herón
                perimetro = res[0] + res[1] + res[2]
                s = perimetro / 2
                area = math.sqrt(s * (s - res[0]) * (s - res[1]) * (s - res[2]))
                # Altura respecto a lado c
                altura_tri = (2 * area) / res[2] if res[2] != 0 else None
                mediana_a, mediana_b, mediana_c = calcular_medianas(res[0], res[1], res[2])
                circumradius = calcular_circumradius(res[0], res[1], res[2], area)
                tipo_tri = determinar_tipo_triangulo(res[0], res[1], res[2])
                clasif_ang = clasificar_triangulo_por_angulo(res[3], res[4], res[5])
                pitagoras = ""
                if abs(max(res[3], res[4], res[5]) - 90) < 1e-2:
                    pitagoras = "Se cumple el teorema de Pitágoras."
                
                # Gráficas: se generan ambas (estática e interactiva)
                imagen_est = graficar_triangulo_estatico(res[0], res[1], res[2], res[3], res[4], res[5])
                imagen_int = graficar_triangulo_interactivo(res[0], res[1], res[2], res[3], res[4], res[5])
                
                resultados = {
                    'lado_a': f"{res[0]:.2f}",
                    'lado_b': f"{res[1]:.2f}",
                    'lado_c': f"{res[2]:.2f}",
                    'angulo_A': f"{res[3]:.2f}",
                    'angulo_B': f"{res[4]:.2f}",
                    'angulo_C': f"{res[5]:.2f}",
                    'perimetro': f"{perimetro:.2f}",
                    'area': f"{area:.2f}",
                    'altura': f"{altura_tri:.2f}" if altura_tri is not None else "N/A",
                    'mediana_a': f"{mediana_a:.2f}",
                    'mediana_b': f"{mediana_b:.2f}",
                    'mediana_c': f"{mediana_c:.2f}",
                    'circumradius': f"{circumradius:.2f}" if circumradius is not None else "N/A",
                    'tipo_triangulo': tipo_tri,
                    'clasificacion': clasif_ang,
                    'pitagoras': pitagoras,
                    'metodo': metodo
                }
                return render_template("resultado.html", resultados=resultados, imagen_est=imagen_est, imagen_int=imagen_int)
        except Exception as e:
            flash(str(e))
            return redirect(url_for('index'))
    return render_template("index.html", resultados=None)

# Ruta para comparar triángulos (opcional)
@app.route('/comparar', methods=['GET', 'POST'])
def comparar():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    # Implementa la comparación según el código anterior...
    return render_template("comparar.html", res1=None)

# =============================
# Rutas para Donar y Reportar Error
# =============================
@app.route('/donar')
def donar():
    return render_template("donar.html")

@app.route('/reporte', methods=['GET', 'POST'])
def reporte():
    if request.method == 'POST':
        # Implementa envío de reporte (por ejemplo, usando SMTP)
        flash("Reporte enviado correctamente. ¡Gracias por tus comentarios!")
        return redirect(url_for('reporte'))
    return render_template("reporte.html")

if __name__ == "__main__":
    app.run(debug=True)

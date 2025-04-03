from flask import Flask, render_template, request, redirect, url_for, flash, session
import math
import matplotlib
matplotlib.use('Agg')  # Backend no interactivo
import matplotlib.pyplot as plt
import io
import base64
import plotly.graph_objects as go
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'j350z271123r'

# Configuración de sesión
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# Configuración SMTP
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'castilloreyesgabriel4@gmail.com'
SMTP_PASSWORD = 'wkiqrqkcvhoirdyr'

# ============================
# Funciones para resolución de triángulos
# ============================

def calcular_triangulo_sen(angulo_A=None, angulo_B=None, angulo_C=None, 
                             lado_a=None, lado_b=None, lado_c=None):
    # Requiere al menos 2 ángulos y 1 lado
    known_angles = [angulo_A, angulo_B, angulo_C]
    num_angles = sum(x is not None for x in known_angles)
    known_sides = [lado_a, lado_b, lado_c]
    num_sides = sum(x is not None for x in known_sides)
    if num_angles + num_sides < 3 or num_sides < 1:
        raise ValueError("Información insuficiente para resolver el triángulo (Ley de Senos).")
    if num_angles >= 2:
        if angulo_A is None:
            angulo_A = 180 - (angulo_B + angulo_C)
        elif angulo_B is None:
            angulo_B = 180 - (angulo_A + angulo_C)
        elif angulo_C is None:
            angulo_C = 180 - (angulo_A + angulo_B)
    if angulo_A is not None and angulo_B is not None and angulo_C is not None:
        if abs(angulo_A + angulo_B + angulo_C - 180) > 1e-2:
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
    raise ValueError("No se pudo resolver el triángulo con la Ley de Senos (verifica tus datos).")

def calcular_triangulo_cos(a=None, b=None, c=None, A=None, B=None, C=None):
    # Si se conocen los 3 lados y no se proporcionan ángulos, calcularlos
    if a is not None and b is not None and c is not None:
        if A is None and B is None and C is None:
            try:
                A = math.degrees(math.acos((b**2 + c**2 - a**2) / (2 * b * c)))
                B = math.degrees(math.acos((a**2 + c**2 - b**2) / (2 * a * c)))
                C = 180 - A - B
            except Exception as e:
                raise ValueError("Error en la Ley de Cosenos: " + str(e))
            return a, b, c, A, B, C
        elif A is not None and B is not None and C is not None:
            if abs(A + B + C - 180) > 1e-2:
                raise ValueError("Los ángulos proporcionados no suman 180°.")
            return a, b, c, A, B, C
    raise ValueError("Para la Ley de Cosenos se requieren los 3 lados (y opcionalmente los ángulos).")

def resolver_triangulo_altura(base, altura=None, area_input=None):
    # Si se ingresa altura, se calcula el área.
    # Si se ingresa área, se calcula la altura.
    if altura is not None:
        area = 0.5 * base * altura
        return {"base": base, "altura": altura, "area": area}
    elif area_input is not None:
        altura_calculada = (2 * area_input) / base
        return {"base": base, "altura": altura_calculada, "area": area_input}
    else:
        raise ValueError("Debes proporcionar la altura o el área junto con la base.")

def resolver_triangulo(a, b, c, A, B, C, metodo_sel="auto", altura_input=None, area_input=None):
    if metodo_sel == "altura":
        if a is not None and (altura_input is not None or area_input is not None):
            res = resolver_triangulo_altura(a, altura_input, area_input)
            return res, "Altura y Área"
        else:
            raise ValueError("Para Altura y Área se requiere la base (lado a) y la altura o el área.")
    # Método automático: se usa Ley de Cosenos o Ley de Senos según los datos.
    count_sides = sum(x is not None for x in [a, b, c])
    count_angles = sum(x is not None for x in [A, B, C])
    if count_sides == 3:
        try:
            result = calcular_triangulo_cos(a, b, c, A, B, C)
            return result, "Ley de Senos o Cosenos"
        except Exception as e:
            result = calcular_triangulo_sen(angulo_A=A, angulo_B=B, angulo_C=C, 
                                            lado_a=a, lado_b=b, lado_c=c)
            return result, "Ley de Senos o Cosenos"
    elif count_angles >= 2:
        result = calcular_triangulo_sen(angulo_A=A, angulo_B=B, angulo_C=C, 
                                        lado_a=a, lado_b=b, lado_c=c)
        return result, "Ley de Senos o Cosenos"
    else:
        result = calcular_triangulo_sen(angulo_A=A, angulo_B=B, angulo_C=C, 
                                        lado_a=a, lado_b=b, lado_c=c)
        return result, "Ley de Senos o Cosenos"

# ============================
# Funciones adicionales
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

def convertir_unidades(valor, de, a):
    conversiones = {
        ("cm", "m"): 0.01,
        ("m", "cm"): 100,
        ("m", "km"): 0.001,
        ("km", "m"): 1000,
        ("in", "cm"): 2.54,
        ("cm", "in"): 1/2.54,
        ("ft", "m"): 0.3048,
        ("m", "ft"): 1/0.3048
    }
    factor = conversiones.get((de, a), 1)
    return valor * factor

def calcular_puntos_notables(a, b, c, A, B, C):
    A_point = (0, 0)
    B_point = (c, 0)
    C_point = (b * math.cos(math.radians(A)), b * math.sin(math.radians(A)))
    def mediatriz(P, Q):
        mid = ((P[0]+Q[0])/2, (P[1]+Q[1])/2)
        if abs(P[0]-Q[0]) < 1e-5:
            slope = 0
        else:
            m = (Q[1]-P[1])/(Q[0]-P[0])
            slope = None if abs(m) < 1e-5 else -1/m
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
    def altitud(P, Q, R):
        if abs(Q[0]-R[0]) < 1e-5:
            m_alt = 0
        else:
            m_qr = (R[1]-Q[1])/(R[0]-Q[0])
            m_alt = None if abs(m_qr) < 1e-5 else -1/m_qr
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
    plt.plot([A_point[0], B_point[0]], [A_point[1], B_point[1]], 'b-', label=f"Lado c = {c:.2f}")
    plt.plot([A_point[0], C_point[0]], [A_point[1], C_point[1]], 'r-', label=f"Lado b = {b:.2f}")
    plt.plot([B_point[0], C_point[0]], [B_point[1], C_point[1]], 'g-', label=f"Lado a = {a:.2f}")
    mAB = ((A_point[0]+B_point[0])/2, (A_point[1]+B_point[1])/2)
    mAC = ((A_point[0]+C_point[0])/2, (A_point[1]+C_point[1])/2)
    mBC = ((B_point[0]+C_point[0])/2, (B_point[1]+C_point[1])/2)
    plt.plot([C_point[0], mAB[0]], [C_point[1], mAB[1]], 'm--', label="Medianas")
    plt.plot([B_point[0], mAC[0]], [B_point[1], mAC[1]], 'm--')
    plt.plot([A_point[0], mBC[0]], [A_point[1], mBC[1]], 'm--')
    circumcenter, ortocenter, _, _, _ = calcular_puntos_notables(a, b, c, A, B, C)
    plt.plot(circumcenter[0], circumcenter[1], 'ko', label="Circuncentro")
    plt.plot(ortocenter[0], ortocenter[1], 'ks', label="Ortocentro")
    plt.text(A_point[0]-0.2, A_point[1]-0.2, "A", fontsize=12)
    plt.text(B_point[0]+0.2, B_point[1]-0.2, "B", fontsize=12)
    plt.text(C_point[0], C_point[1]+0.2, "C", fontsize=12)
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
# Rutas y funcionalidades adicionales
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
            altura_val = get_val("altura")
            area_val = get_val("area")
            metodo_sel = request.form.get("metodo_sel", "auto")
            
            if metodo_sel == "altura":
                res = resolver_triangulo_altura(a_val, altura_val, area_val)
                resultados = {
                    'base': res['base'],
                    'altura': res['altura'],
                    'area': res['area']
                }
                return render_template("resultado.html", resultados=resultados, imagen_est=None, imagen_int=None)
            else:
                res, metodo = resolver_triangulo(a_val, b_val, c_val, A_val, B_val, C_val, metodo_sel)
                perimetro = res[0] + res[1] + res[2]
                s = perimetro / 2
                area = math.sqrt(s * (s - res[0]) * (s - res[1]) * (s - res[2]))
                altura_tri = (2 * area) / res[2] if res[2] != 0 else None
                mediana_a, mediana_b, mediana_c = calcular_medianas(res[0], res[1], res[2])
                circumradius = calcular_circumradius(res[0], res[1], res[2], area)
                tipo_tri = determinar_tipo_triangulo(res[0], res[1], res[2])
                clasif_ang = clasificar_triangulo_por_angulo(res[3], res[4], res[5])
                imagen_est = graficar_triangulo_estatico(res[0], res[1], res[2], res[3], res[4], res[5])
                imagen_int = graficar_triangulo_interactivo(res[0], res[1], res[2], res[3], res[4], res[5])
                resultados = {
                    'lado_a': res[0],
                    'lado_b': res[1],
                    'lado_c': res[2],
                    'angulo_A': res[3],
                    'angulo_B': res[4],
                    'angulo_C': res[5],
                    'perimetro': perimetro,
                    'area': area,
                    'altura': altura_tri if altura_tri is not None else "N/A",
                    'mediana_a': mediana_a,
                    'mediana_b': mediana_b,
                    'mediana_c': mediana_c,
                    'circumradius': circumradius if circumradius is not None else "N/A",
                    'tipo_triangulo': tipo_tri,
                    'clasificacion': clasif_ang,
                    'pitagoras': "",
                    'metodo': "🏧 Ley de Senos o Cosenos"
                }
                return render_template("resultado.html", resultados=resultados, imagen_est=imagen_est, imagen_int=imagen_int)
        except Exception as e:
            flash(str(e))
            return redirect(url_for('index'))
    return render_template("index.html", resultados=None)

@app.route('/donar')
def donar():
    return render_template("donar.html")

@app.route('/reporte', methods=['GET', 'POST'])
def reporte():
    if request.method == 'POST':
        email = request.form.get('email')
        mensaje = request.form.get('mensaje')
        asunto = "Reporte de error desde Instant Math Solver: Triángulos"
        cuerpo = f"Reporte de: {email}\n\nMensaje:\n{mensaje}"
        msg = MIMEText(cuerpo)
        msg['Subject'] = asunto
        msg['From'] = SMTP_USER
        msg['To'] = SMTP_USER
        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            flash("Reporte enviado correctamente. ¡Gracias por tus comentarios!")
        except Exception as e:
            flash("Error al enviar reporte: " + str(e))
        return redirect(url_for('reporte'))
    return render_template("reporte.html")

if __name__ == "__main__":
    app.run(debug=True)

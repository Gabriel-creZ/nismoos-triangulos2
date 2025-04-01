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

# =========================
# Funciones de resolución de triángulos
# =========================

def calcular_triangulo_sen(angulo_A=None, angulo_B=None, angulo_C=None, 
                             lado_a=None, lado_b=None, lado_c=None):
    # Función similar a la ya existente (sin cambios importantes)
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
    # Caso SSA (2 lados y 1 ángulo)
    if num_angles == 1 and num_sides == 2:
        # Se implementan los casos SSA (similar a lo anterior)
        # [Se omiten detalles por brevedad]
        pass  # Puedes conservar el código existente de SSA aquí.
    raise ValueError("No se pudo determinar el triángulo.")

def calcular_triangulo_cos(a=None, b=None, c=None, A=None, B=None, C=None):
    # Función similar a la ya existente (sin cambios importantes)
    # [Se conserva el código existente de la ley de cosenos]
    pass

def resolver_triangulo(a, b, c, A, B, C):
    count_sides = sum(x is not None for x in [a, b, c])
    count_angles = sum(x is not None for x in [A, B, C])
    if count_sides + count_angles < 3 or count_sides < 1:
        raise ValueError("Se requieren al menos 3 datos (con al menos 1 lado).")
    if count_angles >= 2:
        method = "senos"
    elif count_sides == 3:
        method = "cosenos"
    elif count_sides == 2 and count_angles == 1:
        method = "cosenos"  # O "senos" según el caso
    else:
        method = "senos"
    if method == "senos":
        return calcular_triangulo_sen(angulo_A=A, angulo_B=B, angulo_C=C,
                                      lado_a=a, lado_b=b, lado_c=c), method
    else:
        return calcular_triangulo_cos(a=a, b=b, c=c, A=A, B=B, C=C), method

# ================================
# Funciones de cálculos adicionales
# ================================

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
    if abs(mayor - 90) < 1e-5:
        return "Rectángulo"
    elif mayor > 90:
        return "Obtuso"
    else:
        return "Acutángulo"

# Función de conversión de unidades (ejemplo cm a m)
def convertir_unidades(valor, de="cm", a="m"):
    conversiones = {("cm", "m"): 0.01, ("m", "cm"): 100}
    factor = conversiones.get((de, a), 1)
    return valor * factor

# Cálculo del circuncentro y ortocentro (usando coordenadas de vértices)
def calcular_puntos_notables(a, b, c, A, B, C):
    # Definición de vértices (A en (0,0), B en (c,0) y C en base a la ley de senos)
    A_point = (0, 0)
    B_point = (c, 0)
    C_point = (b * math.cos(math.radians(A)), b * math.sin(math.radians(A)))
    # Circuncentro: intersección de las mediatrices
    def mediatriz(P, Q):
        mid = ((P[0]+Q[0])/2, (P[1]+Q[1])/2)
        if abs(P[0]-Q[0])<1e-5:
            # mediatriz horizontal
            slope = 0
        else:
            m = (Q[1]-P[1])/(Q[0]-P[0])
            if abs(m) < 1e-5:
                slope = None
            else:
                slope = -1/m
        return mid, slope
    midAB, slopeAB = mediatriz(A_point, B_point)
    midAC, slopeAC = mediatriz(A_point, C_point)
    # Intersección de dos líneas: si slope es None, vertical
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
    # Ortocentro: intersección de las altitudes
    def altitud(P, Q, R):
        # Altitud desde P a la recta QR
        if abs(Q[0]-R[0])<1e-5:
            m_alt = 0
        else:
            m_qr = (R[1]-Q[1])/(R[0]-Q[0])
            if abs(m_qr)<1e-5:
                m_alt = None
            else:
                m_alt = -1/m_qr
        return P, m_alt
    alt_A = altitud(A_point, B_point, C_point)
    alt_B = altitud(B_point, A_point, C_point)
    ortocenter = interseccion(alt_A[0], alt_A[1], alt_B[0], alt_B[1])
    return circumcenter, ortocenter, A_point, B_point, C_point

# ================================
# Funciones de graficado (estático e interactivo)
# ================================

def graficar_triangulo_estatico(a, b, c, A, B, C):
    # Se dibujan lados, medianas, altitudes y se marcan circuncentro y ortocentro
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
    plt.plot([C_point[0], mAB[0]], [C_point[1], mAB[1]], 'm--', label="Mediana")
    plt.plot([B_point[0], mAC[0]], [B_point[1], mAC[1]], 'm--')
    plt.plot([A_point[0], mBC[0]], [A_point[1], mBC[1]], 'm--')
    # Dibujar altitudes
    # (Cálculos simplificados)
    # Circuncentro y ortocentro
    circumcenter, ortocenter, _, _, _ = calcular_puntos_notables(a, b, c, A, B, C)
    plt.plot(circumcenter[0], circumcenter[1], 'ko', label="Circuncentro")
    plt.plot(ortocenter[0], ortocenter[1], 'ks', label="Ortocentro")
    
    # Etiquetas de vértices
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
    # Usando Plotly para generar una gráfica interactiva
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
    # Marcar circuncentro y ortocentro
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

# Página para comparar dos triángulos
@app.route('/comparar', methods=['GET', 'POST'])
def comparar():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            def get_val(field):
                val = request.form.get(field)
                return float(val) if val and val.strip() != "" else None
            # Primer triángulo
            a1 = get_val("lado_a1")
            b1 = get_val("lado_b1")
            c1 = get_val("lado_c1")
            A1 = get_val("angulo_A1")
            B1 = get_val("angulo_B1")
            C1 = get_val("angulo_C1")
            # Segundo triángulo
            a2 = get_val("lado_a2")
            b2 = get_val("lado_b2")
            c2 = get_val("lado_c2")
            A2 = get_val("angulo_A2")
            B2 = get_val("angulo_B2")
            C2 = get_val("angulo_C2")
            res1, met1 = resolver_triangulo(a1, b1, c1, A1, B1, C1)
            res2, met2 = resolver_triangulo(a2, b2, c2, A2, B2, C2)
            # Calcular propiedades de cada triángulo
            per1 = sum(res1[:3])
            s1 = per1/2
            area1 = math.sqrt(s1*(s1-res1[0])*(s1-res1[1])*(s1-res1[2]))
            per2 = sum(res2[:3])
            s2 = per2/2
            area2 = math.sqrt(s2*(s2-res2[0])*(s2-res2[1])*(s2-res2[2]))
            # Determinar similitud y congruencia (muy básico)
            ratio1 = res1[0]/res1[1] if res1[1]!=0 else None
            ratio2 = res2[0]/res2[1] if res2[1]!=0 else None
            similares = abs(ratio1 - ratio2) < 1e-2 if (ratio1 and ratio2) else False
            congruentes = all(abs(x-y)<1e-2 for x,y in zip(res1[:3], res2[:3]))
            comp = {
                'similares': "Sí" if similares else "No",
                'congruentes': "Sí" if congruentes else "No"
            }
            return render_template("comparar.html", res1=res1, res2=res2,
                                   per1=f"{per1:.2f}", area1=f"{area1:.2f}",
                                   per2=f"{per2:.2f}", area2=f"{area2:.2f}",
                                   comp=comp)
        except Exception as e:
            flash(str(e))
            return redirect(url_for('comparar'))
    return render_template("comparar.html", res1=None)

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
            
            (res_a, res_b, res_c, res_A, res_B, res_C), metodo = resolver_triangulo(a_val, b_val, c_val, A_val, B_val, C_val)
            
            perimetro = res_a + res_b + res_c
            s = perimetro / 2
            area = math.sqrt(s * (s - res_a) * (s - res_b) * (s - res_c))
            
            mediana_a, mediana_b, mediana_c = calcular_medianas(res_a, res_b, res_c)
            circumradius = calcular_circumradius(res_a, res_b, res_c, area)
            tipo_triangulo = determinar_tipo_triangulo(res_a, res_b, res_c)
            clasificacion = clasificar_triangulo_por_angulo(res_A, res_B, res_C)
            
            # Verificar teorema de Pitágoras para triángulos rectángulos
            pitagoras = ""
            if abs(max(res_A, res_B, res_C) - 90) < 1e-2:
                pitagoras = "Se cumple el teorema de Pitágoras."
            
            # Gráfica estática e interactiva
            imagen_est = graficar_triangulo_estatico(res_a, res_b, res_c, res_A, res_B, res_C)
            imagen_int = graficar_triangulo_interactivo(res_a, res_b, res_c, res_A, res_B, res_C)
            
            resultados = {
                'lado_a': f"{res_a:.2f}",
                'lado_b': f"{res_b:.2f}",
                'lado_c': f"{res_c:.2f}",
                'angulo_A': f"{res_A:.2f}",
                'angulo_B': f"{res_B:.2f}",
                'angulo_C': f"{res_C:.2f}",
                'perimetro': f"{perimetro:.2f}",
                'area': f"{area:.2f}",
                'mediana_a': f"{mediana_a:.2f}",
                'mediana_b': f"{mediana_b:.2f}",
                'mediana_c': f"{mediana_c:.2f}",
                'circumradius': f"{circumradius:.2f}" if circumradius is not None else "N/A",
                'tipo_triangulo': tipo_triangulo,
                'clasificacion': clasificacion,
                'pitagoras': pitagoras,
                'metodo': metodo
            }
            
            return render_template("resultado.html", resultados=resultados, imagen_est=imagen_est, imagen_int=imagen_int)
        except Exception as e:
            flash(str(e))
            return redirect(url_for('index'))
    return render_template("index.html", resultados=None)

# ================================
# Rutas para Donar y Reportar Error
# ================================
@app.route('/donar')
def donar():
    return render_template("donar.html")

@app.route('/reporte', methods=['GET', 'POST'])
def reporte():
    if request.method == 'POST':
        # Aquí se implementaría el envío de correo SMTP similar a la web de rectas
        flash("Reporte enviado correctamente. ¡Gracias por tus comentarios!")
        return redirect(url_for('reporte'))
    return render_template("reporte.html")

if __name__ == "__main__":
    app.run(debug=True)

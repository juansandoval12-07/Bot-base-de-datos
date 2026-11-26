import streamlit as st
import pandas as pd

st.set_page_config(page_title="TechBot - Asistente de Ventas", page_icon="🛒", layout="wide")

# ---------------------------------------------------------------
# 1. Catálogo de productos (puedes cambiarlo por el de tu negocio)
# ---------------------------------------------------------------
CATALOGO = [
    {"id": 1, "nombre": "Laptop Lenovo IdeaPad 15", "categoria": "laptop", "precio": 2200000, "desc": "Intel i5, 16GB RAM, SSD 512GB. Ideal para estudio y oficina."},
    {"id": 2, "nombre": "Laptop Asus TUF Gaming", "categoria": "laptop", "precio": 3800000, "desc": "Ryzen 7, 16GB RAM, RTX 3050. Para gaming y diseño."},
    {"id": 3, "nombre": "Smartphone Samsung Galaxy A55", "categoria": "celular", "precio": 1500000, "desc": "128GB, cámara de 50MP, batería de 5000 mAh."},
    {"id": 4, "nombre": "Smartphone Xiaomi Redmi Note 13", "categoria": "celular", "precio": 900000, "desc": "128GB, pantalla AMOLED. Excelente relación precio-calidad."},
    {"id": 5, "nombre": "Audífonos Sony WH-CH520", "categoria": "audio", "precio": 250000, "desc": "Bluetooth, 50 horas de batería."},
    {"id": 6, "nombre": "Mouse Logitech M170", "categoria": "accesorio", "precio": 45000, "desc": "Inalámbrico, compacto y duradero."},
    {"id": 7, "nombre": "Teclado Redragon Kumara", "categoria": "accesorio", "precio": 160000, "desc": "Mecánico, retroiluminado, formato compacto."},
    {"id": 8, "nombre": "Monitor LG 24'' Full HD", "categoria": "monitor", "precio": 520000, "desc": "IPS, 75Hz, ideal para trabajar y estudiar."},
]
CUPONES = {"UFPS10": 0.10, "TECH15": 0.15}


def cop(valor):
    return "${:,.0f}".format(valor).replace(",", ".")


def catalogo_texto():
    return "\n".join(
        f"- {p['nombre']} | {p['categoria']} | {cop(p['precio'])} | {p['desc']}" for p in CATALOGO
    )


# ---------------------------------------------------------------
# 2. Estado de la sesión
# ---------------------------------------------------------------
if "mensajes" not in st.session_state:
    st.session_state.mensajes = [
        {"role": "assistant", "content": "¡Hola! Soy TechBot 🤖. Cuéntame qué necesitas (laptop, celular, accesorios...) y tu presupuesto, y te ayudo a elegir."}
    ]
if "carrito" not in st.session_state:
    st.session_state.carrito = {}  # id -> cantidad


# ---------------------------------------------------------------
# 3. Cerebro del agente
# ---------------------------------------------------------------
def carrito_texto():
    if not st.session_state.carrito:
        return "El carrito está vacío."
    lineas = []
    for pid, cant in st.session_state.carrito.items():
        p = next(x for x in CATALOGO if x["id"] == pid)
        lineas.append(f"{cant} x {p['nombre']}")
    return ", ".join(lineas)


def sistema_prompt():
    return f"""Eres TechBot, un asistente de ventas amable de una tienda de tecnología en Colombia.
Tu tarea: ayudar al cliente a elegir productos del catálogo, comparar opciones y resolver dudas.
Reglas:
- Responde SOLO con productos del catálogo. Si no existe, dilo con honestidad.
- Precios en pesos colombianos (COP). No inventes precios ni características.
- Sé breve (máximo 120 palabras) y recomienda según presupuesto y necesidad.
- Si el cliente decide comprar, indícale que use el botón "Agregar" del catálogo en la barra lateral.
- Cupones disponibles: UFPS10 (10%) y TECH15 (15%), se aplican en el carrito.

CATÁLOGO:
{catalogo_texto()}

CARRITO ACTUAL: {carrito_texto()}"""


def respuesta_local(pregunta):
    """Modo de respaldo sin API: busca productos por palabras clave."""
    q = pregunta.lower()
    claves = {
        "laptop": ["laptop", "portatil", "portátil", "computador", "pc"],
        "celular": ["celular", "smartphone", "telefono", "teléfono", "movil", "móvil"],
        "audio": ["audifono", "audífono", "audio", "sonido"],
        "accesorio": ["mouse", "teclado", "accesorio"],
        "monitor": ["monitor", "pantalla"],
    }
    cats = [c for c, palabras in claves.items() if any(w in q for w in palabras)]
    if "cupon" in q or "cupón" in q or "descuento" in q:
        return "Tenemos los cupones **UFPS10** (10%) y **TECH15** (15%). Aplícalos en el carrito 🛒"
    if not cats:
        return "Puedo ayudarte con laptops, celulares, audífonos, monitores y accesorios. ¿Qué buscas y cuál es tu presupuesto?"
    items = [p for p in CATALOGO if p["categoria"] in cats]
    return "Estas opciones pueden servirte:\n\n" + "\n".join(
        f"- **{p['nombre']}** ({cop(p['precio'])}): {p['desc']}" for p in items
    )


def responder(pregunta):
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        api_key = None
    if not api_key:
        return respuesta_local(pregunta)
    try:
        from groq import Groq

        client = Groq(api_key=api_key)
        msgs = [{"role": "system", "content": sistema_prompt()}]
        msgs += [{"role": m["role"], "content": m["content"]} for m in st.session_state.mensajes[-10:]]
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile", messages=msgs, temperature=0.4, max_tokens=400
        )
        return r.choices[0].message.content
    except Exception as e:
        return respuesta_local(pregunta) + f"\n\n_(Modo local activado: {type(e).__name__})_"


# ---------------------------------------------------------------
# 4. Barra lateral: catálogo + carrito (funcionalidad adicional)
# ---------------------------------------------------------------
with st.sidebar:
    st.header("🛍️ Catálogo")
    for p in CATALOGO:
        st.markdown(f"**{p['nombre']}**  \n{cop(p['precio'])}")
        if st.button("Agregar", key=f"add_{p['id']}"):
            st.session_state.carrito[p["id"]] = st.session_state.carrito.get(p["id"], 0) + 1
            st.rerun()

st.title("🛒 TechBot - Asistente de Ventas")
st.caption("Agente de IA que te asesora en la compra de tecnología y arma tu cotización.")

col_chat, col_carrito = st.columns([3, 2])

# ---------------- Chat ----------------
with col_chat:
    for m in st.session_state.mensajes:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if pregunta := st.chat_input("Escribe tu pregunta, ej: ¿qué laptop me recomiendas para estudiar?"):
        st.session_state.mensajes.append({"role": "user", "content": pregunta})
        with st.chat_message("user"):
            st.markdown(pregunta)
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                texto = responder(pregunta)
            st.markdown(texto)
        st.session_state.mensajes.append({"role": "assistant", "content": texto})

# ---------------- Carrito ----------------
with col_carrito:
    st.subheader("🧾 Tu carrito")
    if not st.session_state.carrito:
        st.info("Aún no has agregado productos.")
    else:
        filas, subtotal = [], 0
        for pid, cant in st.session_state.carrito.items():
            p = next(x for x in CATALOGO if x["id"] == pid)
            total = p["precio"] * cant
            subtotal += total
            filas.append({"Producto": p["nombre"], "Cant.": cant, "Total": cop(total)})
        st.table(pd.DataFrame(filas))

        cupon = st.text_input("Cupón de descuento").strip().upper()
        descuento = CUPONES.get(cupon, 0)
        if cupon and descuento:
            st.success(f"Cupón aplicado: {int(descuento * 100)}% de descuento")
        elif cupon:
            st.warning("Cupón no válido")
        valor_desc = subtotal * descuento
        total_final = subtotal - valor_desc

        st.write(f"Subtotal: **{cop(subtotal)}**")
        st.write(f"Descuento: **-{cop(valor_desc)}**")
        st.markdown(f"### Total: {cop(total_final)}")

        cotizacion = "COTIZACIÓN TECHBOT\n" + "-" * 30 + "\n"
        for f in filas:
            cotizacion += f"{f['Cant.']} x {f['Producto']} = {f['Total']}\n"
        cotizacion += f"\nSubtotal: {cop(subtotal)}\nDescuento: -{cop(valor_desc)}\nTOTAL: {cop(total_final)}\n"

        c1, c2 = st.columns(2)
        c1.download_button("📥 Descargar cotización", cotizacion, file_name="cotizacion.txt")
        if c2.button("🗑️ Vaciar carrito"):
            st.session_state.carrito = {}
            st.rerun()
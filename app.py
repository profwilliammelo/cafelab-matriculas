import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import plotly.express as px
from faker import Faker
import random
import os

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="NAVE LÚCIO THOME | Dashboard", page_icon="🚀")

# ==============================================================================
# 🎨 1. TEMA E CSS (ALTO CONTRASTE NUCLEAR + GAMIFICAÇÃO DE FORMULÁRIO)
# ==============================================================================
# Este bloco garante que textos sejam sempre visíveis, independente do tema do navegador.

if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'  # DEFINIDO COMO PADRÃO: DARK

def toggle_theme():
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

# Definição das Paletas de Cores
themes = {
    "light": {
        "bg": "#FFFFFF",          # Branco Absoluto
        "card_bg": "#F3F4F6",     # Cinza muito claro
        "text": "#000000",        # Preto Puro (Contraste Máximo)
        "text_secondary": "#1F2937", 
        "primary": "#BE185D",     # Magenta
        "secondary": "#9D174D",   # Bordô
        "border": "#D1D5DB",      
        "chart_colors": ["#BE185D", "#111827", "#B45309", "#047857", "#6D28D9"],
        "hover_bg": "#FCE7F3",    # Cor de fundo ao passar o mouse
        "input_bg": "#FFFFFF",    # Fundo explícito para inputs
        "expander_header": "#E5E7EB" # Cor de fundo do cabeçalho do expander
    },
    "dark": {
        "bg": "#121212",          # Preto Quase Puro
        "card_bg": "#1E1E1E",     
        "text": "#FFFFFF",        
        "text_secondary": "#E5E7EB",
        "primary": "#FF69B4",     # Hot Pink
        "secondary": "#FFD700",   # Gold
        "border": "#374151",
        "chart_colors": ["#FF69B4", "#FFD700", "#34D399", "#A78BFA", "#60A5FA"],
        "hover_bg": "#374151",    # Cor de fundo ao passar o mouse
        "input_bg": "#2D2D2D",    # Fundo explícito para inputs
        "expander_header": "#374151" # Cor de fundo do cabeçalho do expander
    }
}

current_theme = themes[st.session_state.theme]

# Injeção de CSS com !important para sobrescrever padrões do Streamlit
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

    /* Reset Global */
    html, body, .stApp {{
        font-family: 'Poppins', sans-serif !important;
        background-color: {current_theme['bg']} !important;
        color: {current_theme['text']} !important;
    }}
    
    /* FORÇA A COR DOS TEXTOS PARA EVITAR "INVISIBILIDADE" */
    h1, h2, h3, h4, h5, h6, .stHeading {{
        color: {current_theme['text']} !important;
        font-weight: 700 !important;
    }}
    
    p, div, span, label, li, .stMarkdown, .stText {{
        color: {current_theme['text']} !important;
    }}

    /* Título com Gradiente */
    h1 {{
        background: linear-gradient(135deg, #BE185D 0%, #9D174D 100%);
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }}
    
    /* Cards e Containers */
    .metric-card, .filter-box {{
        background-color: {current_theme['card_bg']} !important;
        border: 1px solid {current_theme['border']} !important;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        padding: 20px;
    }}

    /* --- CORREÇÃO CRÍTICA: INPUTS, SELECTBOX E MULTISELECT --- */
    
    /* Input de Texto e Números */
    .stTextInput input, .stNumberInput input, .stDateInput input {{
        background-color: {current_theme['input_bg']} !important;
        color: {current_theme['text']} !important;
        border: 1px solid {current_theme['border']} !important;
    }}

    /* Selectbox e Multiselect (O container fechado) */
    div[data-baseweb="select"] > div {{
        background-color: {current_theme['input_bg']} !important;
        color: {current_theme['text']} !important;
        border-color: {current_theme['border']} !important;
    }}
    
    /* Texto dentro do Selectbox */
    div[data-baseweb="select"] span {{
        color: {current_theme['text']} !important;
    }}
    
    /* Ícone de seta do dropdown */
    div[data-baseweb="select"] svg {{
        fill: {current_theme['text']} !important;
    }}

    /* Menu Dropdown (Quando aberto - As opções) */
    ul[data-baseweb="menu"] {{
        background-color: {current_theme['card_bg']} !important;
    }}
    
    /* Itens da lista do Dropdown */
    li[data-baseweb="option"] {{
        color: {current_theme['text']} !important;
    }}

    /* --- CORREÇÃO CRÍTICA: BOTÃO DE REGISTRAR --- */
    
    /* Força o background do botão no estado normal */
    div[data-testid="stButton"] > button {{
        background-color: {current_theme['primary']} !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        opacity: 1 !important; /* Garante que não fique transparente */
        box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
    }}
    
    /* Garante que o texto DENTRO do botão seja branco */
    div[data-testid="stButton"] > button p {{
        color: white !important;
    }}
    
    /* Estado Hover do botão */
    div[data-testid="stButton"] > button:hover {{
        background-color: {current_theme['secondary']} !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.3) !important;
    }}
    
    /* --- CORREÇÃO CRÍTICA: EXPANDERS (SUBTÍTULOS) --- */
    
    /* Cabeçalho do Expander (A "faixa") */
    div[data-testid="stExpander"] > details > summary {{
        background-color: {current_theme['expander_header']} !important;
        border: 1px solid {current_theme['border']} !important;
        border-radius: 8px;
        color: {current_theme['text']} !important;
    }}
    
    /* Texto dentro do cabeçalho do Expander */
    div[data-testid="stExpander"] > details > summary span {{
        color: {current_theme['text']} !important;
        font-weight: 600 !important;
    }}
    
    /* Hover no Expander */
    div[data-testid="stExpander"] > details > summary:hover {{
        background-color: {current_theme['hover_bg']} !important;
        color: {current_theme['primary']} !important;
    }}
    
    div[data-testid="stExpander"] > details > summary:hover span {{
        color: {current_theme['primary']} !important;
    }}
    
    /* Conteúdo interno do Expander */
    div[data-testid="stExpander"] > details > div {{
        border-left: 2px solid {current_theme['border']};
        border-right: 2px solid {current_theme['border']};
        border-bottom: 2px solid {current_theme['border']};
        border-bottom-left-radius: 8px;
        border-bottom-right-radius: 8px;
        padding: 15px;
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: {current_theme['card_bg']} !important;
        border-right: 1px solid {current_theme['border']} !important;
    }}

</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🔧 2. BACKEND E DADOS
# ==============================================================================

PASSWORD = "NAVE2026"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# Coordenadas aproximadas dos bairros de Maricá para o Mapa
COORDENADAS_BAIRROS = {
    "Araçatiba": {"lat": -22.9275, "lon": -42.8098}, "Bambuí": {"lat": -22.9231, "lon": -42.7482},
    "Barra de Maricá": {"lat": -22.9567, "lon": -42.8374}, "Boqueirão": {"lat": -22.9224, "lon": -42.8336},
    "Centro": {"lat": -22.9194, "lon": -42.8183}, "Cordeirinho": {"lat": -22.9602, "lon": -42.7561},
    "Inoã": {"lat": -22.9188, "lon": -42.8712}, "Itaipuaçu": {"lat": -22.9658, "lon": -42.9242},
    "Itapeba": {"lat": -22.9080, "lon": -42.8300}, "Ponta Negra": {"lat": -22.9610, "lon": -42.6930},
    "São José do Imbassaí": {"lat": -22.9380, "lon": -42.8440}, "Ubatiba": {"lat": -22.8800, "lon": -42.7900}
}
BAIRROS_MARICA = sorted(list(COORDENADAS_BAIRROS.keys()))

def login():
    st.markdown("### 🔒 Acesso Restrito NAVE")
    senha = st.text_input("Digite a senha de acesso:", type="password")
    if st.button("Logar no Sistema"):
        if senha == PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Senha incorreta!")

def get_spreadsheet_object():
    try:
        if "gsheets" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gsheets"], SCOPES)
        else:
            # Fallback para uso local
            creds = ServiceAccountCredentials.from_json_keyfile_name("rwilliammelo-7509a86c9df0.json", SCOPES)
        client = gspread.authorize(creds)
        # ID da Planilha Google
        return client.open_by_key("1lKH8BrZ0LVi_tufuv9_kEeOhJGLueSQahh-6Ft1_idA")
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        return None

def save_data(sh, tab_name, data):
    try:
        worksheet = sh.worksheet(tab_name)
        worksheet.append_row(data)
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    return st.session_state.password_correct

@st.cache_data(ttl=60)
def load_data_cached(tab_name):
    # R: dados <- read_sheet("url", sheet = tab_name)
    sh = get_spreadsheet_object()
    if not sh: return pd.DataFrame()
    try:
        worksheet = sh.worksheet(tab_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

# Lógica do INSE (Indicador Nível Socioeconômico)
def calcular_inse(escolaridade1, escolaridade2, bens, banheiros, qtd_pessoas):
    # R: Lógica equivalente seria feita com `case_when` e somas ponderadas
    pontos = 0
    mapa_escolaridade = {
        "Não alfabetizado": 0, "Fundamental Incompleto": 1, "Fundamental Completo": 2,
        "Médio Incompleto": 3, "Médio Completo": 4, "Superior Incompleto": 5, "Superior Completo": 6,
        "Não informado": 0 # Tratando a opção "sem resposta"
    }
    pontos += mapa_escolaridade.get(escolaridade1, 0) * 2
    if escolaridade2: pontos += mapa_escolaridade.get(escolaridade2, 0)
    
    if isinstance(bens, str): lista_bens = bens.split(",")
    elif isinstance(bens, list): lista_bens = bens
    else: lista_bens = []
        
    pontos += len(lista_bens)
    pontos += int(banheiros) * 2
    if "Carro" in lista_bens: pontos += 3
    if "Computador/Notebook" in lista_bens: pontos += 2
    
    classificacao = ""
    if pontos <= 5: classificacao = "Baixo"
    elif pontos <= 10: classificacao = "Médio-Baixo"
    elif pontos <= 18: classificacao = "Médio"
    elif pontos <= 25: classificacao = "Médio-Alto"
    else: classificacao = "Alto"
    return pontos, classificacao

def agrupar_raca(df):
    """
    Cria uma nova coluna agrupando Pretos e Pardos.
    R: df <- df %>% mutate(raca_grupo = if_else(raca %in% c("Preta", "Parda"), "Negra (Preta+Parda)", raca))
    """
    if 'raca' not in df.columns: return df
    df['raca_grupo'] = df['raca'].apply(lambda x: "Negra (Preta+Parda)" if x in ["Preta", "Parda"] else x)
    return df

def generate_fake_data(sh, qtd=10):
    fake = Faker('pt_BR')
    rows_novas, rows_rematriculas = [], []
    
    for _ in range(qtd):
        tipo = random.choice(["Nova", "Rematricula"])
        esc1 = random.choice(["Fundamental Completo", "Médio Completo", "Superior Completo"])
        esc2 = random.choice(["", "Fundamental Completo", "Médio Completo"])
        bens_lista = random.sample(["TV", "Geladeira", "Máquina de Lavar", "Carro", "Computador/Notebook", "Internet Wifi", "Ar Condicionado"], k=random.randint(1, 7))
        bens_str = ", ".join(bens_lista)
        banheiros = random.randint(1, 3)
        qtd_pessoas = random.randint(2, 7)
        pontos, inse_class = calcular_inse(esc1, esc2, bens_lista, banheiros, qtd_pessoas)
        bairro_escolhido = random.choice(BAIRROS_MARICA)
        raca_fake = random.choice(["Branca", "Preta", "Parda", "Indígena"])

        dados_comuns_inicio = [
            fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S"),
            fake.name(), str(fake.date_of_birth(minimum_age=6, maximum_age=15)),
            fake.name(), str(fake.date_of_birth(minimum_age=25, maximum_age=60)),
            random.choice(["Mãe", "Pai", "Avó"]), fake.phone_number(), fake.email(),
            fake.street_name(), fake.building_number(), bairro_escolhido, "Maricá", fake.postcode(),
            f"{random.randint(1, 9)}º Ano", random.choice(["Manhã", "Tarde"])
        ]
        
        # IMPORTANTE: A ordem aqui deve bater EXATAMENTE com as colunas da planilha
        dados_comuns_fim = [
            random.choice(["Sim", "Não"]), raca_fake, random.choice(["Masculino", "Feminino"]),
            esc1, esc2, qtd_pessoas, banheiros, bens_str,
            random.choice(["0-10", "11-50", "Mais de 100"]), random.choice(["Sim", "Não"]),
            pontos, inse_class,
            random.choice(["Nunca", "Às vezes", "Sempre"]), # p1
            random.choice(["Nunca", "Às vezes", "Sempre"]), # p2
            random.choice(["Raramente", "Semanalmente", "Diariamente"]), # p3
            random.choice(["Raramente", "Semanalmente", "Diariamente"]), # p4
            random.choice(["Raramente", "Semanalmente", "Diariamente"])  # p5
        ]
        
        if tipo == "Nova":
            # Inclui coluna "escola_origem"
            rows_novas.append(dados_comuns_inicio + [f"Escola {fake.last_name()}"] + dados_comuns_fim)
        else:
            # Inclui coluna "turma_anterior"
            rows_rematriculas.append(dados_comuns_inicio + [f"7{random.randint(10, 99)}"] + dados_comuns_fim)
            
    if rows_novas: sh.worksheet("Novas_Matriculas").append_rows(rows_novas)
    if rows_rematriculas: sh.worksheet("Rematriculas").append_rows(rows_rematriculas)
    st.cache_data.clear()

# ==============================================================================
# 📊 3. FUNÇÕES DE VISUALIZAÇÃO (AUTOMATIZADAS)
# ==============================================================================

def gamified_card(title, value, icon, color_key):
    color = current_theme.get(color_key, current_theme['primary'])
    st.markdown(f"""
    <div class="metric-card" style="border-left: 5px solid {color};">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom: 5px;">
            <span style="font-size: 1.5rem;">{icon}</span>
            <span style="font-size: 0.9rem; font-weight:600; text-transform: uppercase; color:{current_theme['text_secondary']}">{title}</span>
        </div>
        <p style="font-size: 2rem; font-weight: 800; margin:0; color: {current_theme['text']};">{value}</p>
    </div>
    """, unsafe_allow_html=True)

def apply_theme_plotly(fig):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': current_theme['text'], 'family': 'Poppins, sans-serif'},
        title_font={'size': 18, 'color': current_theme['text'], 'family': 'Poppins, sans-serif', 'weight': 700},
        # CORREÇÃO: Forçar cor do título da legenda para preto/contraste alto
        legend={
            'font': {'color': current_theme['text']}, 
            'bgcolor': 'rgba(0,0,0,0)',
            'title': {'font': {'color': current_theme['text']}}  # Garante título da legenda visível
        },
        xaxis={'tickfont': {'color': current_theme['text_secondary']}, 'title_font': {'color': current_theme['text']}, 'gridcolor': current_theme['border']},
        yaxis={'tickfont': {'color': current_theme['text_secondary']}, 'title_font': {'color': current_theme['text']}, 'gridcolor': current_theme['border']}
    )
    return fig

def plot_analise_completa(df, coluna, titulo, ordem=None):
    """
    Gera automaticamente:
    1. Gráfico Univariado (Total - Contagem Absoluta)
    2. Gráfico Bivariado (Perfil Racial - % dentro do grupo)
    """
    if coluna not in df.columns:
        st.warning(f"Coluna {coluna} não encontrada nos dados.")
        return

    st.markdown(f"#### {titulo}")
    
    # Ordenação
    if ordem:
        # Adiciona "Não informado" se ele existir nos dados, mas não estiver na ordem padrão
        if "Não informado" in df[coluna].unique() and "Não informado" not in ordem:
             ordem.append("Não informado")

        cat_existentes = [x for x in ordem if x in df[coluna].unique()]
        if cat_existentes:
            df[coluna] = pd.Categorical(df[coluna], categories=cat_existentes, ordered=True)
            df = df.sort_values(coluna)

    c1, c2 = st.columns(2)
    
    # Gráfico 1: Univariado (Contagem Simples)
    with c1:
        df_uni = df[coluna].value_counts().reset_index()
        df_uni.columns = [coluna, 'count']
        fig1 = px.bar(df_uni, x=coluna, y='count', text_auto=True, title=f"Total Absoluto: {titulo}",
                      color_discrete_sequence=[current_theme['chart_colors'][0]])
        st.plotly_chart(apply_theme_plotly(fig1), use_container_width=True)

    # Gráfico 2: Bivariado (Perfil Racial em %)
    # Lógica R equivalente (dplyr): 
    # df %>% group_by(raca_grupo) %>% count(coluna) %>% mutate(percent = n / sum(n))
    # Ou seja: calculamos o percentual da categoria DENTRO de cada raça (soma 100% por raça)
    with c2:
        # 1. Agrupa por Variável e Raça (contagem bruta)
        df_bi = df.groupby([coluna, 'raca_grupo']).size().reset_index(name='count')
        
        # 2. Calcula o total de N de cada grupo racial (Denominador)
        # Isso garante que estamos calculando % dentro do grupo, não do total geral
        total_por_raca = df_bi.groupby('raca_grupo')['count'].transform('sum')
        
        # 3. Calcula %
        df_bi['percent'] = (df_bi['count'] / total_por_raca) * 100
        
        # 4. Cria label formatada: "25.5% (N=12)"
        df_bi['label'] = df_bi.apply(lambda x: f"{x['percent']:.1f}% (N={x['count']})", axis=1)
        
        # 5. Plota usando % no Y, mas mostrando a label customizada e o eixo em %
        fig2 = px.bar(df_bi, x=coluna, y='percent', color='raca_grupo', barmode='group',
                      text='label', # Usa o texto formatado com % e N
                      title=f"Perfil por Raça (% dentro do grupo)",
                      color_discrete_sequence=current_theme['chart_colors'])
        
        fig2.update_layout(yaxis_title="% do Grupo Racial")
        st.plotly_chart(apply_theme_plotly(fig2), use_container_width=True)
    
    st.markdown("---")

# ==============================================================================
# 🚀 4. INTERFACE PRINCIPAL
# ==============================================================================

def main():
    if not check_password():
        login()
        return

    with st.sidebar:
        col_img, col_btn = st.columns([2, 1])
        with col_img:
            st.image("https://img.icons8.com/clouds/100/000000/rocket.png", width=80)
        with col_btn:
            st.toggle('🌗', value=(st.session_state.theme == 'dark'), on_change=toggle_theme)
        
        st.title("Menu NAVE")
        page = st.radio("Navegação:", ["Dashboard", "Formulário de Matrícula", "Administração"])
    
    sh = get_spreadsheet_object()
    if not sh: return

    if page == "Dashboard":
        st.title("🚀 NAVE LÚCIO THOME: ESTUDANTES A DECOLAR")
        st.markdown(f"Modo: **{st.session_state.theme.title()}** | Sistema de Monitorização")

        if st.button("🔄 Atualizar Dados"):
            st.cache_data.clear()
            st.rerun()

        # Carregar e Unificar Dados
        # R: bind_rows(df_novas, df_rematriculas)
        df_novas = load_data_cached("Novas_Matriculas")
        df_rematriculas = load_data_cached("Rematriculas")
        
        if not df_novas.empty: df_novas['tipo_matricula'] = 'Nova Matrícula'
        if not df_rematriculas.empty: df_rematriculas['tipo_matricula'] = 'Rematrícula'
        df_total = pd.concat([df_novas, df_rematriculas], ignore_index=True)
        
        # Aplicar agrupamento racial
        df_total = agrupar_raca(df_total)

        if df_total.empty:
            st.warning("Sem dados. Gere dados de teste na aba Administração.")
        else:
            # --- FILTROS ---
            with st.expander("🔍 Filtros Avançados", expanded=False):
                st.markdown('<div class="filter-box">', unsafe_allow_html=True)
                f1, f2, f3 = st.columns(3)
                with f1:
                    opcoes_serie = sorted(df_total['ano_serie'].astype(str).unique()) if 'ano_serie' in df_total.columns else []
                    sel_serie = st.multiselect("Série:", options=opcoes_serie)
                with f2:
                    opcoes_bairro = sorted(df_total['bairro'].astype(str).unique()) if 'bairro' in df_total.columns else []
                    sel_bairro = st.multiselect("Bairro:", options=opcoes_bairro)
                with f3:
                    opcoes_inse = sorted(df_total['inse_classificacao'].astype(str).unique()) if 'inse_classificacao' in df_total.columns else []
                    sel_inse = st.multiselect("INSE:", options=opcoes_inse)
                st.markdown('</div>', unsafe_allow_html=True)

            # R: df_filtered <- df_total %>% filter(...)
            df_filtered = df_total.copy()
            if sel_serie: df_filtered = df_filtered[df_filtered['ano_serie'].isin(sel_serie)]
            if sel_bairro: df_filtered = df_filtered[df_filtered['bairro'].isin(sel_bairro)]
            if sel_inse: df_filtered = df_filtered[df_filtered['inse_classificacao'].isin(sel_inse)]

            if df_filtered.empty:
                st.warning("Filtro retornou vazio.")
            else:
                # --- CARDS DE RESUMO ---
                c1, c2, c3, c4 = st.columns(4)
                with c1: gamified_card("Total Alunos", len(df_filtered), "🎓", 'primary')
                with c2: gamified_card("Novas", len(df_filtered[df_filtered['tipo_matricula'] == 'Nova Matrícula']), "✨", 'primary')
                with c3: gamified_card("Rematrículas", len(df_filtered[df_filtered['tipo_matricula'] == 'Rematrícula']), "🛡️", 'primary')
                inse_moda = df_filtered['inse_classificacao'].mode()[0] if 'inse_classificacao' in df_filtered.columns and not df_filtered['inse_classificacao'].mode().empty else "N/A"
                with c4: gamified_card("Nível INSE Típico", inse_moda, "📊", 'primary')

                st.markdown("---")

                # --- ABAS DE ANÁLISE ---
                tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Visão Geral", "💰 Socioeconômico", "🏠 Estrutura & Bens", "👨‍👩‍👧‍👦 Práticas Familiares", "🗺️ Mapa"])

                with tab1:
                    # Gráficos Univariados e Bivariados por Raça
                    plot_analise_completa(df_filtered, "ano_serie", "Matrículas por Série", 
                                          ordem=[f"{i}º Ano" for i in range(1,10)])
                    plot_analise_completa(df_filtered, "turno", "Distribuição por Turno")

                with tab2:
                    plot_analise_completa(df_filtered, "inse_classificacao", "INSE (Nível Socioeconômico)", 
                                          ordem=["Baixo", "Médio-Baixo", "Médio", "Médio-Alto", "Alto"])
                    plot_analise_completa(df_filtered, "bolsa_familia", "Bolsa Família")
                    plot_analise_completa(df_filtered, "escolaridade_resp1", "Escolaridade Resp. 1",
                                          ordem=["Não informado", "Não alfabetizado", "Fundamental Incompleto", "Fundamental Completo", "Médio Incompleto", "Médio Completo", "Superior Incompleto", "Superior Completo"])

                with tab3:
                    # R: Usando 'qtd_pessoas_domicilio' que é o nome correto da coluna
                    if 'qtd_pessoas_domicilio' in df_filtered.columns:
                        plot_analise_completa(df_filtered, "qtd_pessoas_domicilio", "Pessoas no Domicílio")
                    
                    if 'livros_qtd' in df_filtered.columns:
                        plot_analise_completa(df_filtered, "livros_qtd", "Quantidade de Livros em Casa",
                                              ordem=["Não informado", "0-10", "11-50", "Mais de 100"]) # Ajuste conforme dados

                with tab4:
                    st.info("Nota: Gere novos dados para visualizar estas informações corretamente.")
                    cols_praticas = {
                        'pratica_local_estudo': 'Local adequado para estudo?', 
                        'pratica_horario_fixo': 'Tem horário fixo?', 
                        'pratica_acompanhamento_pais': 'Pais ajudam?', 
                        'pratica_leitura_compartilhada': 'Leitura em família?', 
                        'pratica_conversa_escola': 'Conversam sobre escola?'
                    }
                    ordem_freq = ["Não informado", "Nunca", "Raramente", "Às vezes", "Frequentemente", "Sempre", "Semanalmente", "Diariamente"]
                    
                    for col_db, pergunta in cols_praticas.items():
                        plot_analise_completa(df_filtered, col_db, pergunta, ordem=ordem_freq)

                with tab5:
                    if 'bairro' in df_filtered.columns:
                        # R: count(bairro) %>% left_join(lat_long)
                        df_mapa = df_filtered['bairro'].value_counts().reset_index()
                        df_mapa.columns = ['bairro', 'count']
                        df_mapa['lat'] = df_mapa['bairro'].apply(lambda x: COORDENADAS_BAIRROS.get(x, {}).get('lat'))
                        df_mapa['lon'] = df_mapa['bairro'].apply(lambda x: COORDENADAS_BAIRROS.get(x, {}).get('lon'))
                        df_mapa = df_mapa.dropna(subset=['lat', 'lon'])
                        if not df_mapa.empty:
                            fig_map = px.scatter_mapbox(
                                df_mapa, lat="lat", lon="lon", hover_name="bairro", size="count", color="count",
                                color_continuous_scale=["#FFC0CB", "#BE185D", "#4B0082"], size_max=40, zoom=10.5, mapbox_style="open-street-map",
                                title="Geolocalização (Centróide)"
                            )
                            st.plotly_chart(apply_theme_plotly(fig_map), use_container_width=True)

    elif page == "Formulário de Matrícula":
        st.title("📝 Nova Matrícula")
        with st.container():
            st.markdown('<div class="filter-box">', unsafe_allow_html=True)
            tipo_matricula = st.radio("Tipo:", ["Nova Matrícula", "Rematrícula"], horizontal=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.write("") 
        with st.form("matricula_form"):
            c1, c2 = st.columns(2)
            nm_estudante = c1.text_input("Nome Completo")
            dt_nasc = c2.date_input("Data de Nascimento", min_value=datetime(2000, 1, 1))
            ce1, ce2 = st.columns([3, 1])
            logradouro = ce1.text_input("Rua/Logradouro")
            numero = ce2.text_input("Nº")
            ce3, ce4 = st.columns(2)
            bairro_sel = ce3.selectbox("Bairro", BAIRROS_MARICA + ["Outro"])
            bairro_final = bairro_sel if bairro_sel != "Outro" else ce3.text_input("Digite o Bairro")
            cep = ce4.text_input("CEP")
            serie = st.selectbox("Série 2026", [f"{i}º Ano" for i in range(1, 10)])
            turno = st.radio("Turno", ["Manhã", "Tarde"], horizontal=True)
            complemento = st.text_input("Escola Anterior") if tipo_matricula == "Nova Matrícula" else st.text_input("Turma Anterior")
            
            st.markdown("### Socioeconômico e Familiar")
            # Lista de opções padrão + "Não informado"
            opcoes_raca = ["Não informado", "Parda", "Preta", "Branca", "Indígena", "Amarela"]
            opcoes_esc = ["Não informado", "Não alfabetizado", "Fundamental Incompleto", "Fundamental Completo", "Médio Incompleto", "Médio Completo", "Superior Incompleto", "Superior Completo"]
            opcoes_livros = ["Não informado", "0-10", "11-50", "51-100", "Mais de 100"]
            opcoes_bolsa = ["Não informado", "Sim", "Não"]

            raca = st.selectbox("Cor/Raça", opcoes_raca)
            esc1 = st.selectbox("Escolaridade Responsável 1", opcoes_esc)
            esc2 = st.selectbox("Escolaridade Responsável 2", ["Não informado", "", "Fundamental Incompleto", "Médio Completo", "Superior Completo"])
            bens = st.multiselect("Bens", ["TV", "Carro", "Computador/Notebook", "Internet Wifi", "Ar Condicionado"])
            banheiros = st.number_input("Banheiros", 1, 5)
            pessoas = st.number_input("Pessoas na casa", 1, 15)
            livros = st.selectbox("Livros em casa", opcoes_livros)
            bolsa = st.radio("Recebe Bolsa Família?", opcoes_bolsa, horizontal=True)
            
            st.markdown("### Práticas Familiares (Gamificado)")
            
            # --- Seção Gamificada ---
            with st.expander(label="🏠 Onde e quando o aluno estuda?", expanded=True):
                 # Ajustado para st.radio conforme solicitado
                 opcoes_freq_estudo = ["Não informado", "Nunca", "Raramente", "Às vezes", "Frequentemente", "Sempre"]
                 p1 = st.radio("Local adequado para estudar?", opcoes_freq_estudo, horizontal=True)
                 p2 = st.radio("Horário fixo de estudo?", opcoes_freq_estudo, horizontal=True)

            with st.expander(label="👨‍👩‍👧‍👦 Envolvimento da Família", expanded=True):
                 opcoes_freq = ["Não informado", "Nunca", "Raramente", "Semanalmente", "Diariamente"]
                 p3 = st.radio("Pais ajudam nas tarefas?", opcoes_freq, horizontal=True)
                 p4 = st.radio("Leitura em família?", opcoes_freq, horizontal=True)
                 p5 = st.radio("Conversam sobre a escola?", opcoes_freq, horizontal=True)
            # -------------------------

            submitted = st.form_submit_button("✅ Registrar Aluno")
            if submitted:
                if not nm_estudante:
                    st.error("Nome é obrigatório!")
                else:
                    pontos, inse_nivel = calcular_inse(esc1, esc2, bens, banheiros, pessoas)
                    # Cria lista de dados garantindo ordem correta para o Sheets
                    dados = [
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nm_estudante, str(dt_nasc), 
                        "Responsável Fake", "Parentesco Fake", "Tel Fake", "Email Fake", 
                        logradouro, numero, bairro_final, "Maricá", cep, 
                        serie, turno, complemento, "Sim", 
                        raca, "Gen Fake", esc1, esc2, 
                        pessoas, banheiros, ", ".join(bens), 
                        livros, bolsa, pontos, inse_nivel, 
                        p1, p2, p3, p4, p5
                    ]
                    target = "Novas_Matriculas" if tipo_matricula == "Nova Matrícula" else "Rematriculas"
                    save_data(sh, target, dados)
                    st.success(f"Matrícula realizada! INSE: {inse_nivel}")

    elif page == "Administração":
        st.title("⚙️ Painel Admin")
        tab_admin = st.radio("Tabela:", ["Novas_Matriculas", "Rematriculas"], horizontal=True)
        df_admin = load_data_cached(tab_admin)
        if not df_admin.empty:
            st.markdown(f"### Visualizando: {tab_admin} ({len(df_admin)} registros)")
            st.data_editor(df_admin, use_container_width=True, num_rows="dynamic")
            csv = df_admin.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Baixar CSV", csv, f"{tab_admin}.csv", "text/csv")
        st.divider()
        st.subheader("🛠️ Ferramentas de Teste")
        if st.button("🎲 Gerar 10 Alunos Fakes"):
            with st.spinner("Gerando dados..."):
                generate_fake_data(sh, 10)
            st.success("Dados gerados com sucesso!")

if __name__ == "__main__":
    main()
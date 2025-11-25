import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import plotly.express as px
from faker import Faker
import random

# --- Configuração da Página ---
st.set_page_config(page_title="Matrículas 2026 - NAVE", layout="wide", page_icon="🚀")

# --- Estilização Personalizada (CSS) ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    h1 {
        color: #2c3e50;
        font-family: 'Helvetica Neue', sans-serif;
    }
    h2 {
        color: #e67e22; /* Laranja NAVE */
        border-bottom: 2px solid #e67e22;
        padding-bottom: 10px;
        margin-top: 30px;
    }
    h3 {
        color: #34495e;
    }
    .stButton>button {
        background-color: #e67e22;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #d35400;
        color: white;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    /* Estilo para container de filtros */
    .filter-box {
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
        background-color: #ffffff;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Constantes e Segredos ---
PASSWORD = "NAVE2026"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Mapeamento Real Aproximado (Centróide) dos Bairros de Maricá
COORDENADAS_BAIRROS = {
    "Araçatiba":        {"lat": -22.9275, "lon": -42.8098},
    "Bambuí":           {"lat": -22.9231, "lon": -42.7482},
    "Barra de Maricá":  {"lat": -22.9567, "lon": -42.8374},
    "Boqueirão":        {"lat": -22.9224, "lon": -42.8336},
    "Caju":             {"lat": -22.9125, "lon": -42.8055},
    "Centro":           {"lat": -22.9194, "lon": -42.8183},
    "Condado de Maricá":{"lat": -22.9130, "lon": -42.7850},
    "Cordeirinho":      {"lat": -22.9602, "lon": -42.7561},
    "Flamengo":         {"lat": -22.9150, "lon": -42.8250},
    "Inoã":             {"lat": -22.9188, "lon": -42.8712},
    "Itaipuaçu":        {"lat": -22.9658, "lon": -42.9242},
    "Itapeba":          {"lat": -22.9080, "lon": -42.8300},
    "Jacaroá":          {"lat": -22.9055, "lon": -42.7950},
    "Jaconé":           {"lat": -22.9370, "lon": -42.6390},
    "Jardim Interlagos":{"lat": -22.9400, "lon": -42.7200},
    "Lagarto":          {"lat": -22.9000, "lon": -42.7800},
    "Maricá":           {"lat": -22.9194, "lon": -42.8183},
    "Mumbuca":          {"lat": -22.9085, "lon": -42.8120},
    "Parque Nanci":     {"lat": -22.9150, "lon": -42.8450},
    "Pilar":            {"lat": -22.8850, "lon": -42.8100},
    "Pindobal":         {"lat": -22.9300, "lon": -42.7400},
    "Ponta Negra":      {"lat": -22.9610, "lon": -42.6930},
    "Restinga de Maricá":{"lat": -22.9680, "lon": -42.8500},
    "Retiro":           {"lat": -22.8950, "lon": -42.7850},
    "São José do Imbassaí": {"lat": -22.9380, "lon": -42.8440},
    "Silvado":          {"lat": -22.8700, "lon": -42.7800},
    "Spar":             {"lat": -22.9250, "lon": -42.8900},
    "Ubatiba":          {"lat": -22.8800, "lon": -42.7900},
    "Vale da Figueira": {"lat": -22.9450, "lon": -42.7100}
}

BAIRROS_MARICA = sorted(list(COORDENADAS_BAIRROS.keys()))

# --- Funções Auxiliares ---

def login():
    st.markdown("### 🔒 Acesso Restrito")
    senha = st.text_input("Digite a senha:", type="password")
    if st.button("Entrar"):
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
            # Fallback para desenvolvimento local
            creds = ServiceAccountCredentials.from_json_keyfile_name("rwilliammelo-7509a86c9df0.json", SCOPES)
        
        client = gspread.authorize(creds)
        return client.open("Matrículas 2026 - NAVE")
    except Exception as e:
        st.error(f"Erro de Conexão com Google Sheets: {e}")
        return None

def setup_spreadsheet():
    return get_spreadsheet_object()

def save_data(sh, tab_name, data):
    try:
        worksheet = sh.worksheet(tab_name)
        worksheet.append_row(data)
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    return st.session_state.password_correct
    st.cache_data.clear()

@st.cache_data(ttl=60)
def load_data_cached(tab_name):
    sh = get_spreadsheet_object()
    if not sh: return pd.DataFrame()
    try:
        worksheet = sh.worksheet(tab_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

def calcular_inse(escolaridade1, escolaridade2, bens, banheiros, qtd_pessoas):
    pontos = 0
    mapa_escolaridade = {
        "Não alfabetizado": 0, "Fundamental Incompleto": 1, "Fundamental Completo": 2,
        "Médio Incompleto": 3, "Médio Completo": 4, "Superior Incompleto": 5, "Superior Completo": 6
    }
    pontos += mapa_escolaridade.get(escolaridade1, 0) * 2
    if escolaridade2:
        pontos += mapa_escolaridade.get(escolaridade2, 0)
    
    if isinstance(bens, str):
        lista_bens = bens.split(",")
        pontos += len(lista_bens)
    elif isinstance(bens, list):
        pontos += len(bens)
        
    pontos += int(banheiros) * 2
    
    if "Carro" in bens: pontos += 3
    if "Computador/Notebook" in bens: pontos += 2
    
    classificacao = ""
    if pontos <= 5: classificacao = "Baixo"
    elif pontos <= 10: classificacao = "Médio-Baixo"
    elif pontos <= 18: classificacao = "Médio"
    elif pontos <= 25: classificacao = "Médio-Alto"
    else: classificacao = "Alto"
    
    return pontos, classificacao

def generate_fake_data(sh, qtd=10):
    fake = Faker('pt_BR')
    rows_novas = []
    rows_rematriculas = []
    
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

        dados_comuns_inicio = [
            fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S"),
            fake.name(), str(fake.date_of_birth(minimum_age=6, maximum_age=15)),
            fake.name(), str(fake.date_of_birth(minimum_age=25, maximum_age=60)),
            random.choice(["Mãe", "Pai", "Avó", "Tio"]), fake.phone_number(), fake.email(),
            fake.street_name(), fake.building_number(), bairro_escolhido, "Maricá", fake.postcode(),
            f"{random.randint(1, 9)}º Ano", random.choice(["Manhã", "Tarde"])
        ]
        
        dados_comuns_fim = [
            "Sim", random.choice(["Branca", "Preta", "Parda"]), random.choice(["Masculino", "Feminino"]),
            esc1, esc2, qtd_pessoas, banheiros, bens_str,
            random.choice(["0-10", "11-50", "Mais de 100"]), random.choice(["Sim", "Não"]),
            pontos, inse_class,
            random.choice(["Sempre", "Às vezes"]), random.choice(["Sempre", "Às vezes"]),
            random.choice(["Diariamente", "Semanalmente"]), random.choice(["Raramente", "Semanalmente"]),
            random.choice(["Diariamente", "Semanalmente"])
        ]

        if tipo == "Nova":
            especifico = [f"Escola {fake.last_name()}"]
            rows_novas.append(dados_comuns_inicio + especifico + dados_comuns_fim)
        else:
            especifico = [f"7{random.randint(10, 99)}"]
            rows_rematriculas.append(dados_comuns_inicio + especifico + dados_comuns_fim)
            
    if rows_novas: sh.worksheet("Novas_Matriculas").append_rows(rows_novas)
    if rows_rematriculas: sh.worksheet("Rematriculas").append_rows(rows_rematriculas)
    st.cache_data.clear()

# --- Interface Principal ---

def main():
    if not check_password():
        login()
        return

    st.sidebar.image("https://img.icons8.com/clouds/100/000000/rocket.png", width=100)
    st.sidebar.title("Navegação")
    page = st.sidebar.radio("Ir para:", ["Dashboard", "Formulário de Matrícula", "Administração"])
    
    sh = setup_spreadsheet()
    if not sh: return

    if page == "Dashboard":
        st.title("📊 Dashboard NAVE 2026")
        st.markdown("Visão geral dos dados. Atualiza automaticamente após novos cadastros.")
        
        if st.button("🔄 Atualizar Agora"):
            st.cache_data.clear()
            st.rerun()

        # Carrega dados
        df_novas = load_data_cached("Novas_Matriculas")
        df_rematriculas = load_data_cached("Rematriculas")
        
        if not df_novas.empty: df_novas['tipo_matricula'] = 'Nova Matrícula'
        if not df_rematriculas.empty: df_rematriculas['tipo_matricula'] = 'Rematrícula'
            
        df_total = pd.concat([df_novas, df_rematriculas], ignore_index=True)
        
        if df_total.empty:
            st.warning("Sem dados. Vá em Administração e gere dados de teste.")
        else:
            # --- ÁREA DE FILTROS NO DASHBOARD ---
            with st.expander("🔍 Filtros Avançados (Clique para expandir)", expanded=False):
                st.markdown('<div class="filter-box">', unsafe_allow_html=True)
                f1, f2, f3 = st.columns(3)
                
                with f1:
                    # Filtro Série
                    opcoes_serie = sorted(df_total['ano_serie'].astype(str).unique()) if 'ano_serie' in df_total.columns else []
                    sel_serie = st.multiselect("Filtrar por Série:", options=opcoes_serie)
                    
                    # Filtro Turno
                    opcoes_turno = sorted(df_total['turno'].astype(str).unique()) if 'turno' in df_total.columns else []
                    sel_turno = st.multiselect("Filtrar por Turno:", options=opcoes_turno)

                with f2:
                    # Filtro Bairro
                    opcoes_bairro = sorted(df_total['bairro'].astype(str).unique()) if 'bairro' in df_total.columns else []
                    sel_bairro = st.multiselect("Filtrar por Bairro:", options=opcoes_bairro)
                    
                    # Filtro Raça
                    opcoes_raca = sorted(df_total['raca'].astype(str).unique()) if 'raca' in df_total.columns else []
                    sel_raca = st.multiselect("Filtrar por Raça:", options=opcoes_raca)

                with f3:
                     # Filtro INSE
                    if 'inse_classificacao' in df_total.columns:
                        todas_opcoes = ["Baixo", "Médio-Baixo", "Médio", "Médio-Alto", "Alto"]
                        existentes = df_total['inse_classificacao'].unique()
                        opcoes_inse = [x for x in todas_opcoes if x in existentes]
                        sel_inse = st.multiselect("Filtrar por INSE:", options=opcoes_inse)
                    else:
                        sel_inse = []
                
                st.markdown('</div>', unsafe_allow_html=True)

            # --- APLICAÇÃO DOS FILTROS ---
            df_filtered = df_total.copy()
            
            if sel_serie:
                df_filtered = df_filtered[df_filtered['ano_serie'].isin(sel_serie)]
            if sel_turno:
                df_filtered = df_filtered[df_filtered['turno'].isin(sel_turno)]
            if sel_bairro:
                df_filtered = df_filtered[df_filtered['bairro'].isin(sel_bairro)]
            if sel_raca:
                df_filtered = df_filtered[df_filtered['raca'].isin(sel_raca)]
            if sel_inse:
                df_filtered = df_filtered[df_filtered['inse_classificacao'].isin(sel_inse)]

            # --- EXIBIÇÃO DOS DADOS FILTRADOS ---
            
            if df_filtered.empty:
                st.warning("Nenhum dado encontrado com os filtros selecionados.")
            else:
                # Métricas (Usando df_filtered)
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("Total Alunos", len(df_filtered))
                col2.metric("Novas", len(df_filtered[df_filtered['tipo_matricula'] == 'Nova Matrícula']))
                col3.metric("Rematrículas", len(df_filtered[df_filtered['tipo_matricula'] == 'Rematrícula']))
                col4.metric("Bolsa Família", len(df_filtered[df_filtered['bolsa_familia'] == 'Sim']) if 'bolsa_familia' in df_filtered.columns else 0)
                
                inse_moda = df_filtered['inse_classificacao'].mode()[0] if 'inse_classificacao' in df_filtered.columns and not df_filtered['inse_classificacao'].mode().empty else "N/A"
                col5.metric("INSE Predominante", inse_moda)

                st.markdown("---")
                
                # Abas do Dashboard (Usando df_filtered)
                tab1, tab2, tab3, tab4 = st.tabs(["📈 Demografia & Escola", "💰 Socioeconômico (INSE)", "👪 Práticas Familiares", "🗺️ Mapa (Maricá)"])
                
                with tab1:
                    c1, c2 = st.columns(2)
                    with c1:
                        df_serie = df_filtered.groupby(['ano_serie', 'tipo_matricula']).size().reset_index(name='count')
                        fig_serie = px.bar(df_serie, x='ano_serie', y='count', color='tipo_matricula',
                            title="Total de Alunos por Série", text_auto=True, color_discrete_sequence=px.colors.qualitative.Pastel)
                        st.plotly_chart(fig_serie, use_container_width=True)
                    with c2:
                        df_turno = df_filtered['turno'].value_counts().reset_index()
                        df_turno.columns = ['turno', 'count']
                        fig_turno = px.bar(df_turno, x='turno', y='count', title="Alunos por Turno", text_auto=True,
                            color='turno', color_discrete_sequence=px.colors.qualitative.Set3)
                        st.plotly_chart(fig_turno, use_container_width=True)
                    
                    c3, c4 = st.columns(2)
                    with c3:
                        if 'bairro' in df_filtered.columns:
                            bairros_count = df_filtered['bairro'].value_counts().reset_index().head(10)
                            bairros_count.columns = ['bairro', 'count']
                            fig_bairro = px.bar(bairros_count, x='count', y='bairro', orientation='h', 
                                title="Top 10 Bairros (Maricá)", text_auto=True, color='count', color_continuous_scale='Oranges')
                            st.plotly_chart(fig_bairro, use_container_width=True)
                    with c4:
                        if 'raca' in df_filtered.columns:
                            df_raca = df_filtered['raca'].value_counts().reset_index()
                            df_raca.columns = ['raca', 'count']
                            fig_raca = px.bar(df_raca, x='raca', y='count', title="Autodeclaração de Cor/Raça", 
                                text_auto=True, color='raca', color_discrete_sequence=px.colors.qualitative.Safe)
                            st.plotly_chart(fig_raca, use_container_width=True)

                with tab2:
                    c1, c2 = st.columns(2)
                    with c1:
                        if 'inse_classificacao' in df_filtered.columns:
                            ordem_inse = ["Baixo", "Médio-Baixo", "Médio", "Médio-Alto", "Alto"]
                            df_filtered['inse_classificacao'] = pd.Categorical(df_filtered['inse_classificacao'], categories=ordem_inse, ordered=True)
                            fig_inse = px.histogram(df_filtered.sort_values('inse_classificacao'), x='inse_classificacao', 
                                title="Distribuição de Nível Socioeconômico", color='inse_classificacao', text_auto=True,
                                color_discrete_sequence=px.colors.sequential.Viridis)
                            st.plotly_chart(fig_inse, use_container_width=True)
                    with c2:
                        if 'escolaridade_resp1' in df_filtered.columns:
                            df_esc = df_filtered['escolaridade_resp1'].value_counts().reset_index()
                            df_esc.columns = ['escolaridade', 'count']
                            fig_esc = px.bar(df_esc, x='escolaridade', y='count', title="Escolaridade do Responsável 1",
                                text_auto=True, color='escolaridade')
                            fig_esc.update_xaxes(tickangle=45)
                            st.plotly_chart(fig_esc, use_container_width=True)

                with tab3:
                    cols = ['pratica_local_estudo', 'pratica_horario_fixo', 'pratica_acompanhamento_pais', 'pratica_leitura_compartilhada', 'pratica_conversa_escola']
                    for col in cols:
                        if col in df_filtered.columns:
                            fig = px.histogram(df_filtered, x=col, title=col.replace('pratica_', '').replace('_', ' ').title(), color=col, text_auto=True)
                            st.plotly_chart(fig, use_container_width=True)

                with tab4:
                    if 'bairro' in df_filtered.columns:
                        df_mapa = df_filtered['bairro'].value_counts().reset_index()
                        df_mapa.columns = ['bairro', 'count']
                        df_mapa['lat'] = df_mapa['bairro'].apply(lambda x: COORDENADAS_BAIRROS.get(x, {}).get('lat'))
                        df_mapa['lon'] = df_mapa['bairro'].apply(lambda x: COORDENADAS_BAIRROS.get(x, {}).get('lon'))
                        df_mapa = df_mapa.dropna(subset=['lat', 'lon'])
                        
                        if not df_mapa.empty:
                            fig_map = px.scatter_mapbox(
                                df_mapa, lat="lat", lon="lon", hover_name="bairro", size="count", color="count",
                                color_continuous_scale="Viridis", size_max=40, zoom=10, mapbox_style="open-street-map",
                                title="Concentração de Alunos por Bairro (Filtrado)"
                            )
                            st.plotly_chart(fig_map, use_container_width=True)
                        else:
                             st.info("Nenhum dado geográfico para os filtros selecionados.")
                    else:
                        st.warning("Sem dados de bairro.")

    elif page == "Formulário de Matrícula":
        st.title("📝 Ficha de Matrícula 2026")
        
        with st.container():
            tipo_matricula = st.radio("", ["Nova Matrícula", "Rematrícula"], horizontal=True)
        
        st.divider()

        with st.form("matricula_form"):
            st.subheader("1. Identificação")
            c1, c2 = st.columns(2)
            nm_estudante = c1.text_input("Nome do Estudante")
            dt_nasc_estudante = c2.date_input("Nascimento do Estudante", min_value=datetime(2000, 1, 1))
            c3, c4 = st.columns(2)
            nm_responsavel = c3.text_input("Nome do Responsável")
            dt_nasc_responsavel = c4.date_input("Nascimento do Responsável", min_value=datetime(1950, 1, 1))
            c5, c6, c7 = st.columns(3)
            parentesco = c5.selectbox("Parentesco", ["Mãe", "Pai", "Avó/Avô", "Tio/Tia", "Outro"])
            telefone = c6.text_input("Celular/WhatsApp")
            email = c7.text_input("E-mail")

            st.subheader("2. Endereço")
            ce1, ce2 = st.columns([3, 1])
            logradouro = ce1.text_input("Logradouro")
            numero = ce2.text_input("Número")
            ce3, ce4, ce5 = st.columns(3)
            bairro_selecionado = ce3.selectbox("Bairro", BAIRROS_MARICA + ["Outro"])
            bairro_final = bairro_selecionado if bairro_selecionado != "Outro" else ce3.text_input("Nome do bairro")
            municipio = ce4.text_input("Município", value="Maricá", disabled=True)
            cep = ce5.text_input("CEP")

            st.subheader("3. Dados Escolares")
            ces1, ces2 = st.columns(2)
            ano_serie = ces1.selectbox("Ano/Série (2026)", [f"{i}º Ano" for i in range(1, 10)])
            turno = ces2.radio("Turno", ["Manhã", "Tarde"], horizontal=True)
            escola_origem = ""
            turma_anterior = ""
            if tipo_matricula == "Nova Matrícula": escola_origem = st.text_input("Escola de Origem")
            else: turma_anterior = st.text_input("Turma Anterior")

            st.subheader("4. Perfil Socioeconômico (INSE)")
            ci1, ci2 = st.columns(2)
            raca = ci1.selectbox("Cor/Raça", ["Branca", "Preta", "Parda", "Amarela", "Indígena", "Não declarado"])
            genero = ci2.selectbox("Gênero", ["Masculino", "Feminino", "Outro"])
            ci3, ci4 = st.columns(2)
            escolaridade_resp1 = ci3.selectbox("Escolaridade Resp. 1", ["Não alfabetizado", "Fundamental Incompleto", "Fundamental Completo", "Médio Incompleto", "Médio Completo", "Superior Incompleto", "Superior Completo"])
            escolaridade_resp2 = ci4.selectbox("Escolaridade Resp. 2", ["", "Não alfabetizado", "Fundamental Incompleto", "Fundamental Completo", "Médio Incompleto", "Médio Completo", "Superior Incompleto", "Superior Completo"])
            ci5, ci6 = st.columns(2)
            qtd_pessoas = ci5.number_input("Pessoas na casa", 1, 20)
            qtd_banheiros = ci6.number_input("Banheiros na casa", 0, 10)
            bens = st.multiselect("Bens no Domicílio", ["TV", "Geladeira", "Máquina de Lavar", "Carro", "Computador/Notebook", "Internet Wifi", "Ar Condicionado", "Microondas"])
            livros = st.selectbox("Livros em casa", ["0-10", "11-50", "51-100", "Mais de 100"])
            bolsa = st.radio("Recebe Bolsa Família?", ["Sim", "Não"], horizontal=True)

            st.subheader("5. Práticas Familiares")
            p1 = st.select_slider("Local adequado para estudar?", ["Nunca", "Raramente", "Às vezes", "Frequentemente", "Sempre"])
            p2 = st.select_slider("Horário fixo de estudo?", ["Nunca", "Raramente", "Às vezes", "Frequentemente", "Sempre"])
            p3 = st.selectbox("Pais ajudam nas tarefas?", ["Nunca", "Raramente", "Semanalmente", "Diariamente"])
            p4 = st.selectbox("Leitura em família?", ["Nunca", "Raramente", "Semanalmente", "Diariamente"])
            p5 = st.selectbox("Conversam sobre a escola?", ["Nunca", "Raramente", "Semanalmente", "Diariamente"])

            st.divider()
            consentimento = st.checkbox("Declaro que as informações são verdadeiras.")
            submitted = st.form_submit_button("✅ Confirmar Matrícula", use_container_width=True)

            if submitted:
                if not consentimento: st.warning("Aceite o termo.")
                elif not nm_estudante: st.error("Nome obrigatório.")
                else:
                    pontos, inse_nivel = calcular_inse(escolaridade_resp1, escolaridade_resp2, bens, qtd_banheiros, qtd_pessoas)
                    dados_inicio = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nm_estudante, str(dt_nasc_estudante), nm_responsavel, str(dt_nasc_responsavel), parentesco, telefone, email, logradouro, numero, bairro_final, municipio, cep, ano_serie, turno]
                    dados_fim = ["Sim", raca, genero, escolaridade_resp1, escolaridade_resp2, qtd_pessoas, qtd_banheiros, ", ".join(bens), livros, bolsa, pontos, inse_nivel, p1, p2, p3, p4, p5]
                    
                    if tipo_matricula == "Nova Matrícula":
                        dados_finais = dados_inicio + [escola_origem] + dados_fim
                        tab = "Novas_Matriculas"
                    else:
                        dados_finais = dados_inicio + [turma_anterior] + dados_fim
                        tab = "Rematriculas"
                    
                    with st.spinner("Salvando..."):
                        save_data(sh, tab, dados_finais)
                        st.success(f"Salvo com sucesso! INSE Estimado: {inse_nivel}")
                        st.balloons()

    elif page == "Administração":
        st.title("⚙️ Administração")
        
        # --- ÁREA DE FILTROS DE ADMIN ---
        st.markdown("### 🔍 Filtros da Tabela")
        with st.expander("Opções de Filtragem", expanded=True):
            st.markdown('<div class="filter-box">', unsafe_allow_html=True)
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            
            # Carregar dados primeiro para pegar as opções
            tabela_selecionada = st.selectbox("Selecione a Tabela Base:", ["Novas_Matriculas", "Rematriculas"])
            df_admin = load_data_cached(tabela_selecionada)
            
            df_admin_filtrado = df_admin.copy()

            if not df_admin.empty:
                with col_f1:
                    # Filtro Série Admin
                    opts_serie_adm = sorted(df_admin['ano_serie'].astype(str).unique()) if 'ano_serie' in df_admin.columns else []
                    sel_serie_adm = st.multiselect("Série", options=opts_serie_adm, key="adm_serie")
                with col_f2:
                     # Filtro Turno Admin
                    opts_turno_adm = sorted(df_admin['turno'].astype(str).unique()) if 'turno' in df_admin.columns else []
                    sel_turno_adm = st.multiselect("Turno", options=opts_turno_adm, key="adm_turno")
                with col_f3:
                    # Filtro Bairro Admin
                    opts_bairro_adm = sorted(df_admin['bairro'].astype(str).unique()) if 'bairro' in df_admin.columns else []
                    sel_bairro_adm = st.multiselect("Bairro", options=opts_bairro_adm, key="adm_bairro")
                with col_f4:
                     # Filtro INSE Admin
                    if 'inse_classificacao' in df_admin.columns:
                         opts_inse_adm = [x for x in ["Baixo", "Médio-Baixo", "Médio", "Médio-Alto", "Alto"] if x in df_admin['inse_classificacao'].unique()]
                         sel_inse_adm = st.multiselect("INSE", options=opts_inse_adm, key="adm_inse")
                    else:
                         sel_inse_adm = []
                
                # Aplicar filtros Admin
                if sel_serie_adm: df_admin_filtrado = df_admin_filtrado[df_admin_filtrado['ano_serie'].isin(sel_serie_adm)]
                if sel_turno_adm: df_admin_filtrado = df_admin_filtrado[df_admin_filtrado['turno'].isin(sel_turno_adm)]
                if sel_bairro_adm: df_admin_filtrado = df_admin_filtrado[df_admin_filtrado['bairro'].isin(sel_bairro_adm)]
                if sel_inse_adm: df_admin_filtrado = df_admin_filtrado[df_admin_filtrado['inse_classificacao'].isin(sel_inse_adm)]

            st.markdown('</div>', unsafe_allow_html=True)

        if not df_admin_filtrado.empty:
            st.info(f"Exibindo {len(df_admin_filtrado)} registros filtrados.")
            st.data_editor(
                df_admin_filtrado, 
                num_rows="dynamic", 
                use_container_width=True,
                column_config={
                    "inse_pontos": st.column_config.NumberColumn("Pontos INSE", format="%d pts"),
                    "inse_classificacao": st.column_config.TextColumn("Faixa INSE", width="medium")
                }
            )
            st.download_button("Baixar CSV Filtrado", df_admin_filtrado.to_csv(index=False).encode('utf-8'), "dados_filtrados.csv")
        else:
            st.warning("Nenhum dado para exibir.")
        
        st.divider()
        qtd = st.number_input("Qtd Simulação", 1, 100, 10)
        if st.button("Gerar Dados Fake"):
            with st.spinner("Gerando..."):
                generate_fake_data(sh, qtd)
                st.success("Feito!")

if __name__ == "__main__":
    main()
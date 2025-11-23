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
    .stRadio > label {
        font-weight: bold;
        color: #2c3e50;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Constantes e Segredos ---
PASSWORD = "NAVE2026"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

BAIRROS_MARICA = [
    "Araçatiba", "Bambuí", "Barra de Maricá", "Boqueirão", "Caju", "Centro", 
    "Condado de Maricá", "Cordeirinho", "Flamengo", "Inoã", "Itaipuaçu", 
    "Itapeba", "Jacaroá", "Jaconé", "Jardim Interlagos", "Lagarto", "Maricá", 
    "Mumbuca", "Parque Nanci", "Pilar", "Pindobal", "Ponta Negra", 
    "Restinga de Maricá", "Retiro", "São José do Imbassaí", "Silvado", 
    "Spar", "Ubatiba", "Vale da Figueira"
]

# --- Funções Auxiliares ---

def check_password():
    """Retorna True se a senha estiver correta na sessão."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    return st.session_state.password_correct

def login():
    """Exibe o formulário de login."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🚀 Acesso Restrito - NAVE 2026")
        st.markdown("Bem-vindo ao sistema de matrículas.")
        password = st.text_input("Digite a Senha de Acesso", type="password")
        if st.button("Entrar", use_container_width=True):
            # Login case-insensitive
            if password.strip().upper() == PASSWORD.upper():
                st.session_state.password_correct = True
                st.rerun()
            elif password:
                st.error("Senha incorreta.")

def get_gspread_client():
    """Autentica e retorna o cliente gspread usando st.secrets."""
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Erro ao conectar com Google Sheets: {e}")
        return None

def setup_spreadsheet(client, sheet_name="Matriculas_NAVE_2026"):
    """Verifica e configura a planilha e suas abas."""
    try:
        sh = client.open(sheet_name)
    except gspread.SpreadsheetNotFound:
        st.error(f"Planilha '{sheet_name}' não encontrada!")
        st.info("Por favor, crie a planilha manualmente no Google Drive e compartilhe com o email da conta de serviço.")
        st.stop()
        return None

    # Campos comuns (Atualizado com raca e inse_classificacao)
    common_headers = [
        "data_registro", "nm_estudante", "dt_nasc_estudante", "nm_responsavel", 
        "dt_nasc_responsavel", "parentesco", "telefone", "email",
        "logradouro", "numero", "bairro", "municipio", "cep",
        "ano_serie", "turno",
        "consentimento_dados",
        "raca", "genero", "escolaridade_resp1", "escolaridade_resp2", # Renomeado inse_raca -> raca
        "qtd_pessoas_domicilio", "qtd_banheiros", "bens",
        "livros_qtd", "bolsa_familia",
        "inse_classificacao", # NOVO CAMPO
        "pratica_local_estudo", "pratica_horario_fixo", "pratica_acompanhamento_pais",
        "pratica_leitura_compartilhada", "pratica_conversa_escola"
    ]

    # Configurar Aba "Novas_Matriculas"
    try:
        ws_novas = sh.worksheet("Novas_Matriculas")
    except gspread.WorksheetNotFound:
        ws_novas = sh.add_worksheet(title="Novas_Matriculas", rows=1000, cols=40)
        headers_novas = common_headers[:15] + ["escola_origem"] + common_headers[15:]
        ws_novas.append_row(headers_novas)

    # Configurar Aba "Rematriculas"
    try:
        ws_rematriculas = sh.worksheet("Rematriculas")
    except gspread.WorksheetNotFound:
        ws_rematriculas = sh.add_worksheet(title="Rematriculas", rows=1000, cols=40)
        headers_rematriculas = common_headers[:15] + ["turma_anterior"] + common_headers[15:]
        ws_rematriculas.append_row(headers_rematriculas)
    
    return sh

def save_data(sh, tab_name, data):
    """Salva uma linha de dados na aba especificada."""
    worksheet = sh.worksheet(tab_name)
    worksheet.append_row(data)

def update_all_data(sh, tab_name, df):
    """Sobrescreve todos os dados da aba especificada."""
    worksheet = sh.worksheet(tab_name)
    data = [df.columns.values.tolist()] + df.values.tolist()
    worksheet.clear()
    worksheet.update(data)

def load_data(sh, tab_name):
    """Carrega dados de uma aba como DataFrame."""
    try:
        worksheet = sh.worksheet(tab_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

def calcular_inse(escolaridade1, escolaridade2, bens, banheiros, qtd_pessoas):
    """
    Calcula uma estimativa de INSE baseada em pontos.
    Lógica simplificada para fins de demonstração.
    """
    pontos = 0
    
    # Escolaridade (Peso alto)
    mapa_escolaridade = {
        "Não alfabetizado": 0, "Fundamental Incompleto": 1, "Fundamental Completo": 2,
        "Médio Incompleto": 3, "Médio Completo": 4, "Superior Incompleto": 5, "Superior Completo": 6
    }
    pontos += mapa_escolaridade.get(escolaridade1, 0) * 2
    if escolaridade2:
        pontos += mapa_escolaridade.get(escolaridade2, 0)
    
    # Bens (1 ponto cada)
    if isinstance(bens, str):
        lista_bens = bens.split(",")
        pontos += len(lista_bens)
    elif isinstance(bens, list):
        pontos += len(bens)
        
    # Banheiros
    pontos += int(banheiros) * 2
    
    # Ajuste por pessoa (mais pessoas dilui a renda, mas aqui simplificamos)
    # Se tiver carro e computador, bônus
    if "Carro" in bens: pontos += 3
    if "Computador/Notebook" in bens: pontos += 2
    
    # Classificação
    if pontos <= 5: return "Baixo"
    elif pontos <= 10: return "Médio-Baixo"
    elif pontos <= 18: return "Médio"
    elif pontos <= 25: return "Médio-Alto"
    else: return "Alto"

def generate_fake_data(sh, qtd=10):
    """Gera dados fictícios e salva nas duas abas em lote."""
    fake = Faker('pt_BR')
    rows_novas = []
    rows_rematriculas = []
    
    for _ in range(qtd):
        tipo = random.choice(["Nova", "Rematricula"])
        
        # Gerar dados para cálculo do INSE
        esc1 = random.choice(["Fundamental Completo", "Médio Completo", "Superior Completo"])
        esc2 = random.choice(["", "Fundamental Completo", "Médio Completo"])
        bens_lista = random.sample(["TV", "Geladeira", "Máquina de Lavar", "Carro", "Computador/Notebook", "Internet Wifi", "Ar Condicionado"], k=random.randint(1, 7))
        bens_str = ", ".join(bens_lista)
        banheiros = random.randint(1, 3)
        qtd_pessoas = random.randint(2, 7)
        
        inse_calc = calcular_inse(esc1, esc2, bens_lista, banheiros, qtd_pessoas)

        dados_comuns_inicio = [
            fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S"),
            fake.name(),
            str(fake.date_of_birth(minimum_age=6, maximum_age=15)),
            fake.name(),
            str(fake.date_of_birth(minimum_age=25, maximum_age=60)),
            random.choice(["Mãe", "Pai", "Avó", "Tio"]),
            fake.phone_number(),
            fake.email(),
            fake.street_name(),
            fake.building_number(),
            random.choice(BAIRROS_MARICA),
            "Maricá",
            fake.postcode(),
            f"{random.randint(1, 9)}º Ano",
            random.choice(["Manhã", "Tarde"])
        ]
        
        dados_comuns_fim = [
            "Sim",
            random.choice(["Branca", "Preta", "Parda"]),
            random.choice(["Masculino", "Feminino"]),
            esc1, esc2,
            qtd_pessoas, banheiros, bens_str,
            random.choice(["0-10", "11-50", "Mais de 100"]),
            random.choice(["Sim", "Não"]),
            inse_calc, # INSE CALCULADO
            random.choice(["Sempre", "Às vezes"]),
            random.choice(["Sempre", "Às vezes"]),
            random.choice(["Diariamente", "Semanalmente"]),
            random.choice(["Raramente", "Semanalmente"]),
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

# --- Interface Principal ---

def main():
    if not check_password():
        login()
        return

    st.sidebar.image("https://img.icons8.com/clouds/100/000000/rocket.png", width=100)
    st.sidebar.title("Navegação")
    page = st.sidebar.radio("Ir para:", ["Dashboard", "Formulário de Matrícula", "Administração"])
    
    client = get_gspread_client()
    if not client: st.stop()
    
    sh = setup_spreadsheet(client)
    if not sh: st.stop()

    if page == "Dashboard":
        st.title("📊 Dashboard NAVE 2026")
        st.markdown("Visão geral dos dados de matrícula e perfil dos estudantes.")
        
        df_novas = load_data(sh, "Novas_Matriculas")
        df_rematriculas = load_data(sh, "Rematriculas")
        
        if not df_novas.empty: df_novas['tipo_matricula'] = 'Nova Matrícula'
        if not df_rematriculas.empty: df_rematriculas['tipo_matricula'] = 'Rematrícula'
            
        df_total = pd.concat([df_novas, df_rematriculas], ignore_index=True)
        
        if df_total.empty:
            st.warning("Sem dados. Vá em Administração e gere dados de teste.")
        else:
            # Métricas
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Total Alunos", len(df_total))
            col2.metric("Novas", len(df_novas))
            col3.metric("Rematrículas", len(df_rematriculas))
            col4.metric("Bolsa Família", len(df_total[df_total['bolsa_familia'] == 'Sim']) if 'bolsa_familia' in df_total.columns else 0)
            
            # Métrica de INSE Médio (Moda)
            inse_moda = df_total['inse_classificacao'].mode()[0] if 'inse_classificacao' in df_total.columns else "N/A"
            col5.metric("INSE Predominante", inse_moda)

            st.markdown("---")
            
            # Abas do Dashboard
            tab1, tab2, tab3 = st.tabs(["📈 Demografia & Escola", "💰 Socioeconômico (INSE)", "👪 Práticas Familiares"])
            
            with tab1:
                c1, c2 = st.columns(2)
                with c1:
                    fig_serie = px.bar(df_total, x='ano_serie', title="Alunos por Série", color='tipo_matricula', text_auto=True, color_discrete_sequence=px.colors.qualitative.Pastel)
                    st.plotly_chart(fig_serie, use_container_width=True)
                with c2:
                    fig_turno = px.pie(df_total, names='turno', title="Turno", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
                    st.plotly_chart(fig_turno, use_container_width=True)
                
                c3, c4 = st.columns(2)
                with c3:
                    if 'bairro' in df_total.columns:
                        bairros_count = df_total['bairro'].value_counts().reset_index().head(10)
                        bairros_count.columns = ['bairro', 'count']
                        fig_bairro = px.bar(bairros_count, x='count', y='bairro', orientation='h', title="Top 10 Bairros (Maricá)", color='count', color_continuous_scale='Oranges')
                        st.plotly_chart(fig_bairro, use_container_width=True)
                with c4:
                    if 'raca' in df_total.columns:
                        fig_raca = px.pie(df_total, names='raca', title="Autodeclaração de Cor/Raça", color_discrete_sequence=px.colors.qualitative.Safe)
                        st.plotly_chart(fig_raca, use_container_width=True)

            with tab2:
                st.info("O INSE (Nível Socioeconômico) é calculado automaticamente com base na escolaridade dos pais, bens e estrutura domiciliar.")
                c1, c2 = st.columns(2)
                with c1:
                    if 'inse_classificacao' in df_total.columns:
                        # Ordenar faixas
                        ordem_inse = ["Baixo", "Médio-Baixo", "Médio", "Médio-Alto", "Alto"]
                        df_total['inse_classificacao'] = pd.Categorical(df_total['inse_classificacao'], categories=ordem_inse, ordered=True)
                        fig_inse = px.histogram(df_total.sort_values('inse_classificacao'), x='inse_classificacao', title="Distribuição de Nível Socioeconômico", color='inse_classificacao', color_discrete_sequence=px.colors.sequential.Viridis)
                        st.plotly_chart(fig_inse, use_container_width=True)
                with c2:
                    if 'escolaridade_resp1' in df_total.columns:
                        fig_esc = px.pie(df_total, names='escolaridade_resp1', title="Escolaridade do Responsável 1")
                        st.plotly_chart(fig_esc, use_container_width=True)
                
                # Cruzamento INSE x Raça
                if 'inse_classificacao' in df_total.columns and 'raca' in df_total.columns:
                    st.subheader("Cruzamento: INSE x Raça")
                    fig_cross = px.histogram(df_total, x='inse_classificacao', color='raca', barmode='group', title="INSE por Raça")
                    st.plotly_chart(fig_cross, use_container_width=True)

            with tab3:
                cols = ['pratica_local_estudo', 'pratica_horario_fixo', 'pratica_acompanhamento_pais', 'pratica_leitura_compartilhada', 'pratica_conversa_escola']
                for col in cols:
                    if col in df_total.columns:
                        fig = px.histogram(df_total, x=col, title=col.replace('pratica_', '').replace('_', ' ').title(), color=col)
                        st.plotly_chart(fig, use_container_width=True)

    elif page == "Formulário de Matrícula":
        st.title("📝 Ficha de Matrícula 2026")
        st.markdown("Preencha os dados com atenção. Campos marcados são obrigatórios.")
        
        with st.container():
            st.markdown("### Tipo de Vínculo")
            tipo_matricula = st.radio("", ["Nova Matrícula", "Rematrícula"], horizontal=True)
            if tipo_matricula == "Nova Matrícula":
                st.success("Aluno vindo de outra escola.")
            else:
                st.info("Aluno que já estuda na NAVE.")
        
        st.markdown("---")

        with st.form("matricula_form"):
            st.subheader("1. Identificação do Aluno e Responsável")
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

            st.subheader("2. Endereço (Maricá)")
            ce1, ce2 = st.columns([3, 1])
            logradouro = ce1.text_input("Logradouro")
            numero = ce2.text_input("Número")
            
            ce3, ce4, ce5 = st.columns(3)
            # Lógica de Bairro com "Outro"
            bairro_selecionado = ce3.selectbox("Bairro", BAIRROS_MARICA + ["Outro"])
            bairro_final = bairro_selecionado
            if bairro_selecionado == "Outro":
                bairro_final = ce3.text_input("Digite o nome do bairro")
            
            municipio = ce4.text_input("Município", value="Maricá", disabled=True)
            cep = ce5.text_input("CEP")

            st.subheader("3. Dados Escolares")
            ces1, ces2 = st.columns(2)
            ano_serie = ces1.selectbox("Ano/Série (2026)", [f"{i}º Ano" for i in range(1, 10)])
            turno = ces2.radio("Turno", ["Manhã", "Tarde"], horizontal=True)
            
            escola_origem = ""
            turma_anterior = ""
            
            if tipo_matricula == "Nova Matrícula":
                escola_origem = st.text_input("Escola de Origem")
            else:
                turma_anterior = st.text_input("Turma Anterior (Ex: 712)")

            st.subheader("4. Perfil Socioeconômico (INSE)")
            st.markdown("*As perguntas abaixo ajudam a definir o perfil da escola.*")
            
            ci1, ci2 = st.columns(2)
            raca = ci1.selectbox("Cor/Raça", ["Branca", "Preta", "Parda", "Amarela", "Indígena", "Não declarado"])
            genero = ci2.selectbox("Gênero", ["Masculino", "Feminino", "Outro"])
            
            ci3, ci4 = st.columns(2)
            escolaridade_resp1 = ci3.selectbox("Escolaridade Resp. 1", ["Não alfabetizado", "Fundamental Incompleto", "Fundamental Completo", "Médio Incompleto", "Médio Completo", "Superior Incompleto", "Superior Completo"])
            escolaridade_resp2 = ci4.selectbox("Escolaridade Resp. 2", ["", "Não alfabetizado", "Fundamental Incompleto", "Fundamental Completo", "Médio Incompleto", "Médio Completo", "Superior Incompleto", "Superior Completo"])
            
            ci5, ci6 = st.columns(2)
            qtd_pessoas = ci5.number_input("Pessoas na casa", 1, 20)
            qtd_banheiros = ci6.number_input("Banheiros na casa", 0, 10)
            
            bens = st.multiselect("Quais destes itens possui?", ["TV", "Geladeira", "Máquina de Lavar", "Carro", "Computador/Notebook", "Internet Wifi", "Ar Condicionado", "Microondas"])
            livros = st.selectbox("Livros em casa", ["0-10", "11-50", "51-100", "Mais de 100"])
            bolsa = st.radio("Recebe Bolsa Família?", ["Sim", "Não"], horizontal=True)

            st.subheader("5. Práticas Familiares")
            p1 = st.select_slider("Local adequado para estudar?", ["Nunca", "Raramente", "Às vezes", "Frequentemente", "Sempre"])
            p2 = st.select_slider("Horário fixo de estudo?", ["Nunca", "Raramente", "Às vezes", "Frequentemente", "Sempre"])
            p3 = st.selectbox("Pais ajudam nas tarefas?", ["Nunca", "Raramente", "Semanalmente", "Diariamente"])
            p4 = st.selectbox("Leitura em família?", ["Nunca", "Raramente", "Semanalmente", "Diariamente"])
            p5 = st.selectbox("Conversam sobre a escola?", ["Nunca", "Raramente", "Semanalmente", "Diariamente"])

            st.markdown("---")
            consentimento = st.checkbox("Declaro que as informações são verdadeiras.")
            
            submitted = st.form_submit_button("✅ Confirmar Matrícula", use_container_width=True)

            if submitted:
                if not consentimento:
                    st.warning("Aceite o termo para continuar.")
                elif not nm_estudante:
                    st.error("Nome do estudante é obrigatório.")
                else:
                    # Calcular INSE
                    inse_nivel = calcular_inse(escolaridade_resp1, escolaridade_resp2, bens, qtd_banheiros, qtd_pessoas)
                    
                    dados_comuns_inicio = [
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        nm_estudante, str(dt_nasc_estudante), nm_responsavel,
                        str(dt_nasc_responsavel), parentesco, telefone, email,
                        logradouro, numero, bairro_final, municipio, cep,
                        ano_serie, turno
                    ]
                    
                    dados_comuns_fim = [
                        "Sim", raca, genero, escolaridade_resp1, escolaridade_resp2,
                        qtd_pessoas, qtd_banheiros, ", ".join(bens),
                        livros, bolsa,
                        inse_nivel, # INSE CALCULADO
                        p1, p2, p3, p4, p5
                    ]

                    if tipo_matricula == "Nova Matrícula":
                        dados_finais = dados_comuns_inicio + [escola_origem] + dados_comuns_fim
                        tab = "Novas_Matriculas"
                    else:
                        dados_finais = dados_comuns_inicio + [turma_anterior] + dados_comuns_fim
                        tab = "Rematriculas"
                    
                    with st.spinner("Enviando..."):
                        save_data(sh, tab, dados_finais)
                        st.success(f"Matrícula realizada! Nível Socioeconômico estimado: {inse_nivel}")
                        st.balloons()

    elif page == "Administração":
        st.title("⚙️ Administração")
        
        tabela = st.selectbox("Tabela", ["Novas_Matriculas", "Rematriculas"])
        df = load_data(sh, tabela)
        
        if not df.empty:
            st.data_editor(df, num_rows="dynamic", use_container_width=True)
            st.download_button("Baixar CSV", df.to_csv(index=False).encode('utf-8'), "dados.csv")
        
        st.divider()
        qtd = st.number_input("Qtd Simulação", 1, 100, 10)
        if st.button("Gerar Dados Fake"):
            with st.spinner("Gerando..."):
                generate_fake_data(sh, qtd)
                st.success("Feito!")

if __name__ == "__main__":
    main()

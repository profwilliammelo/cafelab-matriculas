import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import plotly.express as px
from faker import Faker
import random

# --- Configuração da Página ---
st.set_page_config(page_title="Matrículas 2026 - NAVE", layout="wide", page_icon="🏫")

# --- Constantes e Segredos ---
PASSWORD = "NAVE2026"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# --- Funções Auxiliares ---

def check_password():
    """Retorna True se a senha estiver correta na sessão."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    return st.session_state.password_correct

def login():
    """Exibe o formulário de login."""
    st.title("🔐 Acesso Restrito - Matrículas 2026")
    password = st.text_input("Digite a Senha de Acesso", type="password")
    if st.button("Entrar"):
        if password == PASSWORD:
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
        st.info("Por favor, crie a planilha manualmente no Google Drive e compartilhe com o email da conta de serviço (veja no secrets.toml).")
        st.stop()
        return None

    # Configurar Aba "Dados"
    try:
        worksheet_dados = sh.worksheet("Dados")
    except gspread.WorksheetNotFound:
        worksheet_dados = sh.add_worksheet(title="Dados", rows=1000, cols=35)
        headers = [
            "data_registro", "nm_estudante", "dt_nasc_estudante", "nm_responsavel", 
            "dt_nasc_responsavel", "parentesco", "telefone", "email",
            "logradouro", "numero", "bairro", "municipio", "cep",
            "ano_serie", "turno", "turma", "escola_origem",
            "consentimento_dados",
            "inse_raca", "inse_genero", "inse_escolaridade_resp1", "inse_escolaridade_resp2",
            "inse_qtd_pessoas_domicilio", "inse_qtd_banheiros", "inse_bens",
            "inse_livros_qtd", "inse_bolsa_familia",
            "pratica_local_estudo", "pratica_horario_fixo", "pratica_acompanhamento_pais",
            "pratica_leitura_compartilhada", "pratica_conversa_escola"
        ]
        worksheet_dados.append_row(headers)

    return sh

def save_data(sh, data):
    """Salva uma linha de dados na aba 'Dados'."""
    worksheet = sh.worksheet("Dados")
    worksheet.append_row(data)

def update_all_data(sh, df):
    """Sobrescreve todos os dados da aba 'Dados' com o DataFrame fornecido."""
    worksheet = sh.worksheet("Dados")
    # Mantém o cabeçalho original ou usa o do DF
    data = [df.columns.values.tolist()] + df.values.tolist()
    worksheet.clear()
    worksheet.update(data)

def load_data(sh):
    """Carrega dados da aba 'Dados' como DataFrame."""
    worksheet = sh.worksheet("Dados")
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

def generate_fake_data(sh, qtd=10):
    """Gera dados fictícios e salva na planilha."""
    fake = Faker('pt_BR')
    
    bairros_niteroi = ["Icaraí", "Centro", "Fonseca", "Santa Rosa", "São Francisco", "Charitas", "Jurujuba", "Barreto", "Engenhoca"]
    series = [f"{i}º Ano" for i in range(1, 10)]
    
    for _ in range(qtd):
        dados = [
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
            random.choice(bairros_niteroi),
            "Niterói",
            fake.postcode(),
            random.choice(series),
            random.choice(["Manhã", "Tarde"]),
            f"7{random.randint(10, 99)}",
            f"Escola {fake.last_name()}",
            "Sim",
            random.choice(["Branca", "Preta", "Parda"]),
            random.choice(["Masculino", "Feminino"]),
            random.choice(["Fundamental Completo", "Médio Completo", "Superior Completo"]),
            random.choice(["Fundamental Completo", "Médio Completo"]),
            random.randint(2, 7),
            random.randint(1, 3),
            "TV, Geladeira, Internet",
            random.choice(["0-10", "11-50", "Mais de 100"]),
            random.choice(["Sim", "Não"]),
            random.choice(["Sempre", "Às vezes"]),
            random.choice(["Sempre", "Às vezes"]),
            random.choice(["Diariamente", "Semanalmente"]),
            random.choice(["Raramente", "Semanalmente"]),
            random.choice(["Diariamente", "Semanalmente"])
        ]
        save_data(sh, dados)

# --- Interface Principal ---

def main():
    if not check_password():
        login()
        return

    st.sidebar.title("Navegação")
    page = st.sidebar.radio("Ir para:", ["Dashboard", "Nova Matrícula", "Administração"])
    
    client = get_gspread_client()
    if not client:
        st.stop()
    
    sh = setup_spreadsheet(client)
    if not sh:
        st.stop()

    # Carregar dados (cacheado se possível, mas aqui faremos direto para garantir frescor)
    df = load_data(sh)

    if page == "Dashboard":
        st.title("📊 Dashboard Pedagógico e Administrativo")
        
        if df.empty:
            st.warning("Não há dados suficientes para gerar o dashboard. Vá em 'Administração' e gere dados de teste.")
        else:
            # Métricas Gerais
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total de Alunos", len(df))
            col2.metric("Turno Manhã", len(df[df['turno'] == 'Manhã']))
            col3.metric("Turno Tarde", len(df[df['turno'] == 'Tarde']))
            col4.metric("Bolsa Família", len(df[df['inse_bolsa_familia'] == 'Sim']))

            st.markdown("---")

            # Gráficos Linha 1
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("Distribuição por Ano/Série")
                fig_serie = px.bar(df, x='ano_serie', title="Alunos por Série", color='ano_serie', text_auto=True)
                st.plotly_chart(fig_serie, use_container_width=True)
            
            with c2:
                st.subheader("Distribuição por Turno")
                fig_turno = px.pie(df, names='turno', title="Preferência de Turno", hole=0.4)
                st.plotly_chart(fig_turno, use_container_width=True)

            # Gráficos Linha 2
            c3, c4 = st.columns(2)
            
            with c3:
                st.subheader("Alunos por Bairro")
                bairros_count = df['bairro'].value_counts().reset_index()
                bairros_count.columns = ['bairro', 'count']
                fig_bairro = px.bar(bairros_count, x='count', y='bairro', orientation='h', title="Top Bairros", color='count')
                st.plotly_chart(fig_bairro, use_container_width=True)

            with c4:
                st.subheader("Perfil Socioeconômico (Raça)")
                fig_raca = px.pie(df, names='inse_raca', title="Autodeclaração de Cor/Raça")
                st.plotly_chart(fig_raca, use_container_width=True)

            st.markdown("---")
            st.subheader("Indicadores de Práticas Familiares")
            
            # Agrupando dados de práticas
            pratica_cols = ['pratica_local_estudo', 'pratica_horario_fixo', 'pratica_acompanhamento_pais']
            for col in pratica_cols:
                fig = px.histogram(df, x=col, title=f"Distribuição: {col.replace('pratica_', '').replace('_', ' ').title()}", color=col)
                st.plotly_chart(fig, use_container_width=True)

    elif page == "Nova Matrícula":
        st.title("📝 Ficha de Matrícula - Ano Letivo 2026")
        
        with st.form("matricula_form"):
            st.header("1. Identificação")
            col1, col2 = st.columns(2)
            nm_estudante = col1.text_input("Nome Completo do Estudante")
            dt_nasc_estudante = col2.date_input("Data de Nascimento do Estudante", min_value=datetime(2000, 1, 1))
            
            col3, col4 = st.columns(2)
            nm_responsavel = col3.text_input("Nome do Responsável")
            dt_nasc_responsavel = col4.date_input("Data de Nascimento do Responsável", min_value=datetime(1950, 1, 1))
            
            col5, col6 = st.columns(2)
            parentesco = col5.selectbox("Parentesco", ["Mãe", "Pai", "Avó/Avô", "Tio/Tia", "Outro"])
            telefone = col6.text_input("Telefone de Contato")
            email = st.text_input("E-mail")

            st.header("2. Endereço")
            col_end1, col_end2 = st.columns([3, 1])
            logradouro = col_end1.text_input("Logradouro (Rua, Av., etc)")
            numero = col_end2.text_input("Número")
            
            col_end3, col_end4, col_end5 = st.columns(3)
            bairro = col_end3.text_input("Bairro")
            municipio = col_end4.text_input("Município")
            cep = col_end5.text_input("CEP")

            st.header("3. Dados Escolares")
            col_esc1, col_esc2 = st.columns(2)
            ano_serie = col_esc1.selectbox("Ano/Série (2026)", [f"{i}º Ano" for i in range(1, 10)])
            turno = col_esc2.radio("Turno Pretendido", ["Manhã", "Tarde"])
            
            col_esc3, col_esc4 = st.columns(2)
            turma = col_esc3.text_input("Turma (se souber, ex: 712)")
            escola_origem = col_esc4.text_input("Escola de Origem")

            st.header("4. INSE (Socioeconômico)")
            col_inse1, col_inse2 = st.columns(2)
            inse_raca = col_inse1.selectbox("Cor/Raça", ["Branca", "Preta", "Parda", "Amarela", "Indígena", "Não declarado"])
            inse_genero = col_inse2.selectbox("Gênero", ["Masculino", "Feminino", "Outro"])
            
            inse_escolaridade_resp1 = st.selectbox("Escolaridade do Responsável 1", ["Não alfabetizado", "Fundamental Incompleto", "Fundamental Completo", "Médio Incompleto", "Médio Completo", "Superior Incompleto", "Superior Completo"])
            inse_escolaridade_resp2 = st.selectbox("Escolaridade do Responsável 2 (Opcional)", ["", "Não alfabetizado", "Fundamental Incompleto", "Fundamental Completo", "Médio Incompleto", "Médio Completo", "Superior Incompleto", "Superior Completo"])
            
            col_inse3, col_inse4 = st.columns(2)
            inse_qtd_pessoas_domicilio = col_inse3.number_input("Qtd. Pessoas no Domicílio", min_value=1, step=1)
            inse_qtd_banheiros = col_inse4.number_input("Qtd. Banheiros", min_value=0, step=1)
            
            inse_bens = st.multiselect("Bens no Domicílio", ["TV", "Geladeira", "Máquina de Lavar", "Carro", "Computador/Notebook", "Internet Wifi", "Ar Condicionado"])
            inse_livros_qtd = st.selectbox("Quantidade aproximada de livros em casa", ["0-10", "11-50", "51-100", "Mais de 100"])
            inse_bolsa_familia = st.radio("Recebe Bolsa Família?", ["Sim", "Não"])

            st.header("5. Práticas Familiares")
            pratica_local_estudo = st.select_slider("O estudante tem local adequado para estudar?", options=["Nunca", "Raramente", "Às vezes", "Frequentemente", "Sempre"])
            pratica_horario_fixo = st.select_slider("O estudante tem horário fixo para estudar?", options=["Nunca", "Raramente", "Às vezes", "Frequentemente", "Sempre"])
            pratica_acompanhamento_pais = st.selectbox("Frequência de acompanhamento dos pais nas tarefas", ["Nunca", "Raramente", "Semanalmente", "Diariamente"])
            pratica_leitura_compartilhada = st.selectbox("Prática de leitura compartilhada", ["Nunca", "Raramente", "Semanalmente", "Diariamente"])
            pratica_conversa_escola = st.selectbox("Conversam sobre a escola?", ["Nunca", "Raramente", "Semanalmente", "Diariamente"])

            st.header("6. Consentimento")
            consentimento_dados = st.checkbox("Declaro que as informações acima são verdadeiras e autorizo o uso dos dados para fins escolares.")

            submitted = st.form_submit_button("💾 Salvar Matrícula")

            if submitted:
                if not consentimento_dados:
                    st.error("É necessário aceitar o termo de consentimento.")
                elif not nm_estudante or not nm_responsavel:
                    st.error("Preencha os campos obrigatórios (Nomes).")
                else:
                    dados = [
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        nm_estudante, str(dt_nasc_estudante), nm_responsavel,
                        str(dt_nasc_responsavel), parentesco, telefone, email,
                        logradouro, numero, bairro, municipio, cep,
                        ano_serie, turno, turma, escola_origem,
                        "Sim" if consentimento_dados else "Não",
                        inse_raca, inse_genero, inse_escolaridade_resp1, inse_escolaridade_resp2,
                        inse_qtd_pessoas_domicilio, inse_qtd_banheiros, ", ".join(inse_bens),
                        inse_livros_qtd, inse_bolsa_familia,
                        pratica_local_estudo, pratica_horario_fixo, pratica_acompanhamento_pais,
                        pratica_leitura_compartilhada, pratica_conversa_escola
                    ]
                    
                    with st.spinner("Salvando dados..."):
                        try:
                            save_data(sh, dados)
                            st.success("✅ Matrícula salva com sucesso!")
                            st.balloons()
                        except Exception as e:
                            st.error(f"Erro ao salvar: {e}")

    elif page == "Administração":
        st.title("⚙️ Painel Administrativo")
        
        st.subheader("Simulação de Dados")
        col_sim1, col_sim2 = st.columns([1, 3])
        qtd_sim = col_sim1.number_input("Qtd. Registros", min_value=1, value=10)
        if col_sim2.button("🤖 Gerar Dados de Teste"):
            with st.spinner(f"Gerando {qtd_sim} matrículas fictícias..."):
                generate_fake_data(sh, qtd_sim)
                st.success("Dados gerados com sucesso! Recarregue a página para ver no Dashboard.")
                st.rerun()

        st.divider()
        
        st.subheader("Gerenciamento de Dados")
        if not df.empty:
            # Editor de Dados
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            
            # Botão para salvar edições
            if st.button("💾 Salvar Alterações na Planilha"):
                with st.spinner("Atualizando planilha Google..."):
                    try:
                        update_all_data(sh, edited_df)
                        st.success("Planilha atualizada com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao atualizar planilha: {e}")

            # Download
            csv = edited_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Dados (CSV)",
                data=csv,
                file_name='matriculas_2026.csv',
                mime='text/csv',
            )
        else:
            st.info("Nenhuma matrícula registrada ainda.")

if __name__ == "__main__":
    main()

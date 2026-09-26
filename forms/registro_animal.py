import re
import streamlit as st
from utils import add_document


def calcular_faixa_etaria(idade_str: str) -> str:
    """
    Calcula automaticamente a faixa etária com base na idade informada.
    Exemplos: '6 meses', '1.5 anos', '3 anos', '10', 'Filhote'
    """
    if not idade_str:
        return ""

    idade_clean = idade_str.strip().lower()

    # Mapeamento direto por palavras-chave
    if "filhote" in idade_clean:
        return "Filhote"
    if "juvenil" in idade_clean or "suvenil" in idade_clean:
        return "Juvenil"
    if "sub" in idade_clean:
        return "Sub Adulto"
    if "adulto" in idade_clean:
        return "Adulto"
    if "senil" in idade_clean or "idoso" in idade_clean:
        return "Senil"

    # Extrai o primeiro número (inteiro ou decimal)
    match = re.search(r"(\d+(?:[\.,]\d+)?)", idade_clean)
    if not match:
        return ""

    num_val = float(match.group(1).replace(",", "."))

    # Identifica a unidade de tempo
    if any(unit in idade_clean for unit in ["mês", "mes", "meses", "m"]):
        anos = num_val / 12.0
    elif any(unit in idade_clean for unit in ["dia", "dias", "d"]):
        anos = num_val / 365.0
    elif any(unit in idade_clean for unit in ["semana", "semanas", "sem"]):
        anos = num_val / 52.0
    else:
        # Padrão: anos
        anos = num_val

    if anos < 1.0:
        return "Filhote"
    elif anos < 2.0:
        return "Juvenil"
    elif anos < 4.0:
        return "Sub Adulto"
    elif anos < 10.0:
        return "Adulto"
    else:
        return "Senil"


@st.dialog("Informações do Animal")
def modal_confirmar_animal(animal_data):
    
    rotulos = {
        "_id": "ID do Animal",
        "animal_id_projeto": "ID do Projeto",
        "classe": "Classe",
        "suspeita_clinica": "Suspeita Clínica",
        "nome_comum": "Nome Comum",
        "nome_cientifico": "Nome Científico",
        "sexo": "Sexo",
        "peso": "Peso (kg)",
        "status": "Status",
        "funcao": "Função",
        "local_origem": "Local de Origem",
        "hvu": "ID HVU",
        "microchip": "Microchip",
        "orgao": "Órgão de Origem",
        "idade": "Idade",
        "faixa_etaria": "Faixa Etária",
        "observacoes": "Observações"
    }

    for k, v in animal_data.items():
        lbl = rotulos.get(k, k)
        st.markdown(f"**{lbl}:** {v}")

    c_canc, c_edit, c_conf = st.columns([1, 1, 1])
    
    with c_canc:
        if st.button("Cancelar", type="secondary", icon=":material/close:", use_container_width=True):
            st.session_state['show_confirm_animal'] = False
            st.session_state['pending_animal_data'] = None
            st.rerun()
            
    with c_edit:
        if st.button("Editar", type="secondary", icon=":material/edit:", use_container_width=True):
            st.session_state['show_confirm_animal'] = False
            st.session_state['pending_animal_data'] = None
            st.rerun()
    
    with c_conf:
            if st.button("Confirmar", type="primary", icon=":material/check:", use_container_width=True):
                success, message = add_document('animais', animal_data)
                if success:
                    st.session_state['show_confirm_animal'] = False
                    st.session_state['pending_animal_data'] = None
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

def render_form_registro_animal():
    st.header("Novo Animal")
    with st.form("form_registro_animal"):

        # --- 🏷️ IDENTIFICAÇÃO DO ANIMAL ---
        st.subheader(":material/label: Identificação")
        col_id1, col_id2, col_id3, col_microchip = st.columns([2, 2, 2, 2])
        
        with col_id1:
            animal_id_input = st.text_input(
                "ID do Animal (único) :red[*]", placeholder="Ex: ANM001")
            err_id = st.empty()
        
        with col_id2:
            animal_id_projeto = st.text_input("ID do Projeto")
        
        with col_id3:
            animal_hvu = st.text_input(
                "ID do HVU (Hospital Veterinário)")
        
        with col_microchip:
            animal_microchip = st.text_input("Microchip")
        
        st.divider()

        # --- 🧬 TAXONOMIA E BIOMETRIA ---
        st.subheader(":material/genetics: Taxonomia & Biometria")
        col_classe, col_nome_comum, col_nome_cientifico, col_sexo = st.columns([2, 2, 2, 2])
        with col_classe:
            animal_classe = st.selectbox(
                'Classe :red[*]', ["", "Ave", "Mamífero", "Répteis", 'Anfíbios', "Peixes"]
            )
            err_classe = st.empty()
        with col_nome_comum:
            animal_nome_comum = st.text_input("Nome Comum :red[*]")
            err_nome_comum = st.empty()
        with col_nome_cientifico:
            animal_nome_cientifico = st.text_input("Nome Científico :red[*]")
            err_nome_cientifico = st.empty()
        with col_sexo:
            animal_sexo = st.selectbox(
                "Sexo :red[*]", ["", "Macho", "Fêmea", "Desconhecido"])
            err_sexo = st.empty()

        col_peso1, col_peso2, col_idade1, col_idade2 = st.columns([2, 2, 2, 2])
        with col_peso1:
            animal_peso_val = st.number_input(
                "Peso (kg) :red[*]", min_value=0.0, format="%.2f", step=0.01,
            )
        with col_peso2:
            st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
            peso_nao_aferido = st.checkbox("Não aferido")
        err_peso = st.empty()
        with col_idade1:
            animal_idade = st.text_input(
                "Idade",
                placeholder="Ex: 2 anos, 6 meses, 1.5"
            )
        with col_idade2:
            animal_faixa_etaria = st.selectbox(
                'Faixa Etária :red[*]',
                ["", "Filhote", "Juvenil", "Sub Adulto", "Adulto", "Senil", "Não Informado"],
                help="Preenchida automaticamente a partir da Idade se deixada em branco"
            )
        err_idade_faixa = st.empty()

        st.divider()

        # --- 📍 ORIGEM E PROCEDÊNCIA ---
        st.subheader(":material/location_on: Origem e Procedência")
        col_orgao, col_local, col_status, col_funcao = st.columns([2, 2, 2, 2])
        with col_orgao:
            animal_orgao = st.selectbox(
                'Órgão de Origem :red[*]', ['', 'UFPI', 'NEPPAS', 'IBAMA - CETAS - PI', 'IBAMA - CETAS - CE', 'IBAMA - CETAS - RN', 'SEMARH - CETAS - PI',
                'UFPA', 'UFRR', 'UFAC', 'UFOB', 'DSEI LESTE - AM', 'ZOOLOGICO -PI', 'PARTICULAR', 'Outro']
            )
            err_orgao = st.empty()
        with col_status:
            animal_status = st.selectbox(
                'Status do Animal :red[*]', ["", "Vida livre", "Cativeiro"]
            )
            err_status = st.empty()
        with col_funcao:
            animal_funcao = st.selectbox(
                'Função :red[*]', ['', "PET", "Trabalho", "Lazer", "Outros"]
            )
            err_funcao = st.empty()
        with col_local:
            animal_local_origem = st.text_input("Local de Origem :red[*]")
            err_local_origem = st.empty()

        st.divider()

        # --- 📋 CLÍNICA E OBSERVAÇÕES ---
        st.subheader(":material/notes: Observações")
        animal_suspeita = st.text_input('Suspeita Clínica')
        animal_observacoes = st.text_area("Observações")
        
        col_space, col_submit = st.columns([3, 1])
        with col_submit:
            submit_animal = st.form_submit_button("Registrar Animal", type="primary", use_container_width=True)

        if submit_animal:
            has_errors = False

            if not animal_id_input:
                err_id.error("Insira um ID único para o animal.")
                has_errors = True
            if not animal_nome_comum:
                err_nome_comum.error("Insira o nome comum do animal.")
                has_errors = True
            if not animal_nome_cientifico:
                err_nome_cientifico.error("Insira o nome científico do animal.")
                has_errors = True
            if not animal_sexo:
                err_sexo.error("Selecione o sexo do animal.")
                has_errors = True

            # Processamento e Validação do Peso
            if peso_nao_aferido:
                animal_peso = "Não aferido"
            elif animal_peso_val > 0.0:
                animal_peso = animal_peso_val
            else:
                err_peso.error("Informe o peso (kg) do animal ou marque 'Não aferido'.")
                animal_peso = None
                has_errors = True

            if not animal_orgao:
                err_orgao.error("Selecione o órgão de origem do animal.")
                has_errors = True
            if not animal_status:
                err_status.error("Selecione o status do animal.")
                has_errors = True
            if not animal_funcao:
                err_funcao.error("Selecione a função do animal.")
                has_errors = True
            if not animal_local_origem:
                err_local_origem.error("Insira o local de origem do animal.")
                has_errors = True

            # Preenchimento automático da Faixa Etária com base na Idade (se a faixa etária não foi selecionada)
            if animal_idade and (not animal_faixa_etaria or animal_faixa_etaria == "Não Informado"):
                faixa_calculada = calcular_faixa_etaria(animal_idade)
                if faixa_calculada:
                    animal_faixa_etaria = faixa_calculada

            # Validação Idade / Faixa Etária
            if not animal_idade and (not animal_faixa_etaria or animal_faixa_etaria in ["", "Não Informado"]):
                err_idade_faixa.error("Informe a idade ou selecione a faixa etária do animal.")
                has_errors = True

            if not animal_classe:
                err_classe.error("Selecione a classe do animal.")
                has_errors = True

            if not has_errors:
                animal_data = {
                    "_id": animal_id_input,
                    'animal_id_projeto': animal_id_projeto,
                    "classe": animal_classe,
                    "suspeita_clinica": animal_suspeita,
                    "nome_comum": animal_nome_comum,
                    "nome_cientifico": animal_nome_cientifico,
                    "sexo": animal_sexo,
                    "peso": animal_peso,
                    "status": animal_status,
                    "funcao": animal_funcao,
                    "local_origem": animal_local_origem,
                    "hvu": animal_hvu,
                    "microchip": animal_microchip,
                    "orgao": animal_orgao,
                    "idade": animal_idade,
                    'faixa_etaria': animal_faixa_etaria,
                    "observacoes": animal_observacoes
                }
                # Remove campos vazios ou nulos antes de inserir
                animal_data = {
                    k: v for k, v in animal_data.items() if v not in (None, "", [])}

                st.session_state['pending_animal_data'] = animal_data
                st.session_state['show_confirm_animal'] = True

    # Se a confirmação foi solicitada, aciona o modal pop-up
    if st.session_state.get('show_confirm_animal') and st.session_state.get('pending_animal_data'):
        modal_confirmar_animal(st.session_state['pending_animal_data'])
import streamlit as st
from statsbombpy import sb
from mplsoccer import Pitch
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


# Configuração da página

st.set_page_config(
    page_title="Seleção do Marrocos - Sports Analytics",
    page_icon="⚽",
    layout="wide"
)


# Funções de carregamento de dados

@st.cache_data
def carregar_competicoes():
    competicoes = sb.competitions()

    competicoes["season_name"] = (
        competicoes["season_name"].astype(str)
    )

    competicoes_marrocos = competicoes[
        (
            (competicoes["competition_name"] == "FIFA World Cup")
            & (competicoes["season_name"].isin(["2018", "2022"]))
        )
        |
        (
            (competicoes["competition_name"] == "African Cup of Nations")
            & (competicoes["season_name"] == "2023")
        )
    ].copy()

    return competicoes_marrocos[
        [
            "competition_id",
            "season_id",
            "competition_name",
            "season_name"
        ]
    ].drop_duplicates()


@st.cache_data
def carregar_partidas(competition_id, season_id):
    partidas = sb.matches(
        competition_id=competition_id,
        season_id=season_id
    )

    partidas_marrocos = partidas[
        (partidas["home_team"] == "Morocco")
        | (partidas["away_team"] == "Morocco")
    ].copy()

    return partidas_marrocos


@st.cache_data
def carregar_eventos(match_id):
    return sb.events(match_id=match_id)


@st.cache_data
def carregar_escalacoes(match_id):
    try:
        return sb.lineups(match_id=match_id)
    except Exception:
        return None


# Funções de cálculo

def calcular_metricas(dados):

    passes = dados[
        dados["type"] == "Pass"
    ]

    passes_completos = passes[
        passes["pass_outcome"].isna()
    ]

    chutes = dados[
        dados["type"] == "Shot"
    ]

    gols = chutes[
        chutes["shot_outcome"] == "Goal"
    ]

    xg = chutes["shot_statsbomb_xg"].sum()

    if len(passes) > 0:
        taxa_passes = (
            len(passes_completos)
            / len(passes)
            * 100
        )
    else:
        taxa_passes = 0

    if len(chutes) > 0:
        taxa_conversao = (
            len(gols)
            / len(chutes)
            * 100
        )
    else:
        taxa_conversao = 0

    return {
        "passes": len(passes),
        "passes_completos": len(passes_completos),
        "taxa_passes": taxa_passes,
        "chutes": len(chutes),
        "gols": len(gols),
        "xg": xg,
        "taxa_conversao": taxa_conversao
    }


# Funções de visualização

def criar_mapa_chutes(dados):

    chutes = dados[
        dados["type"] == "Shot"
    ].copy()

    chutes = chutes[
        chutes["location"].notna()
    ].copy()

    if chutes.empty:
        return None

    chutes[["x", "y"]] = pd.DataFrame(
        chutes["location"].tolist(),
        index=chutes.index
    )

    gols = chutes[
        chutes["shot_outcome"] == "Goal"
    ]

    outros_chutes = chutes[
        chutes["shot_outcome"] != "Goal"
    ]

    pitch = Pitch(
        pitch_type="statsbomb",
        pitch_color="white",
        line_color="black"
    )

    fig, ax = pitch.draw(
        figsize=(10, 7)
    )

    pitch.scatter(
        outros_chutes["x"],
        outros_chutes["y"],
        s=outros_chutes["shot_statsbomb_xg"] * 900 + 70,
        alpha=0.6,
        ax=ax,
        label="Chute"
    )

    pitch.scatter(
        gols["x"],
        gols["y"],
        s=gols["shot_statsbomb_xg"] * 900 + 120,
        marker="*",
        ax=ax,
        label="Gol"
    )

    ax.set_title(
        "Localização dos chutes da Seleção do Marrocos",
        fontsize=14
    )

    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.01, 1)
    )

    return fig


def criar_mapa_passes(dados):

    passes = dados[
        dados["type"] == "Pass"
    ].copy()

    passes = passes[
        passes["location"].notna()
        & passes["pass_end_location"].notna()
    ].copy()

    if passes.empty:
        return None

    passes[["x", "y"]] = pd.DataFrame(
        passes["location"].tolist(),
        index=passes.index
    )

    passes[["end_x", "end_y"]] = pd.DataFrame(
        passes["pass_end_location"].tolist(),
        index=passes.index
    )

    passes_completos = passes[
        passes["pass_outcome"].isna()
    ]

    passes_incompletos = passes[
        passes["pass_outcome"].notna()
    ]

    pitch = Pitch(
        pitch_type="statsbomb",
        pitch_color="white",
        line_color="black"
    )

    fig, ax = pitch.draw(
        figsize=(10, 7)
    )

    pitch.arrows(
        passes_completos["x"],
        passes_completos["y"],
        passes_completos["end_x"],
        passes_completos["end_y"],
        width=1.5,
        headwidth=3,
        headlength=3,
        alpha=0.5,
        ax=ax,
        label="Passe completo"
    )

    pitch.arrows(
        passes_incompletos["x"],
        passes_incompletos["y"],
        passes_incompletos["end_x"],
        passes_incompletos["end_y"],
        width=1.5,
        headwidth=3,
        headlength=3,
        alpha=0.3,
        ax=ax,
        label="Passe incompleto"
    )

    ax.set_title(
        "Mapa de passes da Seleção do Marrocos",
        fontsize=14
    )

    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.01, 1)
    )

    return fig


def criar_heatmap(dados):

    eventos_localizados = dados[
        dados["location"].notna()
    ].copy()

    if eventos_localizados.empty:
        return None

    eventos_localizados[["x", "y"]] = pd.DataFrame(
        eventos_localizados["location"].tolist(),
        index=eventos_localizados.index
    )

    pitch = Pitch(
        pitch_type="statsbomb",
        pitch_color="white",
        line_color="black"
    )

    fig, ax = pitch.draw(
        figsize=(10, 7)
    )

    estatistica = pitch.bin_statistic(
        eventos_localizados["x"],
        eventos_localizados["y"],
        statistic="count",
        bins=(12, 8)
    )

    pitch.heatmap(
        estatistica,
        ax=ax,
        cmap="Reds",
        edgecolors="white"
    )

    ax.set_title(
        "Heatmap das ações da Seleção do Marrocos",
        fontsize=14
    )

    return fig


def criar_grafico_tipos_eventos(dados):

    contagem = (
        dados["type"]
        .value_counts()
        .head(10)
    )

    if contagem.empty:
        return None

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    ax.bar(
        contagem.index,
        contagem.values
    )

    ax.set_title(
        "Eventos mais frequentes da Seleção do Marrocos"
    )

    ax.set_xlabel(
        "Tipo de evento"
    )

    ax.set_ylabel(
        "Quantidade"
    )

    ax.tick_params(
        axis="x",
        rotation=45
    )

    fig.tight_layout()

    return fig


def criar_grafico_participacao(dados):

    eventos_jogadores = dados[
        dados["player"].notna()
    ].copy()

    passes_por_jogador = (
        eventos_jogadores[
            eventos_jogadores["type"] == "Pass"
        ]
        .groupby("player")
        .size()
    )

    chutes_por_jogador = (
        eventos_jogadores[
            eventos_jogadores["type"] == "Shot"
        ]
        .groupby("player")
        .size()
    )

    dados_jogadores = pd.DataFrame({
        "Passes": passes_por_jogador,
        "Chutes": chutes_por_jogador
    }).fillna(0)

    dados_jogadores = (
        dados_jogadores
        .reset_index()
    )

    if dados_jogadores.empty:
        return None

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    sns.scatterplot(
        data=dados_jogadores,
        x="Passes",
        y="Chutes",
        s=100,
        ax=ax
    )

    for _, linha in dados_jogadores.iterrows():

        if linha["Chutes"] > 0:

            ax.annotate(
                linha["player"],
                (
                    linha["Passes"],
                    linha["Chutes"]
                ),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8
            )

    ax.set_title(
        "Relação entre passes e chutes por jogador"
    )

    ax.set_xlabel(
        "Número de passes"
    )

    ax.set_ylabel(
        "Número de chutes"
    )

    fig.tight_layout()

    return fig


# Funções da interface

def exibir_metricas(metricas):

    coluna1, coluna2, coluna3, coluna4 = st.columns(4)

    with coluna1:
        st.metric(
            "Passes",
            metricas["passes"]
        )

    with coluna2:
        st.metric(
            "Passes completos",
            metricas["passes_completos"]
        )

    with coluna3:
        st.metric(
            "Taxa de passes",
            f"{metricas['taxa_passes']:.1f}%"
        )

    with coluna4:
        st.metric(
            "Chutes",
            metricas["chutes"]
        )

    coluna5, coluna6, coluna7 = st.columns(3)

    with coluna5:
        st.metric(
            "Gols",
            metricas["gols"]
        )

    with coluna6:
        st.metric(
            "xG",
            f"{metricas['xg']:.2f}"
        )

    with coluna7:
        st.metric(
            "Conversão de chutes",
            f"{metricas['taxa_conversao']:.1f}%"
        )


def diferenca(valor1, valor2, casas=0):

    diferenca_valor = valor1 - valor2

    if casas == 0:
        return f"{diferenca_valor:+.0f}"

    return f"{diferenca_valor:+.{casas}f}"


def exibir_comparacao(
    nome,
    metricas,
    metricas_adversario
):

    st.write(
        f"### {nome}"
    )

    st.metric(
        "Passes",
        metricas["passes"],
        delta=diferenca(
            metricas["passes"],
            metricas_adversario["passes"]
        )
    )

    st.metric(
        "Passes completos",
        metricas["passes_completos"],
        delta=diferenca(
            metricas["passes_completos"],
            metricas_adversario["passes_completos"]
        )
    )

    st.metric(
        "Taxa de passes",
        f"{metricas['taxa_passes']:.1f}%",
        delta=(
            f"{metricas['taxa_passes'] - metricas_adversario['taxa_passes']:+.1f} p.p."
        )
    )

    st.metric(
        "Chutes",
        metricas["chutes"],
        delta=diferenca(
            metricas["chutes"],
            metricas_adversario["chutes"]
        )
    )

    st.metric(
        "Gols",
        metricas["gols"],
        delta=diferenca(
            metricas["gols"],
            metricas_adversario["gols"]
        )
    )

    st.metric(
        "xG",
        f"{metricas['xg']:.2f}",
        delta=diferenca(
            metricas["xg"],
            metricas_adversario["xg"],
            2
        )
    )

    st.metric(
        "Conversão de chutes",
        f"{metricas['taxa_conversao']:.1f}%",
        delta=(
            f"{metricas['taxa_conversao'] - metricas_adversario['taxa_conversao']:+.1f} p.p."
        )
    )


# Cabeçalho

with st.container():

    st.title(
        "Seleção do Marrocos - Sports Analytics"
    )

    st.caption(
        "Dashboard interativo para análise do desempenho "
        "da Seleção do Marrocos em competições internacionais."
    )

    st.markdown(
        """
        **Pergunta de análise:**  
        Como variou a produção ofensiva da Seleção do Marrocos
        em diferentes competições internacionais?
        """
    )

st.divider()


# Barra de progresso

barra_progresso = st.progress(
    0,
    text="Iniciando carregamento dos dados..."
)


# Carregamento das competições

with st.spinner(
    "Carregando competições..."
):

    competicoes = carregar_competicoes()

barra_progresso.progress(
    20,
    text="Competições carregadas."
)


# Sidebar

st.sidebar.header(
    "Filtros principais"
)

nomes_competicoes = sorted(
    competicoes[
        "competition_name"
    ].unique()
)

if (
    "competicao_selecionada"
    not in st.session_state
    or
    st.session_state[
        "competicao_selecionada"
    ] not in nomes_competicoes
):

    st.session_state[
        "competicao_selecionada"
    ] = nomes_competicoes[0]


competicao_escolhida = st.sidebar.selectbox(
    "Selecione a competição:",
    nomes_competicoes,
    key="competicao_selecionada"
)


# Temporada

temporadas_disponiveis = (
    competicoes[
        competicoes["competition_name"]
        == competicao_escolhida
    ]["season_name"]
    .sort_values()
    .unique()
    .tolist()
)


if (
    "temporada_selecionada"
    not in st.session_state
    or
    st.session_state[
        "temporada_selecionada"
    ] not in temporadas_disponiveis
):

    st.session_state[
        "temporada_selecionada"
    ] = temporadas_disponiveis[0]


temporada_escolhida = st.sidebar.selectbox(
    "Selecione a temporada:",
    temporadas_disponiveis,
    key="temporada_selecionada"
)


configuracao = competicoes[
    (
        competicoes["competition_name"]
        == competicao_escolhida
    )
    &
    (
        competicoes["season_name"]
        == temporada_escolhida
    )
].iloc[0]


competition_id = int(
    configuracao["competition_id"]
)

season_id = int(
    configuracao["season_id"]
)


# Carregamento das partidas

with st.spinner(
    "Carregando partidas..."
):

    partidas_marrocos = carregar_partidas(
        competition_id,
        season_id
    )


barra_progresso.progress(
    40,
    text="Partidas carregadas."
)


# Seleção da partida

partidas_marrocos["partida"] = (
    partidas_marrocos["home_team"]
    + " "
    + partidas_marrocos[
        "home_score"
    ].astype(str)
    + " x "
    + partidas_marrocos[
        "away_score"
    ].astype(str)
    + " "
    + partidas_marrocos["away_team"]
)


opcoes_partidas = (
    partidas_marrocos[
        "partida"
    ].tolist()
)


if (
    "partida_selecionada"
    not in st.session_state
    or
    st.session_state[
        "partida_selecionada"
    ] not in opcoes_partidas
):

    st.session_state[
        "partida_selecionada"
    ] = opcoes_partidas[0]


partida_escolhida = st.sidebar.selectbox(
    "Selecione a partida:",
    opcoes_partidas,
    key="partida_selecionada"
)


linha_partida = partidas_marrocos[
    partidas_marrocos["partida"]
    == partida_escolhida
].iloc[0]


match_id = int(
    linha_partida["match_id"]
)


# Carregamento dos eventos

with st.spinner(
    "Carregando eventos e jogadores..."
):

    eventos = carregar_eventos(
        match_id
    )

    escalacoes = carregar_escalacoes(
        match_id
    )


barra_progresso.progress(
    70,
    text="Eventos carregados."
)


eventos_marrocos = eventos[
    eventos["team"] == "Morocco"
].copy()


# Seleção de jogador

jogadores = sorted(
    eventos_marrocos[
        "player"
    ]
    .dropna()
    .unique()
    .tolist()
)


opcoes_jogadores = [
    "Todos os jogadores"
] + jogadores


if (
    "jogador_selecionado"
    not in st.session_state
    or
    st.session_state[
        "jogador_selecionado"
    ] not in opcoes_jogadores
):

    st.session_state[
        "jogador_selecionado"
    ] = "Todos os jogadores"


jogador_escolhido = st.sidebar.selectbox(
    "Selecione o jogador:",
    opcoes_jogadores,
    key="jogador_selecionado"
)


# Intervalo da partida

minuto_maximo = int(
    eventos_marrocos[
        "minute"
    ].max()
)


st.sidebar.write(
    "**Intervalo da partida:**"
)


if (
    "minuto_inicial"
    not in st.session_state
):

    st.session_state[
        "minuto_inicial"
    ] = 0


if (
    "minuto_final"
    not in st.session_state
):

    st.session_state[
        "minuto_final"
    ] = minuto_maximo


if (
    st.session_state[
        "minuto_inicial"
    ] > minuto_maximo
):

    st.session_state[
        "minuto_inicial"
    ] = 0


if (
    st.session_state[
        "minuto_final"
    ] > minuto_maximo
):

    st.session_state[
        "minuto_final"
    ] = minuto_maximo


minuto_inicial = st.sidebar.number_input(
    "Minuto inicial",
    min_value=0,
    max_value=minuto_maximo,
    step=1,
    key="minuto_inicial"
)


minuto_final = st.sidebar.number_input(
    "Minuto final",
    min_value=0,
    max_value=minuto_maximo,
    step=1,
    key="minuto_final"
)


if minuto_inicial > minuto_final:

    st.sidebar.warning(
        "O minuto inicial deve ser menor "
        "ou igual ao minuto final."
    )

    minuto_inicial = minuto_final


# Aplicação dos filtros

eventos_intervalo = eventos_marrocos[
    (
        eventos_marrocos["minute"]
        >= minuto_inicial
    )
    &
    (
        eventos_marrocos["minute"]
        <= minuto_final
    )
].copy()


eventos_filtrados = (
    eventos_intervalo.copy()
)


if (
    jogador_escolhido
    != "Todos os jogadores"
):

    eventos_filtrados = (
        eventos_filtrados[
            eventos_filtrados[
                "player"
            ]
            == jogador_escolhido
        ].copy()
    )


barra_progresso.progress(
    100,
    text="Dados prontos para análise."
)


# Abas

(
    aba_resumo,
    aba_chutes,
    aba_passes,
    aba_adicionais,
    aba_comparacao,
    aba_eventos
) = st.tabs(
    [
        "Resumo",
        "Mapa de chutes",
        "Mapa de passes",
        "Análises adicionais",
        "Comparação de jogadores",
        "Eventos"
    ]
)


# Aba resumo

with aba_resumo:

    with st.container():

        st.subheader(
            "Resumo da partida"
        )

        st.write(
            f"**Competição:** "
            f"{competicao_escolhida}"
        )

        st.write(
            f"**Temporada:** "
            f"{temporada_escolhida}"
        )

        st.write(
            f"**Partida:** "
            f"{linha_partida['home_team']} "
            f"{linha_partida['home_score']} x "
            f"{linha_partida['away_score']} "
            f"{linha_partida['away_team']}"
        )

    st.divider()

    metricas_partida = calcular_metricas(
        eventos_marrocos
    )

    exibir_metricas(
        metricas_partida
    )


    if (
        jogador_escolhido
        != "Todos os jogadores"
    ):

        st.divider()

        st.subheader(
            "Resumo do jogador"
        )

        st.write(
            f"**{jogador_escolhido}**"
        )

        metricas_jogador = (
            calcular_metricas(
                eventos_filtrados
            )
        )

        exibir_metricas(
            metricas_jogador
        )


# Aba mapa de chutes

with aba_chutes:

    st.subheader(
        "Mapa de chutes"
    )

    st.caption(
        f"Eventos entre os minutos "
        f"{minuto_inicial} e "
        f"{minuto_final}."
    )

    fig_chutes = criar_mapa_chutes(
        eventos_filtrados
    )

    if fig_chutes is not None:

        st.pyplot(
            fig_chutes
        )

    else:

        st.info(
            "Não há chutes registrados "
            "para os filtros selecionados."
        )

    st.caption(
        "O tamanho dos pontos representa "
        "o xG de cada finalização. "
        "As estrelas representam gols."
    )


# Aba mapa de passes

with aba_passes:

    st.subheader(
        "Mapa de passes"
    )

    st.caption(
        f"Eventos entre os minutos "
        f"{minuto_inicial} e "
        f"{minuto_final}."
    )

    fig_passes = criar_mapa_passes(
        eventos_filtrados
    )

    if fig_passes is not None:

        st.pyplot(
            fig_passes
        )

    else:

        st.info(
            "Não há passes registrados "
            "para os filtros selecionados."
        )

    st.caption(
        "As setas representam a origem "
        "e o destino de cada passe."
    )


# Aba análises adicionais

with aba_adicionais:

    st.subheader(
        "Heatmap de ações"
    )

    st.write(
        "O heatmap mostra as regiões do campo "
        "com maior concentração de ações."
    )

    fig_heatmap = criar_heatmap(
        eventos_filtrados
    )

    if fig_heatmap is not None:

        st.pyplot(
            fig_heatmap
        )

    else:

        st.info(
            "Não há eventos com localização "
            "para os filtros selecionados."
        )


    st.divider()


    st.subheader(
        "Frequência dos eventos"
    )

    st.write(
        "Visualização criada com Matplotlib."
    )

    fig_eventos = (
        criar_grafico_tipos_eventos(
            eventos_filtrados
        )
    )

    if fig_eventos is not None:

        st.pyplot(
            fig_eventos
        )


    st.divider()


    st.subheader(
        "Participação ofensiva dos jogadores"
    )

    st.write(
        "Visualização criada com Seaborn."
    )

    fig_participacao = (
        criar_grafico_participacao(
            eventos_intervalo
        )
    )

    if fig_participacao is not None:

        st.pyplot(
            fig_participacao
        )

    else:

        st.info(
            "Não há dados suficientes "
            "para esta visualização."
        )


# Aba comparação de jogadores

with aba_comparacao:

    st.subheader(
        "Comparação entre jogadores"
    )

    if len(jogadores) >= 2:

        if (
            "comparacao_jogador_1"
            not in st.session_state
            or
            st.session_state[
                "comparacao_jogador_1"
            ] not in jogadores
        ):

            st.session_state[
                "comparacao_jogador_1"
            ] = jogadores[0]


        if (
            "comparacao_jogador_2"
            not in st.session_state
            or
            st.session_state[
                "comparacao_jogador_2"
            ] not in jogadores
        ):

            st.session_state[
                "comparacao_jogador_2"
            ] = jogadores[1]


        with st.form(
            "form_comparacao"
        ):

            coluna1, coluna2 = (
                st.columns(2)
            )

            with coluna1:

                jogador_1 = (
                    st.selectbox(
                        "Jogador 1",
                        jogadores,
                        key="comparacao_jogador_1"
                    )
                )

            with coluna2:

                jogador_2 = (
                    st.selectbox(
                        "Jogador 2",
                        jogadores,
                        key="comparacao_jogador_2"
                    )
                )


            comparar = (
                st.form_submit_button(
                    "Comparar jogadores"
                )
            )


        dados_jogador_1 = (
            eventos_intervalo[
                eventos_intervalo[
                    "player"
                ]
                == jogador_1
            ]
        )

        dados_jogador_2 = (
            eventos_intervalo[
                eventos_intervalo[
                    "player"
                ]
                == jogador_2
            ]
        )


        metricas_1 = calcular_metricas(
            dados_jogador_1
        )

        metricas_2 = calcular_metricas(
            dados_jogador_2
        )


        if jogador_1 == jogador_2:

            st.info(
                "Selecione dois jogadores "
                "diferentes para realizar "
                "a comparação."
            )

        else:

            st.caption(
                "Os indicadores coloridos mostram "
                "a diferença entre os dois jogadores. "
                "Valores positivos aparecem destacados "
                "em verde e valores negativos em vermelho."
            )

            coluna1, coluna2 = (
                st.columns(2)
            )

            with coluna1:

                exibir_comparacao(
                    jogador_1,
                    metricas_1,
                    metricas_2
                )

            with coluna2:

                exibir_comparacao(
                    jogador_2,
                    metricas_2,
                    metricas_1
                )

    else:

        st.info(
            "Não há jogadores suficientes "
            "para realizar uma comparação."
        )


# Aba eventos

with aba_eventos:

    st.subheader(
        "Eventos da Seleção do Marrocos"
    )

    st.write(
        "Utilize o formulário abaixo para "
        "filtrar os eventos exibidos."
    )


    with st.form(
        "form_eventos"
    ):

        quantidade_eventos = (
            st.number_input(
                "Quantidade de eventos a visualizar",
                min_value=5,
                max_value=500,
                value=50,
                step=5
            )
        )


        busca = st.text_input(
            "Buscar jogador ou tipo de evento"
        )


        tipo_visualizacao = st.radio(
            "Tipo de evento",
            [
                "Todos os eventos",
                "Eventos ofensivos",
                "Eventos defensivos"
            ]
        )


        apenas_localizados = (
            st.checkbox(
                "Mostrar apenas eventos "
                "com localização no campo"
            )
        )


        aplicar_filtros = (
            st.form_submit_button(
                "Aplicar filtros"
            )
        )


    tabela_eventos = (
        eventos_filtrados.copy()
    )


    if (
        tipo_visualizacao
        == "Eventos ofensivos"
    ):

        tabela_eventos = (
            tabela_eventos[
                tabela_eventos[
                    "type"
                ].isin(
                    [
                        "Pass",
                        "Shot",
                        "Carry",
                        "Dribble"
                    ]
                )
            ]
        )


    elif (
        tipo_visualizacao
        == "Eventos defensivos"
    ):

        filtro_defensivo = (
            tabela_eventos[
                "type"
            ].isin(
                [
                    "Interception",
                    "Ball Recovery",
                    "Clearance",
                    "Pressure"
                ]
            )
        )


        if (
            "duel_type"
            in tabela_eventos.columns
        ):

            filtro_desarme = (
                (
                    tabela_eventos[
                        "type"
                    ] == "Duel"
                )
                &
                (
                    tabela_eventos[
                        "duel_type"
                    ] == "Tackle"
                )
            )

            filtro_defensivo = (
                filtro_defensivo
                | filtro_desarme
            )


        tabela_eventos = (
            tabela_eventos[
                filtro_defensivo
            ]
        )


    if apenas_localizados:

        tabela_eventos = (
            tabela_eventos[
                tabela_eventos[
                    "location"
                ].notna()
            ]
        )


    if busca.strip() != "":

        busca_normalizada = (
            busca.strip().lower()
        )

        filtro_busca = (
            tabela_eventos[
                "player"
            ]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.contains(
                busca_normalizada,
                regex=False
            )
            |
            tabela_eventos[
                "type"
            ]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.contains(
                busca_normalizada,
                regex=False
            )
        )

        tabela_eventos = (
            tabela_eventos[
                filtro_busca
            ]
        )


    colunas_tabela = [
        coluna
        for coluna in
        [
            "minute",
            "second",
            "player",
            "type",
            "location",
            "pass_end_location",
            "shot_outcome",
            "duel_type"
        ]
        if coluna
        in tabela_eventos.columns
    ]


    tabela_exibicao = (
        tabela_eventos[
            colunas_tabela
        ]
        .head(
            int(
                quantidade_eventos
            )
        )
        .copy()
    )


    st.write(
        f"**Eventos encontrados:** "
        f"{len(tabela_eventos)}"
    )


    st.dataframe(
        tabela_exibicao,
        use_container_width=True,
        hide_index=True
    )


    csv = tabela_eventos.to_csv(
        index=False
    ).encode(
        "utf-8"
    )


    st.download_button(
        label="Baixar dados filtrados em CSV",
        data=csv,
        file_name="eventos_marrocos.csv",
        mime="text/csv"
    )
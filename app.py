"""Aplicación Streamlit del Planificador Inteligente de Cobertura Móvil."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import pydeck as pdk
import streamlit as st

from coverage_planner.constants import OPERATORS, PRIORITY_WEIGHTS, PROCESSED_DATA, SOURCE_PAGE
from coverage_planner.data import load_processed
from coverage_planner.optimization import OptimizationResult, solve_max_coverage
from coverage_planner.rf import LinkBudget, estimate_radius_km, path_loss

st.set_page_config(
    page_title="Planificador de cobertura móvil | Perú",
    page_icon="📡",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
    [data-testid="stMetricValue"] {font-size: 1.75rem;}
    .small-note {color: #5f6b7a; font-size: 0.88rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Cargando 108 mil centros poblados...")
def get_data() -> pd.DataFrame:
    return load_processed(PROCESSED_DATA)


def colorize(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["color"] = [
        [220, 53, 69, 190]
        if score >= 70
        else [245, 158, 11, 185]
        if score >= 45
        else [25, 135, 84, 175]
        for score in result["priority_score"]
    ]
    return result


def point_map(
    points: pd.DataFrame,
    selected_sites: pd.DataFrame | None = None,
    radius_km: float | None = None,
) -> pdk.Deck:
    display = colorize(points)
    if len(display) > 20_000:
        display = display.nlargest(20_000, "priority_score")

    layers: list[pdk.Layer] = [
        pdk.Layer(
            "ScatterplotLayer",
            display,
            get_position="[longitude, latitude]",
            get_fill_color="color",
            get_radius=110,
            radius_min_pixels=2,
            radius_max_pixels=8,
            pickable=True,
        )
    ]
    if selected_sites is not None and not selected_sites.empty:
        sites = selected_sites.copy()
        sites["radius_m"] = float(radius_km or 0) * 1_000
        layers.extend(
            [
                pdk.Layer(
                    "ScatterplotLayer",
                    sites,
                    get_position="[longitude, latitude]",
                    get_fill_color=[28, 86, 181, 42],
                    get_line_color=[28, 86, 181, 220],
                    get_radius="radius_m",
                    stroked=True,
                    line_width_min_pixels=2,
                    pickable=False,
                ),
                pdk.Layer(
                    "ScatterplotLayer",
                    sites,
                    get_position="[longitude, latitude]",
                    get_fill_color=[22, 55, 110, 255],
                    get_radius=220,
                    radius_min_pixels=7,
                    radius_max_pixels=13,
                    pickable=True,
                ),
            ]
        )

    center_latitude = float(display["latitude"].median())
    center_longitude = float(display["longitude"].median())
    zoom = 7 if display["province"].nunique() == 1 else 4.3
    return pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(
            latitude=center_latitude,
            longitude=center_longitude,
            zoom=zoom,
            pitch=0,
        ),
        map_style="light",
        tooltip={
            "html": (
                "<b>{center_name}</b><br/>{district}, {province}<br/>"
                "Prioridad: <b>{priority_score}</b><br/>"
                "4G garantizada máx.: {max_4g_cg}<br/>"
                "4G total máx.: {max_4g_total}"
            )
        },
    )


def select_scope(data: pd.DataFrame) -> pd.DataFrame:
    departments = sorted(data["department"].unique())
    default_department = departments.index("LIMA") if "LIMA" in departments else 0
    department = st.sidebar.selectbox("Departamento", departments, index=default_department)
    department_data = data[data["department"].eq(department)]

    provinces = sorted(department_data["province"].unique())
    default_province = provinces.index("HUAROCHIRI") if "HUAROCHIRI" in provinces else 0
    province = st.sidebar.selectbox("Provincia", provinces, index=default_province)
    province_data = department_data[department_data["province"].eq(province)]

    districts = ["TODOS"] + sorted(province_data["district"].unique())
    district = st.sidebar.selectbox("Distrito", districts)
    if district != "TODOS":
        province_data = province_data[province_data["district"].eq(district)]
    return province_data.copy()


def link_budget_controls(prefix: str = "") -> tuple[str, float, str, float, float, LinkBudget]:
    model_label = st.selectbox(
        "Modelo",
        ["Okumura-Hata", "COST-231 Hata", "Espacio libre (FSPL)"],
        key=f"{prefix}model",
    )
    model = {
        "Okumura-Hata": "hata",
        "COST-231 Hata": "cost231",
        "Espacio libre (FSPL)": "fspl",
    }[model_label]
    default_frequency = 850.0 if model == "hata" else 1800.0
    min_frequency, max_frequency = (
        (150.0, 1500.0) if model == "hata" else (1500.0, 2000.0)
    )
    if model == "fspl":
        min_frequency, max_frequency = 100.0, 6000.0
    frequency = st.number_input(
        "Frecuencia (MHz)",
        min_value=min_frequency,
        max_value=max_frequency,
        value=default_frequency,
        step=50.0,
        key=f"{prefix}frequency",
    )
    environment = st.selectbox(
        "Entorno", ["rural", "suburban", "urban"], key=f"{prefix}environment"
    )
    base_height = st.number_input(
        "Altura de estación (m)", 30.0, 200.0, 40.0, 5.0, key=f"{prefix}height"
    )
    mobile_height = st.number_input(
        "Altura del receptor (m)", 1.0, 10.0, 1.5, 0.5, key=f"{prefix}mobile_height"
    )

    with st.expander("Presupuesto de enlace"):
        tx_power = st.number_input(
            "Potencia TX (dBm)", 0.0, 60.0, 43.0, 1.0, key=f"{prefix}tx_power"
        )
        tx_gain = st.number_input(
            "Ganancia TX (dBi)", 0.0, 30.0, 15.0, 1.0, key=f"{prefix}tx_gain"
        )
        tx_losses = st.number_input(
            "Pérdidas TX (dB)", 0.0, 20.0, 3.0, 1.0, key=f"{prefix}tx_losses"
        )
        sensitivity = st.number_input(
            "Sensibilidad RX (dBm)", -130.0, -60.0, -100.0, 1.0, key=f"{prefix}sensitivity"
        )
        margin = st.number_input(
            "Margen de desvanecimiento (dB)", 0.0, 40.0, 10.0, 1.0, key=f"{prefix}margin"
        )
    budget = LinkBudget(
        tx_power_dbm=tx_power,
        tx_gain_dbi=tx_gain,
        tx_losses_db=tx_losses,
        receiver_sensitivity_dbm=sensitivity,
        fade_margin_db=margin,
    )
    return model, frequency, environment, base_height, mobile_height, budget


data = get_data()
st.title("📡 Planificador inteligente de cobertura móvil")
st.caption(
    "Exploración territorial con datos declarados por las operadoras a OSIPTEL, "
    "escenarios RF interpretables y optimización de sitios candidatos."
)

st.sidebar.header("Alcance geográfico")
scope = select_scope(data)
st.sidebar.markdown(
    f"**{len(scope):,}** centros poblados seleccionados".replace(",", " ")
)
st.sidebar.warning(
    "La prioridad es territorial. La fuente no contiene población por centro poblado."
)

tab_overview, tab_rf, tab_optimizer, tab_method = st.tabs(
    ["Brechas", "Simulador RF", "Optimizador", "Metodología"]
)

with tab_overview:
    critical = int(scope["coverage_category"].eq("BRECHA CRITICA").sum())
    guaranteed = float(scope["has_4g_guaranteed"].mean())
    five_g = float(scope["has_5g_total"].mean())
    rural = float(scope["classification"].eq("RURAL").mean())
    columns = st.columns(4)
    columns[0].metric("Centros poblados", f"{len(scope):,}".replace(",", " "))
    columns[1].metric("Brecha 4G crítica", f"{critical:,}".replace(",", " "))
    columns[2].metric("4G garantizada ≥80 %", f"{guaranteed:.1%}")
    columns[3].metric("Centros rurales", f"{rural:.1%}")

    st.pydeck_chart(point_map(scope), width="stretch")
    st.caption(
        "Rojo: prioridad ≥70; ámbar: 45-69,99; verde: <45. "
        "El mapa muestra como máximo los 20 mil puntos de mayor prioridad."
    )

    left, right = st.columns(2)
    category_counts = (
        scope["coverage_category"].value_counts().rename_axis("categoría").reset_index(name="centros")
    )
    left.plotly_chart(
        px.bar(
            category_counts,
            x="categoría",
            y="centros",
            color="categoría",
            color_discrete_map={
                "BRECHA CRITICA": "#dc3545",
                "COBERTURA PARCIAL": "#f59e0b",
                "COBERTURA ALTA": "#198754",
            },
            title="Cobertura 4G total por centro poblado",
        ),
        width="stretch",
    )
    operator_rows = []
    for operator in OPERATORS:
        operator_rows.append(
            {
                "operador": operator.title(),
                "4G garantizada promedio": scope[f"{operator}_4g_cg"].mean(),
                "4G total promedio": scope[f"{operator}_4g_total"].mean(),
            }
        )
    operator_frame = pd.DataFrame(operator_rows).melt(
        id_vars="operador", var_name="métrica", value_name="cobertura"
    )
    right.plotly_chart(
        px.bar(
            operator_frame,
            x="operador",
            y="cobertura",
            color="métrica",
            barmode="group",
            range_y=[0, 1],
            title="Cobertura media declarada por operador",
        ),
        width="stretch",
    )
    st.metric("Centros con 5G total ≥80 %", f"{five_g:.1%}")
    st.subheader("Ranking territorial")
    ranking_columns = [
        "center_name",
        "district",
        "classification",
        "priority_score",
        "max_4g_cg",
        "max_4g_total",
        "max_5g_total",
        "operator_count_4g_total",
    ]
    st.dataframe(
        scope.nlargest(100, "priority_score")[ranking_columns],
        width="stretch",
        hide_index=True,
    )

with tab_rf:
    st.subheader("Escenario de propagación")
    controls, chart = st.columns([1, 2])
    with controls:
        model, frequency, environment, base_height, mobile_height, budget = link_budget_controls(
            "rf_"
        )
        radius = estimate_radius_km(
            model,
            frequency,
            budget,
            base_height,
            mobile_height,
            environment,
        )
        st.metric("Pérdida máxima admisible", f"{budget.max_path_loss_db:.1f} dB")
        st.metric("Radio teórico", f"{radius:.2f} km")

    with chart:
        lower = 0.01 if model == "fspl" else 1.0
        upper = 100.0 if model == "fspl" else 20.0
        distances = np.geomspace(lower, upper, 160)
        losses = path_loss(
            model,
            frequency,
            distances,
            base_height,
            mobile_height,
            environment,
        )
        curve = pd.DataFrame({"distancia_km": distances, "pérdida_db": losses})
        figure = px.line(
            curve,
            x="distancia_km",
            y="pérdida_db",
            log_x=True,
            title="Pérdida de propagación",
        )
        figure.add_hline(
            y=budget.max_path_loss_db,
            line_dash="dash",
            annotation_text="Límite del enlace",
        )
        st.plotly_chart(figure, width="stretch")

    candidate_names = (
        scope.nlargest(min(200, len(scope)), "priority_score")
        .assign(label=lambda frame: frame["center_name"] + " · " + frame["district"])
        .drop_duplicates("label")
    )
    selected_label = st.selectbox("Centro candidato", candidate_names["label"].tolist())
    selected_center = candidate_names[candidate_names["label"].eq(selected_label)].head(1)
    st.pydeck_chart(
        point_map(scope, selected_sites=selected_center, radius_km=radius),
        width="stretch",
    )
    st.info(
        "El círculo es un escenario homogéneo. No modela relieve, azimut, tilt, "
        "sectores, interferencia ni carga de red."
    )

with tab_optimizer:
    st.subheader("Selección óptima de sitios candidatos")
    st.write(
        "El modelo maximiza la suma de prioridad territorial cubierta bajo un límite "
        "de estaciones. Los centros de mayor brecha forman el conjunto candidato."
    )
    if len(scope) > 3_000:
        st.warning("Seleccione una provincia o distrito con hasta 3 000 centros para optimizar.")
    else:
        option_columns = st.columns(3)
        n_sites = option_columns[0].slider("Número máximo de estaciones", 1, 12, 5)
        radius_km = option_columns[1].slider("Radio de escenario (km)", 1.0, 20.0, 6.0, 0.5)
        candidate_upper = min(200, len(scope))
        candidate_lower = min(20, candidate_upper)
        candidate_default = min(120, candidate_upper)
        candidate_step = 10 if candidate_upper >= 30 else 1
        max_candidates = option_columns[2].slider(
            "Sitios candidatos",
            candidate_lower,
            candidate_upper,
            candidate_default,
            candidate_step,
        )

        if st.button("Optimizar ubicaciones", type="primary"):
            with st.spinner("Resolviendo el problema de máxima cobertura..."):
                result: OptimizationResult = solve_max_coverage(
                    scope,
                    n_sites=n_sites,
                    radius_km=radius_km,
                    max_candidates=max_candidates,
                )
            metrics = st.columns(4)
            metrics[0].metric("Estado", result.status)
            metrics[1].metric("Sitios", len(result.selected_sites))
            metrics[2].metric("Centros alcanzados", len(result.covered_centers))
            metrics[3].metric("Prioridad atendida", f"{result.coverage_rate:.1%}")
            st.pydeck_chart(
                point_map(scope, result.selected_sites, radius_km),
                width="stretch",
            )
            selected_columns = [
                "site_number",
                "center_name",
                "district",
                "classification",
                "priority_score",
                "latitude",
                "longitude",
            ]
            st.dataframe(
                result.selected_sites[selected_columns],
                hide_index=True,
                width="stretch",
            )
            st.download_button(
                "Descargar sitios propuestos",
                result.selected_sites[selected_columns].to_csv(index=False).encode("utf-8-sig"),
                file_name="sitios_propuestos.csv",
                mime="text/csv",
            )

with tab_method:
    st.subheader("Metodología y límites")
    st.markdown(
        f"""
        **Fuente principal:** [OSIPTEL — Porcentaje de cobertura móvil por centro
        poblado, empresa y tecnología]({SOURCE_PAGE}).

        La fuente diferencia:

        - **CG:** cobertura garantizada, sujeta a condiciones de calidad declaradas.
        - **CG+CAR:** cobertura total, formada por la garantizada más capacidad adicional
          de red, cuyo desempeño puede variar.

        **Índice de prioridad territorial (0-100):**

        - {PRIORITY_WEIGHTS['guaranteed_4g_gap']:.0%}: brecha de 4G garantizada.
        - {PRIORITY_WEIGHTS['total_4g_gap']:.0%}: brecha de 4G total.
        - {PRIORITY_WEIGHTS['total_5g_gap']:.0%}: brecha de 5G total.
        - {PRIORITY_WEIGHTS['competition_gap']:.0%}: baja diversidad de operadores 4G.
        - {PRIORITY_WEIGHTS['rural_priority']:.0%}: prioridad rural explícita.

        El índice **no usa población** y no debe interpretarse como impacto económico.
        Los modelos RF no consideran terreno ni parámetros confidenciales de red. Las
        ubicaciones propuestas son un ejercicio académico de prefactibilidad.
        """
    )

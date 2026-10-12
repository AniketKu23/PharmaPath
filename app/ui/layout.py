"""PharmaPath Responsive Layout & UI Component Utilities."""

from __future__ import annotations

from pathlib import Path
import yaml
import pandas as pd
import streamlit as st

from app.ui.styles import inject_mobile_styles

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "params.yaml"


@st.cache_data
def load_app_params() -> dict:
    """Load cached application parameters from config/params.yaml."""
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def init_page(title: str, icon: str = "🧬") -> None:
    """Initialize page configuration and responsive styles.

    Collapses initial sidebar on mobile devices so it doesn't block the screen,
    and injects responsive CSS.
    """
    st.set_page_config(
        page_title=f"{title} | PharmaPath",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_mobile_styles()


def render_filter_expander(title: str = "⚙️ Controls & Filters", active_summary: str = "") -> st.expander:
    """Render a prominent collapsible filter expander at the top of the page.

    Provides high visibility for mobile users who cannot easily discover the hidden sidebar.
    """
    label = f"{title} — {active_summary}" if active_summary else title
    return st.expander(label, expanded=False)


def render_responsive_dataframe(
    df: pd.DataFrame,
    key_columns: list[str] | None = None,
    download_filename: str = "pharmapath_export.csv",
    key_prefix: str = "df",
) -> None:
    """Render a mobile-friendly dataframe with column pruning and CSV export.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe to display.
    key_columns : list[str], optional
        Priority columns to show by default on mobile.
    download_filename : str
        Filename for the CSV export button.
    key_prefix : str
        Unique key prefix for Streamlit widgets.
    """
    if df is None or df.empty:
        st.info("No data available to display.")
        return

    col1, col2 = st.columns([3, 1])
    with col2:
        st.download_button(
            label="📥 Export CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=download_filename,
            mime="text/csv",
            key=f"{key_prefix}_dl_btn",
            use_container_width=True,
        )

    all_cols = list(df.columns)
    if key_columns and set(key_columns).issubset(set(all_cols)) and len(key_columns) < len(all_cols):
        show_all = col1.checkbox(
            f"Show all {len(all_cols)} columns (currently showing {len(key_columns)} key columns)",
            value=False,
            key=f"{key_prefix}_show_all",
        )
        display_df = df if show_all else df[key_columns]
    else:
        display_df = df

    st.dataframe(
        display_df,
        use_container_width=True,
        height=min(400, 38 * (len(display_df) + 1)),
    )


def format_plotly_figure(
    fig,
    height: int = 380,
    legend_orientation: str = "h",
):
    """Format Plotly figure for optimal mobile and tablet rendering."""
    fig.update_layout(
        autosize=True,
        height=height,
        margin=dict(l=25, r=20, t=35, b=35),
        legend=dict(
            orientation=legend_orientation,
            yanchor="bottom",
            y=1.02 if legend_orientation == "h" else 0.5,
            xanchor="center" if legend_orientation == "h" else "left",
            x=0.5 if legend_orientation == "h" else 1.02,
            font=dict(size=11),
        ),
        font=dict(size=12),
        hoverlabel=dict(font_size=12),
    )
    return fig

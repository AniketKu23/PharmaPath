"""PharmaPath UI Styling and Responsive Injection Helper."""

from __future__ import annotations

import textwrap
from pathlib import Path
import streamlit as st

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
_CSS_FILE = _STATIC_DIR / "mobile.css"


@st.cache_data
def _load_mobile_css() -> str:
    """Load and cache the mobile responsive stylesheet."""
    if _CSS_FILE.exists():
        return _CSS_FILE.read_text(encoding="utf-8")
    return ""


def inject_mobile_styles() -> None:
    """Inject responsive CSS and mobile viewport optimizations into the page."""
    css_content = _load_mobile_css()
    if css_content:
        st.markdown(f"<style>\n{css_content}\n</style>", unsafe_allow_html=True)


def render_metric_grid(metrics: list[dict[str, str]]) -> None:
    """Render metrics in a responsive 2-per-row grid on mobile/tablet.

    Parameters
    ----------
    metrics : list of dict
        Each dict must have keys: 'label', 'value', and optional 'delta'.
    """
    for i in range(0, len(metrics), 2):
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label=metrics[i].get("label", ""),
                value=metrics[i].get("value", ""),
                delta=metrics[i].get("delta"),
            )
        if i + 1 < len(metrics):
            with col2:
                st.metric(
                    label=metrics[i + 1].get("label", ""),
                    value=metrics[i + 1].get("value", ""),
                    delta=metrics[i + 1].get("delta"),
                )


def render_ascii_box(content: str) -> None:
    """Render wide ASCII architecture diagrams inside a safe horizontal scroll container."""
    html_block = (
        '<div class="pp-ascii-container">'
        f'<pre style="margin:0; padding:4px; overflow-x:auto;"><code>{content}</code></pre>'
        '</div>'
    )
    st.markdown(html_block, unsafe_allow_html=True)


def render_back_to_top() -> None:
    """Render a persistent, non-intrusive 'Back to top' floating button."""
    button_html = (
        '<div style="margin-top: 2rem; margin-bottom: 1rem; text-align: center;">'
        '<a href="#top" class="pp-back-to-top" onclick="window.scrollTo({top: 0, behavior: \'smooth\'}); return false;">'
        '⬆ Back to Top'
        '</a>'
        '</div>'
    )
    st.markdown(button_html, unsafe_allow_html=True)

from pathlib import Path

import streamlit as st

DESIGN_FILE = Path(__file__).resolve().parents[1] / "assets" / "jobtalk-final.html"
FRAME_HEAD = """<head>
<base href="about:srcdoc">
<style>
body:has([data-view=explore]:not([hidden]) #explore-dock:not([hidden]), [data-view=roadmap]:not([hidden])) > .jobtalk-editor {
    top: 60px;
    bottom: auto;
}
</style>
"""
EDITOR_HOST = "\n  const host = document.createElement('aside');"
RESOURCE_LOOKUP = "\n    const requestKey = `${kind}:${key}`;"

# Fragment links stay inside the iframe. Move the edit controls clear of the selection tray.
html = DESIGN_FILE.read_text(encoding="utf-8")
html = html.replace("<head>", FRAME_HEAD, 1)
html = html.replace(EDITOR_HOST, EDITOR_HOST + '\n  host.className = "jobtalk-editor";', 1)

# The standalone demo's optional resource server is separate from Streamlit.
html = html.replace('<script src="roadmap-data.js"></script>', "", 1)
html = html.replace(
    RESOURCE_LOOKUP,
    '\n    if (location.href.startsWith("about:srcdoc")) {\n'
    '      if (!snapshot) renderRoadmapResource(node, null);\n'
    '      return;\n'
    '    }' + RESOURCE_LOOKUP,
    1,
)

st.html("""
<style>
.st-key-jobtalk-final iframe {
    display: block;
    width: 100%;
    height: max(360px, calc(100dvh - 7rem));
    border: 0;
}
</style>
""")
with st.container(key="jobtalk-final", gap=None):
    st.page_link("app_pages/home.py", label="기존 데이터 연동 앱", icon=":material/open_in_new:")
    st.iframe(html, height=720, alt="잡담 진로 탐색과 별자리 로드맵")

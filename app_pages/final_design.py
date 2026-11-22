from pathlib import Path

import streamlit as st

from utils import design_backend, llm

DESIGN_FILE = Path(__file__).resolve().parents[1] / "assets" / "jobtalk-final.html"
FRAME_HEAD = """<head>
<base href="about:srcdoc">
<style>
body:has([data-view=explore]:not([hidden]) #explore-dock:not([hidden]), [data-view=roadmap]:not([hidden])) > .jobtalk-editor {
    top: 60px;
    bottom: auto;
}
#jobtalk-api-panel{position:relative;color:var(--ink);font-size:.8rem;flex:none}
#jobtalk-api-panel summary{cursor:pointer;padding:7px;border:1px solid #47493c;border-radius:8px}
#jobtalk-api-list{position:absolute;z-index:20;right:0;top:100%;width:min(330px,85vw);max-height:65vh;overflow:auto;padding:10px;background:#171911;border:1px solid #575a49;border-radius:10px;box-shadow:0 10px 28px #0008}
#jobtalk-api-list div{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:5px 0}
#jobtalk-api-list button{flex:none;padding:3px 6px;border:1px solid #626857;border-radius:6px;background:#1d2115;color:#f4f5e8}
#jobtalk-api-list button:disabled{opacity:.5}
#chat-log .bubble,#future-chat-log .bubble{white-space:pre-wrap}
#chat-quick,#future-questions,#future-headline,#future-story,.future-reflections,#path-check,.mentor-chat-note{display:none!important}
#explore-guide .chat-mode small,#explore-chat .explore-section-head p{display:none}
.roadmap-star-track svg.jobtalk-mobile-stars{display:none}
@media(max-width:640px){
  .roadmap-star-track svg.jobtalk-mobile-stars{display:block;width:64px}
  .roadmap-star-track ol{grid-auto-rows:1fr}
  .roadmap-star-track ol::before{display:none}
  .roadmap-star-node{display:grid;grid-template-columns:minmax(0,1fr);padding-left:64px;height:100%;min-height:48px}
  .roadmap-star-node>span:first-child{position:absolute;left:calc(var(--star-mobile-x,32px) - 22px);top:calc(50% - 22px)}
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

bridge = DESIGN_FILE.with_name("design_bridge.js").read_text(encoding="utf-8-sig")
before_close, closing, after_close = html.rpartition("</body>")
html = before_close + "<script>\n" + bridge + "\n</script>\n" + closing + after_close
html = html.replace("AI 선배 · 예시 대화", "AI 선배", 1).replace(
    "직무 정보를 바탕으로 구성한 예시 대화예요.", "AI 답변은 실제 채용 공고와 함께 확인해 주세요.", 1
)
html = html.replace('\n  byId("future-chat-context").textContent = `${role.name} × ${path.name} · 예시 대화`;',
                    '\n  byId("future-chat-context").textContent = `${role.name} × ${path.name}`;', 1)

component = st.components.v2.component(
    "jobtalk_design",
    html='<iframe title="잡담 진로 탐색과 별자리 로드맵" sandbox="allow-scripts allow-same-origin allow-downloads allow-forms allow-popups allow-popups-to-escape-sandbox allow-modals"></iframe>',
    css="""
    iframe { display:block; width:100%; height:max(360px,calc(100dvh - 7rem)); border:0; }
    """,
    js=DESIGN_FILE.with_name("design_component.js").read_text(encoding="utf-8-sig"),
)
with st.container(horizontal=True, gap="small"):
    st.page_link("app_pages/home.py", label="기존 앱", icon=":material/open_in_new:")
    with st.popover("AI 연결 설정", icon=":material/key:"):
        llm.render_byok_body()
response = st.session_state.get("jobtalk_response", {})
event = component(
    key="jobtalk_design",
    data={"html": html, "connections": design_backend.connection_list(), "response": response},
    on_request_change=lambda: None,
)
request = event.request
if isinstance(request, dict) and isinstance(request.get("id"), str) and request["id"] != response.get("id"):
    try:
        result = design_backend.dispatch(request)
    except Exception:
        result = {"label": "서버 요청 처리 실패"}
    st.session_state.jobtalk_response = {"id": request["id"], "data": result}
    st.rerun()

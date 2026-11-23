from pathlib import Path

import streamlit as st

from utils import design_backend

DESIGN_FILE = Path(__file__).resolve().parents[1] / "assets" / "jobtalk-final.html"
FRAME_HEAD = """<head>
<base href="about:srcdoc">
<style>
body > .jobtalk-editor{display:none!important}
#jobtalk-api-panel{position:relative;color:#f5f3ea;font-size:.8rem;flex:none}
#jobtalk-api-panel summary{cursor:pointer;padding:7px 10px;border:1px solid #5b5e4b;border-radius:8px;color:#f5f3ea!important;background:#141510;font-weight:650}
#jobtalk-api-panel summary:hover{border-color:#d9f477}
#jobtalk-api-list{color:#f5f3ea;z-index:1000!important}
#jobtalk-api-panel[open]{z-index:1000}
.top:has(#jobtalk-api-panel[open]){z-index:1000}
#jobtalk-key-form{display:flex!important;gap:6px;padding:4px 0 10px!important;border-bottom:1px solid #34362c;margin-bottom:6px}
#jobtalk-key-form input{flex:1;min-width:0;padding:5px 8px;border:1px solid #626857;border-radius:6px;background:#0f100c;color:#f5f3ea}
#jobtalk-key-note{display:block!important;color:#b1afa3;font-size:.72rem;padding:0 0 8px!important}
#jobtalk-api-list{position:absolute;z-index:20;right:0;top:100%;width:min(330px,85vw);max-height:65vh;overflow:auto;padding:10px;background:#171911;border:1px solid #575a49;border-radius:10px;box-shadow:0 10px 28px #0008}
#jobtalk-api-list div{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:5px 0}
#jobtalk-api-list button{flex:none;padding:3px 6px;border:1px solid #626857;border-radius:6px;background:#1d2115;color:#f4f5e8}
#jobtalk-api-list button:disabled{opacity:.5}
#chat-log .bubble,#future-chat-log .bubble{white-space:pre-wrap}
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
    # 별도 자료 서버 대신, 잡담 서버(고용24 훈련과정·Q-Net 시험일정)에 물어봐요
    '\n    if (location.href.startsWith("about:srcdoc")) {\n'
    '      const rk = `${kind}:${key}`;\n'
    '      let rq = roadmapLookups.get(rk)?.request;\n'
    '      if (!rq) { rq = requestJobtalk({action:"resource",kind,key}); roadmapLookups.set(rk,{expires:Date.now()+30*60*1000,request:rq}); }\n'
    '      return rq.then(data => { if (node.isConnected) renderRoadmapResource(node, data && data.status ? data : snapshot ?? null); });\n'
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
# API 키 입력은 디자인 안 'API 연결 상태' 패널로 옮겼어요(위쪽에 따로 뜨던 줄 정리)
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

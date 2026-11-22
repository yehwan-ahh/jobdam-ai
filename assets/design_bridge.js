const bridgeQueue = [];
let bridgeActive = null;

function sendNextJobtalkRequest() {
  if (bridgeActive || !bridgeQueue.length) return;
  bridgeActive = bridgeQueue.shift();
  const item = bridgeActive;
  item.timer = setTimeout(() => {
    if (bridgeActive !== item) return;
    bridgeActive = null;
    item.resolve({});
    sendNextJobtalkRequest();
  }, 90000);
  parent.postMessage({type:"jobtalk-request", request:item.request},"*");
}

function requestJobtalk(payload) {
  return new Promise(resolve => {
    bridgeQueue.push({request:{...payload,id:crypto.randomUUID()},resolve});
    sendNextJobtalkRequest();
  });
}

const apiPanel = document.createElement("details");
apiPanel.id = "jobtalk-api-panel";
apiPanel.innerHTML = '<summary>API 연결 상태</summary><div id="jobtalk-api-list"></div>';
document.querySelector(".top > .shell").append(apiPanel);
const checkedConnections = new Map();

function showJobtalkConnections(connections) {
  const list = byId("jobtalk-api-list");
  if (!Array.isArray(connections)) return;
  list.replaceChildren(...connections.map(service => {
    const row = document.createElement("div");
    const label = document.createElement("span");
    label.textContent = service.label + " · " + (checkedConnections.get(service.key) ||
      (service.configured ? "설정됨 · 미확인" : "미설정"));
    label.setAttribute("role","status");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "연결 확인";
    button.disabled = !service.configured || checkedConnections.get(service.key) === "확인 중";
    button.onclick = async () => {
      checkedConnections.set(service.key,"확인 중");
      showJobtalkConnections(connections);
      const result = await requestJobtalk({action:"check",service:service.key});
      checkedConnections.set(service.key,result.status || "응답 확인 실패");
      showJobtalkConnections(connections);
    };
    row.append(label,button);
    return row;
  }));
}

window.addEventListener("message",event => {
  if (event.source !== parent || event.data?.type !== "jobtalk-update") return;
  showJobtalkConnections(event.data.connections);
  const response = event.data.response;
  if (!bridgeActive || response?.id !== bridgeActive.request.id) return;
  const item = bridgeActive;
  clearTimeout(item.timer);
  bridgeActive = null;
  item.resolve(response.data || {});
  sendNextJobtalkRequest();
});

function jobtalkHistory(entries) {
  return entries.slice(-8).map(entry => ({
    role:entry.user ? "user" : "assistant",
    content:entry.text || entry.lines?.join("\n") || ""
  })).filter(entry => entry.content && !entry.content.startsWith("답변을 준비"));
}
function jobtalkReplyText(result) {
  return [result.text, result.sources?.length ? "출처 · " + result.sources.join(" / ") : ""].filter(Boolean).join("\n\n");
}

function appendJobtalkLinks(bubble,links) {
  if (!bubble || !links?.length) return;
  for (const link of links) {
    const url = new URL(link.url);
    if (!["https:","http:"].includes(url.protocol)) continue;
    const anchor = document.createElement("a");
    anchor.href = url.href;
    anchor.textContent = link.label;
    anchor.target = "_blank";
    anchor.rel = "noopener noreferrer";
    bubble.append(document.createElement("br"),anchor);
  }
}
const renderExploreChat = renderChat;
renderChat = function(forceOpen) {
  renderExploreChat(forceOpen);
  const entries = chatHistory.get(chatRole) || [];
  const bubbles = byId("chat-log").querySelectorAll(".bubble");
  if (entries.at(-1)?.links) appendJobtalkLinks(bubbles[bubbles.length-1],entries.at(-1).links);
};

let exploreChatBusy = false;
answer = async function(question) {
  if (exploreChatBusy) return;
  exploreChatBusy = true;
  const role = chatRole;
  const history = chatHistory.get(role) || [];
  const payload = {action:"chat",mode:role ? "mentor" : "guide",job:role?.name,question,history:jobtalkHistory(history)};
  const message = {user:true,text:question,time:new Date()};
  const fallback = role ? {...mentorReply(role,question,history.at(-1)),time:new Date()} : adviceFor(question);
  const pending = {text:"답변을 준비하고 있어요…",time:new Date()};
  history.push(message,pending);
  chatHistory.set(role,history);
  renderChat(true);
  const result = await requestJobtalk(payload);
  const response = result.text
    ? {text:jobtalkReplyText(result),time:new Date(),prompts:fallback.prompts,links:result.links}
    : {...fallback,time:new Date()};
  history[history.indexOf(pending)] = response;
  if (chatRole === role) {
    renderChat(true);
    if (!result.text) byId("chat-log").append(chatBubble(result.label || "시연 응답 · 서버 응답 지연",false));
    byId("chat-log").scrollTop = byId("chat-log").scrollHeight;
  }
  exploreChatBusy = false;
};

let futureChatBusy = false;
const answerFutureDemo = answerAsFutureSelf;
answerAsFutureSelf = async function(question) {
  const conversation = activeFutureConversation;
  if (!conversation || !state.path || futureChatBusy) return;
  futureChatBusy = true;
  const payload = {action:"chat",mode:"future",job:state.role.name,path:state.path.name,question,
    history:jobtalkHistory(conversation.messages)};
  conversation.messages.push({text:question,user:true});
  appendFutureMessage(question,true);
  const pending = appendFutureMessage("답변을 준비하고 있어요…");
  pending.scrollIntoView({block:"nearest"});
  const result = await requestJobtalk(payload);
  if (result.text) {
    const text = jobtalkReplyText(result);
    conversation.messages.push({text,user:false});
    if (activeFutureConversation === conversation) {
      pending.textContent = text;
      appendJobtalkLinks(pending,result.links);
    }
  } else {
    conversation.messages.pop();
    if (activeFutureConversation === conversation) {
      pending.previousElementSibling?.remove();
      pending.remove();
      answerFutureDemo(question);
      appendFutureMessage(result.label || "시연 응답 · 서버 응답 지연");
    }
  }
  if (activeFutureConversation === conversation) {
    const log = byId("future-chat-log");
    log.scrollTop = log.scrollHeight;
  }
  futureChatBusy = false;
};

const buildRoadmapDemo = renderRoadmap;
const personalizedPlans = new Map();
const plansLoading = new Set();
const planStatus = document.createElement("p");
planStatus.className = "roadmap-note";
planStatus.setAttribute("role","status");
byId("roadmap-star-heading").parentElement.after(planStatus);

function applyJobtalkPlan(plan) {
  const cards = byId("milestones").children;
  const stars = byId("roadmap-star-points").children;
  plan.stages.forEach((step,index) => {
    cards[index].querySelector("h3").textContent = step.title;
    cards[index].querySelector(".roadmap-period").textContent = step.period;
    cards[index].querySelector(".roadmap-goal").textContent = step.goals.join(" · ");
    cards[index].querySelector(".roadmap-actions").replaceChildren(...step.actions.map(action => {
      const item = document.createElement("li");
      item.textContent = action;
      return item;
    }));
    stars[index+1].querySelector("strong").textContent = step.title;
    stars[index+1].querySelector("small").textContent = step.period;
  });
  byId("roadmap-destination").textContent = plan.checkpoint;
  planStatus.textContent = plan.ai ? "AI 맞춤 로드맵" : "현재 상황과 진로를 반영한 기본 로드맵";
}

renderRoadmap = function() {
  buildRoadmapDemo();
  const start = byId("stage").value;
  if (!state.role || !state.path || !start) {
    planStatus.textContent = "현재 상황을 선택하면 맞춤 계획을 만들어요.";
    return;
  }
  const job = state.role.name;
  const path = state.path.name;
  const key = JSON.stringify([job,path,start]);
  if (personalizedPlans.has(key)) {
    applyJobtalkPlan(personalizedPlans.get(key));
    return;
  }
  planStatus.textContent = "현재 상황에 맞는 계획을 만드는 중이에요…";
  if (plansLoading.has(key)) return;
  plansLoading.add(key);
  requestJobtalk({action:"plan",job,path,start}).then(plan => {
    plansLoading.delete(key);
    if (plan.stages?.length === 4) personalizedPlans.set(key,plan);
    if (state.role?.name !== job || state.path?.name !== path || byId("stage").value !== start) return;
    if (personalizedPlans.has(key)) applyJobtalkPlan(plan);
    else planStatus.textContent = "맞춤 계획을 불러오지 못했어요. 기본 계획을 표시해요.";
  });
};
byId("stage").removeEventListener("change",buildRoadmapDemo);
byId("stage").addEventListener("change",renderRoadmap);

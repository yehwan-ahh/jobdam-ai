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
  setChatControls(event.data.connections);
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
function chatStatusAfter(anchor) {
  const status = document.createElement("p");
  status.className = "roadmap-note";
  status.setAttribute("role","status");
  anchor.after(status);
  return status;
}

const exploreStatus = chatStatusAfter(byId("chat-log"));
const futureStatus = chatStatusAfter(byId("future-chat-log"));
function setupQuestionExamples(containerId,inputId,examples) {
  const container = byId(containerId);
  const label = document.createElement("p");
  label.className = "jobtalk-suggest-label";
  label.textContent = "질문 예시";
  container.before(label);
  container.setAttribute("aria-label","질문 예시");
  const legacyLabel = container.querySelector("#future-why");
  container.replaceChildren(...examples.map(question => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "btn sub";
    button.textContent = question;
    button.addEventListener("click",event => {
      event.stopPropagation();
      const input = byId(inputId);
      input.value = question;
      if (!input.disabled) input.focus({preventScroll:true});
    });
    return button;
  }));
  if (legacyLabel) {
    legacyLabel.hidden = true;
    container.append(legacyLabel);
  }
}

setupQuestionExamples("chat-quick","chat-input",[
  "하루 일과가 궁금해요", "어떤 회사에 지원해 볼까요?", "무엇부터 준비할까요?"
]);
setupQuestionExamples("future-questions","future-chat-input",[
  "왜 이 길을 골랐어?", "어떤 점이 가장 힘들었어?", "지금 뭘 준비하면 좋을까?"
]);

const missingAI = "AI 연결 설정에서 API 키를 입력해 주세요.";
let aiConfigured = false;
let exploreChatBusy = false;
let futureChatBusy = false;

function updateChatAvailability(connections) {
  if (!Array.isArray(connections)) return;
  const configured = connections.some(item => item.key === "ai" && item.configured);
  if (configured === aiConfigured && exploreStatus.textContent) return;
  aiConfigured = configured;
  for (const status of [exploreStatus,futureStatus]) status.textContent = configured ? "" : missingAI;
}

function appendResponseLinks(log,entry) {
  if (!entry.links?.length) return;
  const bubbles = log.querySelectorAll(".bubble");
  appendJobtalkLinks(bubbles[bubbles.length-1],entry.links);
}

renderChat = function(forceOpen=false) {
  const entries = chatHistory.get(chatRole) || [];
  const log = byId("chat-log");
  byId("explore-chat").hidden = !forceOpen && !chatRole && !entries.length;
  log.replaceChildren();
  for (const entry of entries) {
    if (chatRole) appendMentorMessage(log,entry);
    else log.append(chatBubble(entry.text,entry.user));
    appendResponseLinks(log,entry);
  }
  log.scrollTop = log.scrollHeight;
};

answer = async function(question) {
  if (!aiConfigured || exploreChatBusy) {
    if (!aiConfigured) exploreStatus.textContent = missingAI;
    return;
  }
  exploreChatBusy = true;
  const role = chatRole;
  const history = chatHistory.get(role) || [];
  const payload = {action:"chat",mode:role ? "mentor" : "guide",job:role?.name,question,history:jobtalkHistory(history)};
  const input = byId("chat-input");
  input.disabled = true;
  exploreStatus.textContent = "AI가 답변을 준비하고 있어요…";
  const result = await requestJobtalk(payload);
  if (result.text) {
    history.push({user:true,text:question,time:new Date()},
      {text:jobtalkReplyText(result),time:new Date(),links:result.links});
    chatHistory.set(role,history);
  }
  if (chatRole === role) {
    renderChat(true);
    exploreStatus.textContent = result.text ? "" : (result.label || "AI 응답을 받지 못했어요. 다시 시도해 주세요.");
    if (!result.text && !input.value) input.value = question;
  }
  input.disabled = !aiConfigured;
  exploreChatBusy = false;
};

const renderFutureHistory = renderFutureChat;
renderFutureChat = function() {
  const previous = activeFutureConversation;
  renderFutureHistory();
  if (activeFutureConversation && previous !== activeFutureConversation) {
    const log = byId("future-chat-log");
    activeFutureConversation.messages.forEach((entry,index) => appendJobtalkLinks(log.children[index],entry.links));
  }
};

answerAsFutureSelf = async function(question) {
  const conversation = activeFutureConversation;
  if (!conversation || !state.path || futureChatBusy || !aiConfigured) {
    if (!aiConfigured) futureStatus.textContent = missingAI;
    return;
  }
  futureChatBusy = true;
  const input = byId("future-chat-input");
  input.disabled = true;
  const payload = {action:"chat",mode:"future",job:state.role.name,path:state.path.name,question,
    history:jobtalkHistory(conversation.messages)};
  futureStatus.textContent = "AI가 답변을 준비하고 있어요…";
  const result = await requestJobtalk(payload);
  if (result.text) {
    const entry = {text:jobtalkReplyText(result),user:false,links:result.links};
    conversation.messages.push({text:question,user:true},entry);
    if (activeFutureConversation === conversation) {
      appendFutureMessage(question,true);
      appendJobtalkLinks(appendFutureMessage(entry.text),entry.links);
      const log = byId("future-chat-log");
      log.scrollTop = log.scrollHeight;
    }
  }
  if (activeFutureConversation === conversation) {
    futureStatus.textContent = result.text ? "" : (result.label || "AI 응답을 받지 못했어요. 다시 시도해 주세요.");
    if (!result.text && !input.value) input.value = question;
  }
  input.disabled = !aiConfigured;
  futureChatBusy = false;
};

function setChatControls(connections) {
  updateChatAvailability(connections);
  byId("chat-input").disabled = !aiConfigured || exploreChatBusy;
  byId("future-chat-input").disabled = !aiConfigured || futureChatBusy;
  for (const id of ["chat-form","future-chat-form"]) {
    byId(id).querySelector("button").disabled = !aiConfigured;
  }
}
setChatControls([]);

const buildRoadmapDemo = renderRoadmap;
const personalizedPlans = new Map();
const plansLoading = new Set();
const planStatus = document.createElement("p");
planStatus.className = "roadmap-note";
planStatus.setAttribute("role","status");
byId("roadmap-star-heading").parentElement.after(planStatus);

let previousConstellation;
let constellationFrame;
const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
const mobileConstellation = document.createElementNS("http://www.w3.org/2000/svg","svg");
mobileConstellation.setAttribute("class","jobtalk-mobile-stars");
mobileConstellation.setAttribute("viewBox","0 0 64 600");
mobileConstellation.setAttribute("preserveAspectRatio","none");
mobileConstellation.setAttribute("aria-hidden","true");
const mobileLine = document.createElementNS(mobileConstellation.namespaceURI,"polyline");
mobileConstellation.append(mobileLine);
byId("roadmap-star-points").before(mobileConstellation);

function paintConstellation(heights) {
  [...byId("roadmap-star-points").children].forEach((point,index) => {
    point.style.setProperty("--star-y",heights[index]+"%");
    point.style.setProperty("--star-mobile-x",mobileStarX(heights[index])+"px");
  });
  byId("roadmap-star-line").setAttribute("points",heights.map((y,index) => (50+index*100)+","+y).join(" "));
  mobileLine.setAttribute("points",heights.map((y,index) => mobileStarX(y)+","+(50+index*100)).join(" "));
}

function mobileStarX(height) {
  return 20 + height*.39;
}

function constellationHeights(start,plan) {
  const seed = Object.keys(roadmapStages).indexOf(start);
  return [58,41,51,33,45,25].map((height,index) => {
    const title = plan.stages[index-1]?.title || "";
    const weight = [...title].reduce((total,letter) => total+letter.codePointAt(0),0);
    return height + ((seed*(index+2) + weight)%21)-10;
  });
}

function moveConstellation(route,start,plan) {
  cancelAnimationFrame(constellationFrame);
  const target = constellationHeights(start,plan);
  const base = [...byId("roadmap-star-points").children].map(point => parseFloat(point.style.getPropertyValue("--star-y")));
  const from = previousConstellation?.route === route ? previousConstellation.heights : base;
  const update = heights => {
    previousConstellation = {route,heights};
    paintConstellation(heights);
  };
  if (reducedMotion.matches || target.every((height,index) => height === from[index])) {
    update(target);
    return;
  }
  const begin = performance.now();
  update(from);
  const tick = now => {
    const progress = Math.min(1,(now-begin)/650);
    const eased = progress*progress*(3-2*progress);
    update(from.map((height,index) => height+(target[index]-height)*eased));
    if (progress < 1) constellationFrame = requestAnimationFrame(tick);
  };
  constellationFrame = requestAnimationFrame(tick);
}

function applyJobtalkPlan(plan,route,start) {
  moveConstellation(route,start,plan);
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
  cancelAnimationFrame(constellationFrame);
  buildRoadmapDemo();
  const start = byId("stage").value;
  if (!state.role || !state.path) return;
  const route = JSON.stringify([state.role.name,state.path.name]);
  const defaultHeights = [...byId("roadmap-star-points").children].map(point => parseFloat(point.style.getPropertyValue("--star-y")));
  paintConstellation(start && previousConstellation?.route === route ? previousConstellation.heights : defaultHeights);
  if (!start) {
    previousConstellation = {route,heights:defaultHeights};
    planStatus.textContent = "현재 상황을 선택하면 맞춤 계획을 만들어요.";
    return;
  }
  const job = state.role.name;
  const path = state.path.name;
  const key = JSON.stringify([job,path,start]);
  if (personalizedPlans.has(key)) {
    applyJobtalkPlan(personalizedPlans.get(key),route,start);
    return;
  }
  planStatus.textContent = "현재 상황에 맞는 계획을 만드는 중이에요…";
  if (plansLoading.has(key)) return;
  plansLoading.add(key);
  requestJobtalk({action:"plan",job,path,start}).then(plan => {
    plansLoading.delete(key);
    if (plan.stages?.length === 4) personalizedPlans.set(key,plan);
    if (state.role?.name !== job || state.path?.name !== path || byId("stage").value !== start) return;
    if (personalizedPlans.has(key)) applyJobtalkPlan(plan,route,start);
    else planStatus.textContent = "맞춤 계획을 불러오지 못했어요. 기본 계획을 표시해요.";
  });
};
byId("stage").removeEventListener("change",buildRoadmapDemo);
byId("stage").addEventListener("change",renderRoadmap);

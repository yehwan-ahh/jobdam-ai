export default function ({ data, parentElement, setTriggerValue }) {
  const frame = parentElement.querySelector("iframe");
  if (!frame.dataset.loaded) {
    frame.dataset.loaded = "yes";
    frame.srcdoc = data.html;
  }

  if (frame.jobtalkListener) window.removeEventListener("message", frame.jobtalkListener);
  frame.jobtalkListener = event => {
    if (event.source === frame.contentWindow && event.data?.type === "jobtalk-request") {
      setTriggerValue("request", event.data.request);
    }
  };
  window.addEventListener("message", frame.jobtalkListener);

  const sync = () => frame.contentWindow.postMessage({
    type: "jobtalk-update", connections: data.connections, response: data.response
  }, "*");
  frame.onload = sync;
  sync();
  return () => {
    window.removeEventListener("message", frame.jobtalkListener);
  };
}

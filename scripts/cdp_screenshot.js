const fs = require('fs');

async function capture(url, outPath, width = 1440, height = 900, isMobile = false, waitMs = 1800) {
  const res = await fetch('http://localhost:9225/json');
  const tabs = await res.json();
  const page = tabs.find(t => t.type === 'page');
  if (!page) throw new Error('No page tab found');

  const ws = new WebSocket(page.webSocketDebuggerUrl);

  let id = 1;
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const curId = id++;
    const handler = (evt) => {
      const msg = JSON.parse(evt.data);
      if (msg.id === curId) {
        ws.removeEventListener('message', handler);
        if (msg.error) reject(msg.error);
        else resolve(msg.result);
      }
    };
    ws.addEventListener('message', handler);
    ws.send(JSON.stringify({ id: curId, method, params }));
  });

  await new Promise((resolve) => { ws.onopen = resolve; });

  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', {
    width,
    height,
    deviceScaleFactor: 1,
    mobile: isMobile
  });

  await send('Page.navigate', { url });

  // Wait for React rendering, API calls, and transitions to settle
  await new Promise(r => setTimeout(r, waitMs));

  const screenshot = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(outPath, Buffer.from(screenshot.data, 'base64'));

  ws.close();
}

const args = process.argv.slice(2);
const [url, outPath, w, h, mob, waitMs] = args;
capture(url, outPath, parseInt(w || 1440), parseInt(h || 900), mob === 'true', parseInt(waitMs || 1800))
  .then(() => {
    console.log(`Saved screenshot to ${outPath}`);
    process.exit(0);
  })
  .catch(err => {
    console.error(err);
    process.exit(1);
  });

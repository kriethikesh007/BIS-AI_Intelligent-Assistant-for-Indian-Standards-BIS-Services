const fs = require('fs');
const path = require('path');

const outDir = 'C:/Users/kriet/.gemini/antigravity/brain/846b2f5c-8b44-447a-afcf-587df08bc965/screenshots_verified';
if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

async function getPageWsUrl() {
  const res = await fetch('http://localhost:9225/json');
  const tabs = await res.json();
  const page = tabs.find(t => t.type === 'page');
  return page.webSocketDebuggerUrl;
}

function createCdpClient(wsUrl) {
  const ws = new WebSocket(wsUrl);
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

  const ready = new Promise(resolve => { ws.onopen = resolve; });

  return { ws, send, ready };
}

async function run() {
  const wsUrl = await getPageWsUrl();
  const { ws, send, ready } = createCdpClient(wsUrl);
  await ready;
  await send('Page.enable');

  const captureOne = async (url, filename, width, height, isMobile, waitMs = 1200) => {
    await send('Emulation.setDeviceMetricsOverride', {
      width,
      height,
      deviceScaleFactor: 1,
      mobile: isMobile
    });
    await send('Page.navigate', { url });
    await new Promise(r => setTimeout(r, waitMs));
    const ss = await send('Page.captureScreenshot', { format: 'png' });
    const targetFile = path.join(outDir, filename);
    fs.writeFileSync(targetFile, Buffer.from(ss.data, 'base64'));
    console.log(`Captured: ${filename}`);
  };

  const routes = [
    ['', '01_overview.png'],
    ['assistant?q=Which%20standard%20applies%20to%20motorcycle%20helmets%3F', '02_assistant_chat.png', 4000],
    ['find-standard', '03_find_standard.png'],
    ['search', '04_catalog.png'],
    ['certification', '05_certification.png'],
    ['hallmarking', '06_hallmarking.png'],
    ['laboratories', '07_laboratories.png'],
    ['consumer', '08_consumer.png'],
    ['analytics', '09_analytics.png'],
    ['admin', '10_admin_login.png']
  ];

  console.log('--- CAPTURING DESKTOP DARK (1440x900) ---');
  for (const [route, file, customWait] of routes) {
    await captureOne(`http://localhost:5173/${route}${route.includes('?') ? '&' : '?'}theme=dark`, `desktop_dark_${file}`, 1440, 900, false, customWait || 1200);
  }

  console.log('--- CAPTURING DESKTOP LIGHT (1440x900) ---');
  for (const [route, file, customWait] of [routes[0], routes[1], routes[3], routes[8]]) {
    await captureOne(`http://localhost:5173/${route}${route.includes('?') ? '&' : '?'}theme=light`, `desktop_light_${file}`, 1440, 900, false, customWait || 1200);
  }

  console.log('--- CAPTURING MOBILE DARK (390x844) ---');
  for (const [route, file, customWait] of routes) {
    await captureOne(`http://localhost:5173/${route}${route.includes('?') ? '&' : '?'}theme=dark`, `mobile_dark_${file}`, 390, 844, true, customWait || 1200);
  }

  console.log('--- CAPTURING TABLET DARK (768x1024) ---');
  for (const [route, file, customWait] of [routes[0], routes[1], routes[2], routes[3]]) {
    await captureOne(`http://localhost:5173/${route}${route.includes('?') ? '&' : '?'}theme=dark`, `tablet_dark_${file}`, 768, 1024, false, customWait || 1200);
  }

  ws.close();
  console.log('All captures completed!');
}

run().catch(err => {
  console.error(err);
  process.exit(1);
});

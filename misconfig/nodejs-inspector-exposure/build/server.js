// A trivial always-on app on :3000 (the primary port, used for readiness). The
// only variable is whether the process is started with the V8 inspector bound
// to a public interface (see the per-state command in contract.yaml).
const http = require('http');
http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('ok');
}).listen(3000, '0.0.0.0', () => console.log('app on :3000'));

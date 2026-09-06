import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { resolve, extname, sep } from "node:path";

const root = resolve(process.argv[2] || "review-dist");
const types = {
  ".html": "text/html", ".js": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".gltf": "model/gltf+json", ".glb": "model/gltf-binary",
  ".bin": "application/octet-stream", ".wasm": "application/wasm",
  ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
  ".webp": "image/webp", ".svg": "image/svg+xml", ".hdr": "application/octet-stream",
};

createServer(async (request, response) => {
  try {
    const pathname = decodeURIComponent(new URL(request.url, "http://localhost").pathname);
    if (pathname === "/api/astra/status") {
      response.writeHead(200, { "content-type": "application/json" });
      response.end(JSON.stringify({ configured: false, model: "gpt-6-astra" }));
      return;
    }
    const file = resolve(root, `.${pathname === "/" ? "/index.html" : pathname}`);
    if (!file.startsWith(`${root}${sep}`) || !(await stat(file)).isFile()) {
      response.writeHead(404).end();
      return;
    }
    response.writeHead(200, { "content-type": types[extname(file)] || "application/octet-stream" });
    response.end(await readFile(file));
  } catch {
    response.writeHead(404).end();
  }
}).listen(4180, "127.0.0.1", () => console.log("Eden HTML review server ready"));

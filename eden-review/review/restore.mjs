import { readFile, writeFile, mkdir } from "node:fs/promises";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { dirname, resolve, sep } from "node:path";

const manifest = JSON.parse(await readFile("asset-manifest.json", "utf8"));
const archive = Buffer.from(await readFile("site-build.tar.gz.base64", "utf8"), "base64");
if (createHash("sha256").update(archive).digest("hex") !== manifest.buildSha256) {
  throw new Error("HTML build checksum mismatch");
}
await mkdir("site", { recursive: true });
await writeFile("site-build.tar.gz", archive);
const unpack = spawnSync("tar", ["-xzf", "site-build.tar.gz", "-C", "site"], { stdio: "inherit" });
if (unpack.status !== 0) throw new Error("Could not unpack the HTML build");

for (const asset of manifest.assets) {
  const target = resolve("site", asset.path);
  if (!target.startsWith(`${resolve("site")}${sep}`)) throw new Error("Invalid asset path");
  let bytes;
  if (asset.embedded) {
    bytes = await readFile(target);
  } else {
    const url = new URL(asset.url);
    if (!["raw.githubusercontent.com", "dl.polyhaven.org"].includes(url.hostname) || url.protocol !== "https:") throw new Error("Unexpected asset source");
    const response = await fetch(url, { signal: AbortSignal.timeout(90_000) });
    if (!response.ok) throw new Error(`Asset download failed: ${response.status} ${asset.path}`);
    bytes = Buffer.from(await response.arrayBuffer());
  }
  if (createHash("sha256").update(bytes).digest("hex") !== asset.sha256) {
    throw new Error(`Asset changed from the reviewed source: ${asset.path}`);
  }
  await mkdir(dirname(target), { recursive: true });
  await writeFile(target, bytes);
  console.log(`Verified ${asset.path}`);
}

#!/usr/bin/env node
// Global glTF 2.0 structural verification, sourced from official Khronos
// validator npm module. Requires: npm install --no-save gltf-validator
// Use only for file validation, NEVER reference/style or device approval.
import fs from "node:fs";
import path from "node:path";
import {createRequire} from "node:module";
const require=createRequire(import.meta.url);
const gltfValidator=require("gltf-validator");
const [src,out]=process.argv.slice(2);
if(!src||!out)throw new Error("Usage: node validate_gltf.mjs input.glb report.json");
const report=await gltfValidator.validateBytes(new Uint8Array(fs.readFileSync(src)),{
  uri:path.basename(src),
  maxIssues:10000
});
const artifact={
 schema_version:1,
 status:"TECHNICAL_GLTF_VALIDATION_ONLY",
 validator:"Khronos glTF Validator",
 input_glb:src,
 summary:report.issues?.numErrors===undefined?null:report.issues,
 asset_info:report.info||null,
 source_report:report,
 owner_reference_approved:false,
 physical_device_tested:false
};
fs.mkdirSync(path.dirname(out),{recursive:true});
fs.writeFileSync(out,JSON.stringify(artifact,null,2)+"\n");
const issues=report.issues||{};
console.log(JSON.stringify({errors:issues.numErrors??null,warnings:issues.numWarnings??null,report:out}));
if(issues.numErrors!==0)process.exit(1);

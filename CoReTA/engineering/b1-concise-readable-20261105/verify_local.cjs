const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const root=path.resolve(__dirname,'../..'),raw=path.resolve(root,'../../lab-diagnostics-20261105');
const load=p=>JSON.parse(fs.readFileSync(p,'utf8')),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const serverPrefix='/data2/xiaoxinchen/agent-research/CoReTA/runs/';
let files=0;
for(const name of ['b1-sampling-check-20261105-v2','b1-concise-V8-20261105-v1','b1-concise-tech6-20261105-v1','b1-concise-readable-tech6-20261105-v1']){
 const run=path.join(raw,name),approval=load(path.join(run,'APPROVAL.json'));
 assert.equal(sha(path.join(run,'FREEZE.json')),approval.freeze_sha256);
 const sources=load(path.join(run,'SOURCE_ARCHIVE.json'));
 for(const entry of Object.values(sources)){
  assert(entry.archive.startsWith(serverPrefix));const file=path.resolve(raw,entry.archive.slice(serverPrefix.length));
  assert(file.startsWith(raw+path.sep));assert.equal(sha(file),entry.sha256);files++;
 }
}
const run=path.join(raw,'b1-concise-readable-tech6-20261105-v1');
const result=load(path.join(run,'RESULTS.json')),scores=load(path.join(run,'scores.json'));
assert.equal(result.n_generated,312);assert.equal(result.n_ok,312);assert.equal(scores.n_complete,6);
assert.equal(result.n_format_warnings,3);assert.equal(scores.primary_enabled,false);
const entry=fs.readFileSync(path.join(__dirname,'STAGE_ENTRY.md'),'utf8');
for(const name of ['handoff.md','CURRENT_STATE.md','brainstorm.md','experiment/results.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md']){
 const p=path.join(root,name),old=fs.readFileSync(p,'utf8');
 if(!old.includes(entry.split('\n')[0]))fs.writeFileSync(p,entry+old,'utf8');
}
const validation={freeze_approval_bindings:4,archived_source_hashes_verified:files,requests_verified:312,complete_tasks:6,format_warnings:3,local_project_history_preserved:true,raw_evidence_directory:raw};
fs.writeFileSync(path.join(__dirname,'LOCAL_VALIDATION.json'),JSON.stringify(validation,null,2)+'\n');
console.log(JSON.stringify(validation));

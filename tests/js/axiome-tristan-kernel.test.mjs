import test from "node:test";
import assert from "node:assert/strict";
import {auditClaim,mutateClaim,supportScore,localFingerprint} from "../../interfaces/axiome-tristan/kernel.mjs";
function sample(overrides={}){return{id:"AX-JS-1",statement:"bounded claim",kind:"HYPOTHESIS",domain:"test",definitions:["x=operational"],scope:["s1","s2"],assumptions:[],evidence:[{type:"BENCHMARK",scope:["s1","s2"],strength:.8,independent:true}],counterevidence:[],uncertainty:{model:.2},falsifiers:["counterexample"],proofObligations:[],provenance:["fixture"],status:"TESTED",version:"0.1",generatorId:"g",judgeId:"j",revenueScore:0,...overrides};}
test("valid structural claim passes",()=>assert.equal(auditClaim(sample()).passed,true));
test("generator cannot judge its own claim",()=>assert.equal(auditClaim(sample({generatorId:"x",judgeId:"x"})).passed,false));
test("simulation alone cannot corroborate",()=>assert.equal(auditClaim(sample({status:"CORROBORATED",evidence:[{type:"SIMULATION",scope:["s1","s2"],strength:1,independent:true}]})).passed,false));
test("scope overflow is visible",()=>assert.equal(auditClaim(sample({evidence:[{type:"BENCHMARK",scope:["s1"],strength:1,independent:true}]})).passed,false));
test("mutations stay candidates",()=>assert.ok(mutateClaim(sample()).every(x=>x.generatedCandidate===true)));
test("revenue cannot affect structural result",()=>assert.equal(auditClaim(sample({revenueScore:0})).passed,auditClaim(sample({revenueScore:999999})).passed));
test("support score is deterministic",()=>assert.equal(supportScore(sample()),supportScore(sample())));
test("local fingerprint deterministic",()=>assert.equal(localFingerprint("abc"),localFingerprint("abc")));

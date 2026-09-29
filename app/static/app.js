/* RoleFit. No provider keys or private resume fixtures belong in this file. */
'use strict';
const $ = (q, root = document) => root.querySelector(q);
const $$ = (q, root = document) => [...root.querySelectorAll(q)];
const esc = (v = '') => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clone = x => JSON.parse(JSON.stringify(x));
const paths = {
 document: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h5"/>',
 upload: '<path d="M12 16V3m-4 4 4-4 4 4M4 16v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4"/>',
 download: '<path d="M12 3v13m-4-4 4 4 4-4M4 17v4h16v-4"/>',
 plus: '<path d="M12 5v14M5 12h14"/>',
 check: '<path d="m5 12 4 4L19 6"/>',
 close: '<path d="m6 6 12 12M6 18 18 6"/>',
 arrow: '<path d="M4 12h16m-6-6 6 6-6 6"/>',
 back: '<path d="M20 12H4m6-6-6 6 6 6"/>',
 search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
 edit: '<path d="m15 4 5 5M4 20l4-1L20 7a2 2 0 0 0-4-4L4 15z"/>',
 trash: '<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7"/>',
 copy: '<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V3H3v13h5"/>',
 image: '<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L6 21"/>',
 shield: '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6z"/><path d="m8 12 3 3 5-6"/>',
 lock: '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V6a4 4 0 0 1 8 0v4M12 14v3"/>',
 info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
 settings: '<path d="M4 7h16M4 17h16"/><circle cx="9" cy="7" r="3" fill="currentColor" stroke="none"/><circle cx="15" cy="17" r="3" fill="currentColor" stroke="none"/>',
 user: '<circle cx="12" cy="8" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>',
 folder: '<path d="M3 6a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
 spark: '<path d="m12 3 2.7 6.3L21 12l-6.3 2.7L12 21l-2.7-6.3L3 12l6.3-2.7zM20 2v4M18 4h4"/>',
 clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
 undo: '<path d="M3 10h11a6 6 0 0 1 0 12M3 10l5-5M3 10l5 5"/>',
 up: '<path d="m6 14 6-6 6 6"/>',
 down: '<path d="m6 10 6 6 6-6"/>',
 mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 6 9 7 9-7"/>',
 external: '<path d="M14 3h7v7m0-7L10 14M10 3H3v18h18v-7"/>',
 logout: '<path d="M9 3H3v18h6M10 12h11m-5-5 5 5-5 5"/>'
};
const icon = (name, small = false) => `<svg class="icon${small?' sm':''}" viewBox="0 0 24 24" aria-hidden="true">${paths[name] || paths.document}</svg>`;
const TYPES = ['name','subtitle','contact','heading','subheading','bullet','paragraph','skill'];
const typeLabel = t => ({name:'Name',subtitle:'Professional title',contact:'Contact details',heading:'Section heading',subheading:'Role / project heading',bullet:'Experience bullet',paragraph:'Paragraph',skill:'Skill category'}[t] || t);
const S = {csrf:'', me:null, route:'create', profile:null, resumes:[], images:[], catalog:[],
 form:{jd:'',role:'',company:'',target_pages:6,template:'reference',font:'Aptos',paper:'letter',image_ids:[],consent:false,mode:'ai'},
 backgroundTab:'upload',jobTab:'paste',editor:null,editorTab:'preview',dirty:false,undo:[],search:'',sort:'date',busy:false,
 settingsDraft:null,imageTarget:'create',exportFormat:'pdf',exportClean:false,exportId:null,preview:null};
let toastTimer;
function toast(message, error=false){const el=$('#toast');el.textContent=message;el.className='visible'+(error?' error':'');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.className='',error?6500:3500);}
async function api(path, {method='GET',body,form}={}){
 const headers={'X-RoleFit-Request':'1'};
 if(S.csrf)headers['X-CSRF-Token']=S.csrf;
 if(body!==undefined)headers['Content-Type']='application/json';
 let response;
 try{response=await fetch('/api'+path,{method,headers,body:form|| (body!==undefined?JSON.stringify(body):undefined),credentials:'same-origin'});}
 catch(e){throw new Error('Cannot reach the server. Check the deployment or start RoleFit locally.');}
 if(!response.ok){let data;try{data=await response.json();}catch{data={detail:`Server returned ${response.status}.`};}
   const detail=Array.isArray(data.detail)?data.detail.map(x=>x.msg).join('; '):data.detail;
   const error=new Error(detail||'The request could not be completed.');error.status=response.status;throw error;}
 return response.status===204?null:response.json();
}
async function download(path,filename){
 const response=await fetch('/api'+path,{credentials:'same-origin'});
 if(!response.ok){let data;try{data=await response.json();}catch{data={detail:'Download failed.'};}throw new Error(data.detail);}
 const blob=await response.blob();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;
 const disposition=response.headers.get('Content-Disposition')||'';a.download=filename||(disposition.match(/filename="([^"]+)"/)||[])[1]||'rolefit-export';
 a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);
}
function modal(content){const d=$('#modal');d.innerHTML=content;if(!d.open)d.showModal();}
function drawer(content){const d=$('#drawer');d.innerHTML=content;if(!d.open)d.showModal();}
function closeDialogs(){['#drawer','#modal'].forEach(q=>{if($(q).open)$(q).close();});}
function modalHead(title){return `<div class="modal-head"><h2>${esc(title)}</h2><button class="icon-btn" data-action="close-modal" aria-label="Close dialog">${icon('close')}</button></div>`;}
function drawerHead(title,sub){return `<div class="drawer-head"><div><h2>${esc(title)}</h2><p>${esc(sub)}</p></div><button class="icon-btn" data-action="close-drawer" aria-label="Close drawer">${icon('close')}</button></div>`;}
function friendlyDate(n){return new Date(n*1000).toLocaleDateString(undefined,{month:'short',day:'numeric',year:'numeric'});}
function scorePill(score){return `<span class="pill ${score===null?'neutral':score>90?'success':score>=75?'warning':'danger'}">${score===null?'Not assessed':`${score} / 100`}</span>`;}
function usageUI(){const u=S.me?.usage||{used:0,reserved:0,limit:15};return `<div class="usage" title="${esc(u.timezone||'')} timezone; ${u.reserved||0} in progress"><span><b>${u.used}</b> / 15 today</span><span class="usage-track"><span style="width:${Math.min(100,u.used/15*100)}%"></span></span></div>`;}
function shell(content,wide=false){
 const profileName=S.profile?.document?.blocks.find(b=>b.kind==='name')?.text||'Private workspace';
 const initials=profileName.split(/\s+/).slice(0,2).map(x=>x[0]).join('').toUpperCase();
 return `<header class="topbar"><button class="brand" data-route="create" aria-label="RoleFit home"><span class="brand-mark">${icon('document')}</span>RoleFit</button>
 <nav class="nav" aria-label="Main navigation">${[['create','Create Resume','plus'],['library','My Resumes','folder'],['profile','My Profile','user']].map(([r,t,i])=>`<button class="${S.route.startsWith(r)?'active':''}" data-route="${r}">${icon(i)}${t}</button>`).join('')}<button data-action="settings">${icon('settings')}Settings</button></nav>
 <div class="top-right"><div id="usage-container">${usageUI()}</div><button class="avatar" data-action="account" aria-label="Account menu">${esc(initials)}</button></div></header>
 <main class="workspace${wide?' wide':''}">${content}</main>`;
}
function renderLogin(error=''){
 $('#app').innerHTML=`<main class="login-page"><section class="login-card"><div class="brand"><span class="brand-mark">${icon('document')}</span>RoleFit</div><div class="eyebrow mb12">YOUR PRIVATE WORKSPACE</div><h1>Your next chapter<br>starts with your story.</h1><p>Build thoughtful, job-specific resumes from the experience you already have.</p>
 <form id="login-form"><div class="field"><label for="password">Workspace password</label><input class="input" id="password" name="password" type="password" autocomplete="current-password" required placeholder="Enter your private workspace password" maxlength="256"></div><div id="login-error" class="error-text" role="alert">${esc(error)}</div><button class="btn primary full" type="submit">Open workspace ${icon('arrow')}</button></form><div class="login-footer">${icon('lock',true)} One owner. Your documents stay private.</div></section></main>`;
}
async function boot(){
 try{S.me=await api('/me');S.csrf=S.me.csrf;document.body.dataset.theme=S.me.settings.theme||'lavender';
 [S.profile,S.images]=await Promise.all([api('/profile'),api('/images')]);
 const saved=await api('/create-draft');Object.assign(S.form,saved);S.form.consent=false;
 await loadRoute(location.hash.slice(1)||'create');
 }catch(e){if(e.status===401)renderLogin();else renderLogin(e.message);}
}
function canLeave(){return !S.dirty||confirm('Discard your unsaved edits? Save them first to keep this version.');}
async function navigate(route){if(!canLeave())return;S.dirty=false;closeDialogs();if(location.hash.slice(1)!==route){history.pushState(null,'','#'+route);}await loadRoute(route);}
async function loadRoute(route){
 S.route=route;S.undo=[];S.dirty=false;
 if(route.startsWith('editor/')){
  const ident=route.split('/')[1];S.editor=await api('/resumes/'+ident);S.editorTab='preview';S.preview=null;renderEditor();await refreshPreview();
 }else if(route==='library'){S.resumes=await api('/resumes');renderLibrary();}
 else if(route==='profile'){S.profile=await api('/profile');renderProfile();}
 else{S.route='create';renderCreate();}
 window.scrollTo(0,0);
}
function selectedImages(){return S.images.filter(a=>(S.form.image_ids||[]).includes(a.id));}
function renderCreate(){
 const f=S.form,blocks=S.profile?.document?.blocks||[],name=blocks.find(b=>b.kind==='name')?.text||'Your master resume';
 const ready=Boolean(blocks.length&&S.profile.confirmed);
 const background=S.backgroundTab==='paste'?`<textarea id="manual-background" class="input" rows="7" placeholder="Paste your full resume here, including section headings and work history."></textarea><button class="btn tiny mt8" data-action="parse-paste">Import text for review ${icon('arrow',true)}</button>`:
 (blocks.length?`<div class="profile-ready"><div class="row between"><span class="check-circle">${icon(ready?'check':'info')}</span><span class="pill ${ready?'success':'warning'}">${ready?'Reviewed profile':'Review needed'}</span></div><h3>${esc(name)}</h3><div class="profile-stats"><span>${blocks.length} paragraphs</span><span>${blocks.filter(b=>b.kind==='bullet').length} experience bullets</span></div><div class="row between"><button class="link-button" data-route="profile">${ready?'View / edit profile':'Review extracted details'} ${icon('arrow',true)}</button><label class="link-button">Replace<input class="sr-only" type="file" accept=".pdf,.docx,.txt,.md" data-upload="resume"></label></div></div>`:
 `<label class="dropzone" data-drop="resume"><input type="file" accept=".pdf,.docx,.txt,.md" data-upload="resume" aria-label="Upload your master resume"><span class="icon-box">${icon('upload')}</span><strong>Drop your resume here <span class="muted">or</span> <span style="color:var(--accent)">browse</span></strong><p>PDF, DOCX or TXT &middot; Up to 12 MB</p></label>`);
 const jobInput=S.jobTab==='paste'?`<textarea class="input jd-input" id="jd" data-form="jd" maxlength="12000" placeholder="Paste the job description here. Include the responsibilities, required skills and preferred qualifications.">${esc(f.jd)}</textarea><div class="count" id="jd-count">${f.jd.length.toLocaleString()} / 12,000 characters</div>`:
 `<label class="dropzone" data-drop="job"><input type="file" accept=".pdf,.docx,.txt,.md" data-upload="job" aria-label="Upload job description"><span class="icon-box teal">${icon('upload')}</span><strong>Upload a job description</strong><p>PDF, DOCX or TXT &middot; Text is extracted for review</p></label>`;
 const content=`<div class="page-head"><div><div class="eyebrow">A LITTLE MORE YOU. A LITTLE MORE RELEVANT.</div><h1>Create Resume</h1><p>Your experience, thoughtfully tailored to your next role.</p></div><div class="private-note">${icon('shield',true)} Your private workspace</div></div>
 <div class="welcome-banner"><div class="row"><span class="icon-box">${icon('document')}</span><div><strong>Room for your full experience.</strong><p>5-7 page resumes, reference-inspired styling, and credentials that are yours.</p></div></div><div class="stepper">${['Analyze','Draft','Check','Review'].map((t,i)=>`${i?'<span class="step-line"></span>':''}<div class="step ${i===0?'active':''}"><span>${i+1}</span>${t}</div>`).join('')}</div></div>
 <div class="grid2"><section class="card"><div class="card-head"><div class="card-title"><span class="icon-box">${icon('user',true)}</span><h3>Your Background</h3></div><button class="link-button" data-action="sample-profile">Use sample profile</button></div><div class="card-body"><div class="tabs"><button class="${S.backgroundTab==='upload'?'active':''}" data-action="background-tab" data-value="upload">${blocks.length?'Saved profile':'Upload resume'}</button><button class="${S.backgroundTab==='paste'?'active':''}" data-action="background-tab" data-value="paste">Paste text</button></div>${background}<div class="helper">${icon('lock')}<span>The master profile stays separate from every tailored resume.</span></div></div></section>
 <section class="card"><div class="card-head"><div class="card-title"><span class="icon-box teal">${icon('document',true)}</span><h3>Job Description</h3></div><button class="link-button" data-action="sample-job">Use sample job</button></div><div class="card-body"><div class="tabs"><button class="${S.jobTab==='paste'?'active':''}" data-action="job-tab" data-value="paste">Paste text</button><button class="${S.jobTab==='upload'?'active':''}" data-action="job-tab" data-value="upload">Upload file</button></div>${jobInput}</div></section></div>
 <div class="input-row mt16"><div class="field"><label for="role">Target role</label><input class="input" id="role" data-form="role" value="${esc(f.role)}" maxlength="150" placeholder="e.g. Senior Java Full Stack Developer"></div><div class="field"><label for="company">Company</label><input class="input" id="company" data-form="company" value="${esc(f.company)}" maxlength="120" placeholder="e.g. Your next opportunity"></div></div>
 <div class="grid2 mt24"><section class="card card-pad"><div class="row between"><div><span class="field-label">RESUME LENGTH</span><h3 class="mt8">The detail your experience deserves.</h3></div><span class="pill neutral">Page target</span></div><div class="option-grid">${[[5,'Focused detail'],[6,'Balanced depth'],[7,'Full career story']].map(([n,t])=>`<button class="option ${f.target_pages===n?'active':''}" data-action="choose-pages" data-value="${n}" aria-pressed="${f.target_pages===n}"><div class="option-top"><strong>${n} pages</strong><span class="radio-dot"></span></div><small>${t}</small></button>`).join('')}</div><div class="helper">${icon('info')}<span>A target, not filler. Short profiles stay shorter; long ones prioritize relevant evidence.</span></div><div class="options-bottom"><label>Paper<select class="compact-select" data-form="paper"><option value="letter" ${f.paper==='letter'?'selected':''}>US Letter</option><option value="a4" ${f.paper==='a4'?'selected':''}>A4</option></select></label><label>Font<select class="compact-select" data-form="font">${['Aptos','Calibri','Arial','Times New Roman'].map(x=>`<option ${f.font===x?'selected':''}>${x}</option>`).join('')}</select></label></div></section>
 <section class="card card-pad"><span class="field-label">DOCUMENT STYLE</span><h3 class="mt8">Familiar format. A sharper presentation.</h3><div class="option-grid">${[['reference','Reference','Red headings, skill table & badges'],['ats','ATS Clean','One column, text-first, no images'],['minimal','Minimal','Simple sections, quiet typography']].map(([v,t,d])=>`<button class="option template ${f.template===v?'active':''}" data-action="choose-template" data-value="${v}" aria-pressed="${f.template===v}"><div class="option-top"><span class="mini-doc ${v}"></span><span class="radio-dot"></span></div><strong>${t}</strong><small class="mt8">${d}</small></button>`).join('')}</div><div class="helper">${icon('check')}<span>Preview and export a clean version for application portals.</span></div></section></div>
 <section class="image-card"><div class="row"><span class="icon-box">${icon('image')}</span><div><h3>Images &amp; certification badges</h3><p>Import your existing badges, upload images, or fetch verified issuer artwork.</p></div></div><div class="selected-images">${selectedImages().slice(0,3).map(a=>`<img class="thumb-mini" src="/api/images/${esc(a.id)}" alt="${esc(a.label)}">`).join('')}</div><button class="btn" data-action="images" data-target="create">${icon('plus',true)} ${f.image_ids.length?'Manage ('+f.image_ids.length+')':'Add images'}</button></section>
 <div class="create-footer"><div><div class="mode-row"><label><input type="radio" name="mode" value="ai" data-form="mode" ${f.mode==='ai'?'checked':''}> AI tailoring</label><label><input type="radio" name="mode" value="local" data-form="mode" ${f.mode==='local'?'checked':''}> Local tailoring <span class="muted small">(no AI calls)</span></label></div><label class="checkbox-row" id="consent-row" ${f.mode==='local'?'style="display:none"':''}><input type="checkbox" id="consent" data-form="consent" ${f.consent?'checked':''}><span>Allow relevant resume and job excerpts to be sent to my enabled AI providers. Contact fields are excluded where possible.</span></label><div class="helper" id="generate-help"></div></div><div class="actions"><button class="btn" data-action="save-create">Save draft</button><button class="btn primary" id="generate-btn" data-action="generate">${icon('spark')} Generate resume ${icon('arrow',true)}</button></div></div>
 <div class="bottom-note">${icon('shield')} Your facts stay yours.<span>&middot;</span>No invented experience.<span>&middot;</span>No guaranteed employer ATS score.</div>`;
 $('#app').innerHTML=shell(content);updateGenerateState();
}
function updateGenerateState(){
 const btn=$('#generate-btn');if(!btn)return;
 const u=S.me?.usage||{used:0,reserved:0};const cap=u.used+u.reserved>=15;
 const profileReady=Boolean(S.profile?.confirmed&&S.profile.document.blocks.length);
 const can=profileReady&&S.form.jd.trim().length>=80&&(S.form.mode==='local'||S.form.consent)&&!cap&&!S.busy;
 btn.disabled=!can;
 $('#generate-help').textContent=cap?'Daily limit reached. Editing and exporting remain available.':!profileReady?'Upload and review your master profile to continue.':S.form.jd.trim().length<80?'Add a job description with at least 80 characters.':'Uses 1 daily generation. Automatic provider retries count only once.';
}
async function saveCreate(silent=false){await api('/create-draft',{method:'PUT',body:S.form});if(!silent)toast('Draft saved to your private workspace.');}
async function refreshMe(){S.me=await api('/me');S.csrf=S.me.csrf;const el=$('#usage-container');if(el)el.innerHTML=usageUI();}
async function uploadFile(kind,file){
 if(!file)return;if(file.size>12*1024*1024)throw new Error('Maximum file size is 12 MB.');
 toast('Reading your file...');const form=new FormData();form.append('file',file);
 if(kind==='resume'){
  if(S.profile?.document?.blocks.length&&!confirm('Replace the master profile? Existing tailored resumes are kept.'))return;
  const data=await api('/import',{method:'POST',form});S.profile={document:data.document,confirmed:false};
  await api('/profile',{method:'PUT',body:S.profile});S.images=await api('/images');S.dirty=false;
  toast(`${data.document.blocks.length} paragraphs imported. Review the details before confirming.`);
  await navigate('profile');
 }else if(kind==='job'){const data=await api('/import-job',{method:'POST',form});S.form.jd=data.text;S.jobTab='paste';renderCreate();toast('Job description imported. Please review its text.');}
 else if(kind==='image'){await api('/images',{method:'POST',form});S.images=await api('/images');renderImages();toast('Image added. Confirm its use before selecting it.');}
}
function profileSummary(){const b=S.profile?.document?.blocks||[];return {name:b.find(x=>x.kind==='name')?.text||'Your profile',count:b.length,bullets:b.filter(x=>x.kind==='bullet').length};}
function blockEditor(b,i,target){return `<article class="block-card"><div class="block-card-head"><select class="compact-select" data-block-kind="${i}" data-target="${target}" aria-label="Paragraph ${i+1} type">${TYPES.map(t=>`<option value="${t}" ${b.kind===t?'selected':''}>${typeLabel(t)}</option>`).join('')}</select><div class="row"><span class="source-label">Paragraph ${i+1}</span><button class="icon-btn" data-action="move-block" data-target="${target}" data-index="${i}" data-dir="-1" aria-label="Move paragraph up">${icon('up')}</button><button class="icon-btn" data-action="move-block" data-target="${target}" data-index="${i}" data-dir="1" aria-label="Move paragraph down">${icon('down')}</button><button class="icon-btn danger" data-action="remove-block" data-target="${target}" data-index="${i}" aria-label="Remove paragraph">${icon('trash')}</button></div></div><textarea class="input" data-block-text="${i}" data-target="${target}" rows="${Math.max(2,Math.min(7,Math.ceil(b.text.length/100)))}" maxlength="6000" aria-label="Paragraph ${i+1} text">${esc(b.text)}</textarea></article>`;}
function renderProfile(){
 const p=S.profile||{document:{blocks:[]},confirmed:false},sum=profileSummary();
 const content=`<div class="page-head profile-heading"><div><div class="eyebrow">YOUR SOURCE OF TRUTH</div><h1>My Profile</h1><p>Your complete background. Every tailored resume begins here.</p></div><div class="profile-head-actions"><label class="btn">${icon('upload')} Import resume<input type="file" class="sr-only" accept=".docx,.pdf,.txt,.md" data-upload="resume"></label><button class="btn primary" data-action="save-profile">${icon('check')} Save profile</button></div></div>
 ${!sum.count?`<div class="empty"><span class="icon-box">${icon('user')}</span><h2>Start with your real experience.</h2><p>Upload a resume, paste your background, or try the fictional sample profile.</p><button class="btn primary" data-route="create">${icon('plus')} Add your background</button></div>`:
 `<div class="profile-layout"><section><div class="row between mb12"><span class="muted small">${sum.count} editable paragraphs &middot; ${sum.bullets} experience bullets</span><button class="btn tiny" data-action="add-block" data-target="profile">${icon('plus',true)} Add paragraph</button></div><div class="edit-blocks">${p.document.blocks.map((b,i)=>blockEditor(b,i,'profile')).join('')}</div><button class="btn full mt16" data-action="add-block" data-target="profile">${icon('plus')} Add another paragraph</button></section><aside class="profile-sidebar"><div class="card card-pad"><span class="icon-box mb12">${icon('shield')}</span><h3>${esc(sum.name)}</h3><p class="profile-note mt8">Check contact details, dates, employers, skills and certification titles. The importer preserves text, but it cannot verify that a qualification is accurate.</p><hr class="divider"><label class="checkbox-row"><input type="checkbox" id="profile-confirmed" ${p.confirmed?'checked':''}><span>I reviewed this profile and confirm that its experience and qualifications are accurate.</span></label><button class="btn primary full mt16" data-action="save-profile">Save reviewed profile ${icon('check')}</button><div class="small muted mt12" id="save-state">${S.dirty?'Unsaved changes':p.confirmed?'Profile reviewed':'Review needed'}</div><hr class="divider"><button class="btn full" data-action="images" data-target="profile">${icon('image')} Manage images</button><button class="link-button mt16" data-route="create">Continue to Create Resume ${icon('arrow',true)}</button></div></aside></div>`}`;
 $('#app').innerHTML=shell(content);
}
function setDirty(target){S.dirty=true;if(target==='profile'){S.profile.confirmed=false;const ck=$('#profile-confirmed');if(ck)ck.checked=false;}const label=$('#save-state');if(label)label.textContent='Unsaved changes';const button=$('#save-editor');if(button)button.textContent='Save changes';}
function targetDoc(target){return target==='profile'?S.profile.document:S.editor.document;}
function rememberUndo(target='editor'){if(target==='editor'){S.undo.push(clone(S.editor.document));if(S.undo.length>20)S.undo.shift();}}
function renderLibrary(){
 const total=S.resumes.length;
 const content=`<div class="page-head"><div><div class="eyebrow">ONE CAREER. MANY POSSIBILITIES.</div><h1>My Resumes</h1><p>${total} saved ${total===1?'resume':'resumes'} &middot; Organized around your next opportunity.</p></div><button class="btn primary" data-route="create">${icon('plus')} New resume</button></div><div class="library-toolbar"><label class="search">${icon('search')}<input id="library-search" type="search" placeholder="Search by role, company, or name..." value="${esc(S.search)}" aria-label="Search resumes"></label><div class="sort-row"><span>Sort:</span>${[['date','Date'],['score','Score'],['company','Company']].map(([v,t])=>`<button class="${S.sort===v?'active':''}" data-action="sort" data-value="${v}">${t}</button>`).join('')}</div></div><section id="resume-list" class="resume-list"></section><div class="bottom-note">${icon('lock')} Resumes are stored in your private database, not your GitHub repository.</div>`;
 $('#app').innerHTML=shell(content);renderResumeRows();
}
function renderResumeRows(){
 const query=S.search.toLowerCase();let rows=S.resumes.filter(r=>[r.title,r.company,r.role].join(' ').toLowerCase().includes(query));
 rows.sort((a,b)=>S.sort==='company'?a.company.localeCompare(b.company):S.sort==='score'?(b.analysis.score??-1)-(a.analysis.score??-1):b.updated-a.updated);
 $('#resume-list').innerHTML=rows.length?rows.map(r=>`<article class="resume-row"><div class="file-icon">${icon('document')}</div><div class="resume-info"><h3><span>${esc(r.title)}</span><span class="version">v${r.revision}</span></h3><div class="meta"><span>${esc(r.role||'Resume')}</span>${r.company?`<span>&middot; ${esc(r.company)}</span>`:''}<span>&middot; ${friendlyDate(r.updated)}</span></div><span class="pill neutral mt8">${esc(r.status==='local'?'Locally tailored':r.status[0].toUpperCase()+r.status.slice(1))}</span></div><div class="score-cell">${scorePill(r.analysis.score)}<small>Internal estimate</small></div><div class="row-actions"><button class="btn tiny" data-route="editor/${r.id}">Open ${icon('arrow',true)}</button><button class="icon-btn" data-action="rename" data-id="${r.id}" title="Rename" aria-label="Rename resume">${icon('edit')}</button><button class="icon-btn" data-action="duplicate" data-id="${r.id}" title="Duplicate" aria-label="Duplicate resume">${icon('copy')}</button><button class="icon-btn" data-action="export" data-id="${r.id}" title="Export" aria-label="Export resume">${icon('download')}</button><button class="icon-btn danger" data-action="delete-resume" data-id="${r.id}" title="Delete" aria-label="Delete resume">${icon('trash')}</button></div></article>`).join(''):
 `<div class="empty"><span class="icon-box">${icon('folder')}</span><h2>${query?'No matching resumes':'Your next opportunity starts here.'}</h2><p>${query?'Try another role, company or name.':'Create your first tailored resume and keep every application organized.'}</p>${query?'':'<button class="btn primary" data-route="create">Create a resume '+icon('arrow')+'</button>'}</div>`;
}
function analysisHTML(a){
 const score=a.score;
 return `<aside class="analysis-panel"><div class="analysis-head"><h3>ATS readiness &amp; job match</h3><div class="score-ring" style="--score:${score??0}"><div><strong>${score??'--'}</strong><small>/100</small></div></div><div class="score-caption"><strong>${score===null?'Add a job description':score>90?'Above your 90-point target':'Target: above 90'}</strong>Internal estimate, not an employer ATS result.<br>No score guarantees an interview.</div></div><div class="analysis-body">${(a.breakdown||[]).map(p=>`<div class="score-part"><div class="row"><span>${esc(p.label)}</span><span>${p.value}/${p.max}</span></div><div class="bar"><span style="width:${p.value/p.max*100}%"></span></div></div>`).join('')}<div class="section-label">Matched requirements &middot; ${(a.matched||[]).length}</div><div class="chips">${(a.matched||[]).map((x,i)=>`<button class="chip" data-action="evidence" data-index="${i}">${icon('check',true)} ${esc(x.term)}</button>`).join('')||'<p class="small muted">No matches assessed yet.</p>'}</div><div class="section-label">Missing or unverified</div><div class="chips">${(a.missing||[]).map(t=>`<span class="chip missing">${esc(t)}</span>`).join('')||'<p class="small muted">No missing tracked terms.</p>'}</div><p class="small muted mt12" style="font-size:10px">A missing term is a gap to review, not a skill to invent.</p>${a.omitted_ids?.length?`<div class="alert warning mt16">${icon('info')}<span>${a.omitted_ids.length} lower-priority bullets were omitted to fit the page target. Your full master profile is unchanged.</span></div>`:''}<details><summary>How this is scored</summary><p>${esc(a.method||'A transparent, local lexical check. No ATS integration.')}</p></details>${a.generation?`<details><summary>Generation details</summary><p>${esc(a.generation.provider)} &middot; ${esc(a.generation.model)}</p><p>The AI, when used, reviews up to ${a.generation.evidence_count} relevant excerpts. All ${a.generation.total_blocks} source paragraphs remain available in your master profile.</p></details>`:''}</div></aside>`;
}
function renderEditor(){
 const r=S.editor;if(!r)return;
 const content=`<div class="editor-top"><div class="breadcrumb"><button class="link-button" data-route="library">${icon('back',true)} My Resumes</button><span>/</span><span>Review &amp; refine</span></div><div class="row wrap"><div class="spacer"><input class="editor-title" id="editor-title" aria-label="Resume title" maxlength="150" value="${esc(r.title)}"><div class="row gap6 mt8"><span class="pill neutral">v${r.revision}</span><span class="small muted" id="save-state">${S.dirty?'Unsaved changes':'Saved in your workspace'}</span><span class="small muted" id="layout-count"></span></div></div><div class="actions"><button class="btn" data-action="undo" ${S.undo.length?'':'disabled'} title="Undo unsaved edit">${icon('undo')}</button><button class="btn" data-action="versions">${icon('clock')} Versions</button><button class="btn" id="save-editor" data-action="save-editor">Save changes</button><button class="btn primary" data-action="export" data-id="${r.id}">${icon('download')} Export</button></div></div></div>
 <div class="tabs mobile-editor-tabs"><button class="active" data-action="mobile-editor" data-value="resume">Resume</button><button data-action="mobile-editor" data-value="analysis">Analysis</button></div>
 <div class="editor-grid" id="editor-grid"><section class="editor-main"><div class="editor-toolbar"><div class="tabs">${[['preview','Document'],['pdf','PDF preview'],['edit','Edit text'],['changes','AI suggestions']].map(([v,t])=>`<button class="${S.editorTab===v?'active':''}" data-action="editor-tab" data-value="${v}">${t}${v==='changes'&&r.suggestions.filter(s=>s.status==='pending').length?` (${r.suggestions.filter(s=>s.status==='pending').length})`:''}</button>`).join('')}</div><div class="row"><select class="compact-select" data-editor-setting="target_pages" aria-label="Page target">${[5,6,7].map(n=>`<option value="${n}" ${r.document.target_pages===n?'selected':''}>${n} pages</option>`).join('')}</select><button class="icon-btn" data-action="images" data-target="editor" aria-label="Manage resume images">${icon('image')}</button></div></div><div id="editor-content"></div><div id="layout-warnings" class="helper mt12"></div></section>${analysisHTML(r.analysis)}</div>`;
 $('#app').innerHTML=shell(content,true);renderEditorContent();
}
function previewBlock(b,template){
 const text=esc(b.text);
 if(b.kind==='heading')return `<div class="r-heading">${text.toUpperCase()}</div>`;
 if(b.kind==='subheading')return `<div class="r-subheading">${text}</div>`;
 if(b.kind==='skill'&&b.text.includes(':')){const i=b.text.indexOf(':');return `<div class="r-skill"><strong>${esc(b.text.slice(0,i))}${template==='ats'?': ':''}</strong><span>${esc(b.text.slice(i+1))}</span></div>`;}
 if(b.kind==='image')return `<img src="/api/images/${esc(b.id)}" style="max-width:220px;max-height:150px;object-fit:contain;margin:10px 0" alt="${text}">`;
 let styled=text;
 for(const phrase of [...new Set(b.bold||[])].sort((a,b)=>b.length-a.length).slice(0,20)){
  const e=esc(phrase);if(e.length>2)styled=styled.split(/(<strong>.*?<\/strong>)/).map(s=>s.startsWith('<strong>')?s:s.split(e).join('<strong>'+e+'</strong>')).join('');
 }
 return `<div class="${b.kind==='bullet'?'r-bullet':'r-paragraph'}">${styled}</div>`;
}
function renderDocument(){
 const r=S.editor,p=S.preview;
 if(!p)return '<div class="boot" style="min-height:360px"><span class="loader"></span><p>Measuring the document...</p></div>';
 const header=r.document.blocks.filter(b=>['name','subtitle','contact'].includes(b.kind));
 const images=S.images.filter(a=>r.document.image_ids.includes(a.id)&&a.verified&&a.placement==='header').slice(0,3);
 return `<div class="document-wrap">${p.pages.map((blocks,i)=>`<article class="resume-paper ${r.document.template==='ats'?'ats':''}" aria-label="Resume page ${i+1}">${i===0?`<div class="resume-header"><div>${header.map(b=>`<div class="resume-${b.kind}">${esc(b.text)}</div>`).join('')}</div>${r.document.template!=='ats'?`<div class="resume-header-images">${images.map(a=>`<img src="/api/images/${esc(a.id)}" alt="${esc(a.label)}">`).join('')}</div>`:''}</div>`:''}${blocks.map(b=>previewBlock(b,r.document.template)).join('')}<div class="resume-page-number">Page ${i+1} of ${p.pages.length}</div></article>`).join('')}</div><p class="small muted mt8" style="font-size:10px">Reading preview. Use PDF preview to check exact printable layout; DOCX pagination can vary with installed fonts.</p>`;
}
function renderEditorContent(){
 const r=S.editor;const el=$('#editor-content');if(!el)return;
 if(S.editorTab==='preview'){el.innerHTML=(S.dirty?`<div class="alert warning mb12">${icon('info')}Save your edits to update this document preview and page count.</div>`:'')+renderDocument();}
 else if(S.editorTab==='pdf'){
  el.innerHTML=S.dirty?`<div class="alert warning">${icon('info')}Save your changes to refresh the exact PDF preview.</div>`:`<iframe class="pdf-frame" title="Actual printable resume PDF" src="/api/resumes/${r.id}/export/pdf?inline=true&rev=${r.revision}"></iframe><p class="small muted mt8">If your mobile browser does not embed PDFs, use Export to open the file.</p>`;
 }else if(S.editorTab==='edit'){
  el.innerHTML=`<div class="row wrap mb12"><select class="compact-select" data-editor-setting="template" aria-label="Resume template">${[['reference','Reference'],['ats','ATS Clean'],['minimal','Minimal']].map(([v,t])=>`<option value="${v}" ${r.document.template===v?'selected':''}>${t}</option>`).join('')}</select><select class="compact-select" data-editor-setting="font" aria-label="Document font">${['Aptos','Calibri','Arial','Times New Roman'].map(t=>`<option ${r.document.font===t?'selected':''}>${t}</option>`).join('')}</select><select class="compact-select" data-editor-setting="paper" aria-label="Paper size"><option value="letter" ${r.document.paper==='letter'?'selected':''}>US Letter</option><option value="a4" ${r.document.paper==='a4'?'selected':''}>A4</option></select><span class="spacer"></span><button class="btn tiny" data-action="add-block" data-target="editor">${icon('plus',true)} Add paragraph</button></div><div class="edit-scroll"><div class="edit-blocks">${r.document.blocks.map((b,i)=>blockEditor(b,i,'editor')).join('')}</div></div>`;
 }else{
  el.innerHTML=r.suggestions.length?r.suggestions.map((s,i)=>`<article class="suggestion"><div class="row between"><h3>Evidence-based rewrite</h3><span class="pill ${s.status==='accepted'?'success':'neutral'}">${esc(s.status)}</span></div><p class="muted">${esc(s.reason)}</p><p class="before"><b>Original:</b> ${esc(s.original)}</p><p class="after"><b>Suggested:</b> ${esc(s.proposed)}</p><p class="small muted">Check every fact against your original background. Suggestions are never applied automatically.</p>${s.status==='pending'?`<div class="row"><button class="btn tiny" data-action="suggestion" data-index="${i}" data-value="dismiss">Dismiss</button><button class="btn tiny primary" data-action="suggestion" data-index="${i}" data-value="accept">Confirm &amp; accept ${icon('check',true)}</button></div>`:''}</article>`).join(''):`<div class="empty"><span class="icon-box">${icon('check')}</span><h2>Your facts are unchanged.</h2><p>${r.status==='local'?'Local tailoring ranks your existing evidence without calling an AI model. AI rewrite suggestions are available when an enabled provider successfully returns them.':'No supported rewrite suggestions were returned for this resume. You can still edit any paragraph yourself.'}</p><button class="btn" data-action="editor-tab" data-value="edit">Edit resume text</button></div>`;
 }
}
async function refreshPreview(){
 if(!S.editor)return;const id=S.editor.id;
 try{const p=await api(`/resumes/${id}/preview`);if(S.editor?.id!==id)return;S.preview=p;
 const el=$('#layout-count');if(el)el.textContent=`\u00b7 ${p.pages.length} actual PDF pages`;
 const warn=$('#layout-warnings');if(warn)warn.innerHTML=p.warnings.map(w=>esc(w)).join('<br>');
 if(S.editorTab==='preview')renderEditorContent();
 }catch(e){const el=$('#editor-content');if(el)el.innerHTML=`<div class="alert danger">${icon('info')} ${esc(e.message)}</div>`;}
}
async function saveEditor(){
 if(!S.editor)return;const r=S.editor;
 if(!r.title.trim())throw new Error('Give this resume a title.');
 const payload={title:r.title,role:r.role,company:r.company,jd:r.jd,document:r.document,revision:r.revision};
 S.editor=await api('/resumes/'+r.id,{method:'PUT',body:payload});S.dirty=false;renderEditor();await refreshPreview();toast('Changes saved as a new version.');
}
async function generateResume(){
 if(S.busy)return;S.busy=true;updateGenerateState();
 try{
  await saveCreate(true);
  const request={...S.form,demo:S.form.mode==='local',consent:S.form.consent,
    title:[S.form.role||'Tailored resume',S.form.company].filter(Boolean).join(' - '),idempotency_key:crypto.randomUUID()};
  delete request.mode;
  modal(modalHead(S.form.mode==='local'?'Tailoring your experience':'Creating your tailored resume')+`<div class="modal-body"><div class="progress-content"><div class="progress-orb"><span class="loader"></span></div><h2 id="progress-stage">Preparing your source evidence</h2><p>No new qualifications are added. Your source profile stays unchanged.</p><div class="progress-events" id="progress-events"><p>Saving a recoverable draft...</p></div></div></div>`);
  const result=await api('/generate',{method:'POST',body:request});
  let final=result;
  if(result.job_id){
   // Keep the page open for status; the server owns the job and quota reservation.
   for(let i=0;i<190;i++){
    await new Promise(resolve=>setTimeout(resolve,1600));
    final=await api('/jobs/'+result.job_id);
    const stage=$('#progress-stage');if(stage)stage.textContent=final.stage;
    const events=$('#progress-events');if(events)events.innerHTML=(final.events.length?final.events:['Analyzing relevant source excerpts...']).map(e=>`<p>${esc(e)}</p>`).join('');
    if(final.status!=='running')break;
   }
  }
  closeDialogs();await refreshMe();S.dirty=false;
  await navigate('editor/'+result.resume_id);
  if(final.status==='failed')toast(final.error||'The provider could not complete generation. Your draft is saved.',true);
  else if(final.status==='running')toast('Still processing. Your draft is saved; reopen it from My Resumes shortly.');
  else toast('Your tailored resume is ready to review.');
 }finally{S.busy=false;updateGenerateState();}
}
async function showSettings(){const data=await api('/settings');S.settingsDraft=clone(data.settings);S.me.providers=data.providers;S.me.usage=data.usage;renderSettings();}
function renderSettings(){
 const d=S.settingsDraft,u=S.me.usage;
 const statusNames={not_configured:'Not configured',configured:'Configured',ready:'Last request succeeded',cooling_down:'Cooling down',unavailable:'Unavailable'};
 drawer(drawerHead('Workspace Settings','Free-model routing, appearance, and your private data.')+`<div class="drawer-body"><div class="alert"><div class="spacer"><b>Automatic fallback</b><div class="small mt8">Try another enabled free provider when one is unavailable.</div></div><label class="toggle"><input type="checkbox" data-setting="fallback" ${d.fallback?'checked':''} aria-label="Automatic fallback"><span></span></label></div><div class="alert warning mt12">${icon('info')}<span>If every provider fails, your draft is kept. No silent paid-model switch. Free capacity is not guaranteed.</span></div><div class="section-label">PROVIDERS &middot; PRIORITY ORDER</div>${S.me.providers.map((p,i)=>`<div class="provider"><div class="row between"><div><div class="provider-title"><span class="muted">${i+1}</span><b>${esc(p.name)}</b><span class="status-dot ${p.status}"></span><span class="small muted" style="font-size:10px">${statusNames[p.status]||esc(p.status)}</span></div><div class="mono">${p.models.map(esc).join('<br>')}</div></div><label class="toggle"><input type="checkbox" data-provider="${p.id}" ${d.enabled.includes(p.id)?'checked':''} aria-label="Enable ${esc(p.name)}"><span></span></label></div><p>${esc(p.note)}</p><div class="row between mt8 small muted" style="font-size:10px"><span>Reported quota remaining</span><span>${p.remaining_requests!==null&&p.remaining_requests!==undefined?esc(p.remaining_requests)+' requests/day':'Unknown'}</span></div>${p.remaining_tokens!==null&&p.remaining_tokens!==undefined?`<p>${esc(p.remaining_tokens)} tokens/minute remaining at last response.</p>`:''}${p.last_checked?`<p>Last checked ${new Date(p.last_checked*1000).toLocaleString()}</p>`:''}</div>`).join('')}<p class="small muted" style="font-size:10px">Keys are configured on the server using GROQ_API_KEY / OPENROUTER_API_KEY. They never enter this browser or your GitHub source files.</p><div class="section-label">DAILY LIMIT</div><div class="setting-row"><span>Successful generations today</span><b>${u.used} / 15</b></div><div class="setting-row"><span>Currently reserved</span><b>${u.reserved}</b></div><div class="setting-row"><span>Resets at midnight</span><span>${esc(u.timezone)}</span></div><p class="small muted mt8" style="font-size:10px">AI and local tailored generations count. Editing, exporting, and automatic retries do not add another count. Provider quotas are separate.</p><div class="section-label">BACKGROUND PALETTE</div><div class="theme-options">${['lavender','ocean','sage'].map(t=>`<button class="theme-button ${d.theme===t?'active':''}" data-action="theme" data-value="${t}"><div class="swatch ${t}"></div>${t[0].toUpperCase()+t.slice(1)}</button>`).join('')}</div><div class="section-label">YOUR DATA</div><button class="btn full" data-action="backup">${icon('download')} Download private backup</button><button class="link-button mt16" data-action="delete-data" style="color:var(--danger)">Delete all resume and profile data</button><p class="small muted mt8" style="font-size:10px">Deletion does not reset today's usage. Store downloaded backups privately; they contain personal information.</p></div><div class="drawer-foot"><button class="btn full primary" data-action="save-settings">Save settings</button></div>`);
}
function imageSelection(){if(S.imageTarget==='editor')return S.editor.document.image_ids;if(S.imageTarget==='profile')return S.profile.document.image_ids;return S.form.image_ids;}
function setImageSelection(ids){if(S.imageTarget==='editor'){rememberUndo();S.editor.document.image_ids=ids;setDirty('editor');}else if(S.imageTarget==='profile'){S.profile.document.image_ids=ids;setDirty('profile');}else S.form.image_ids=ids;}
async function showImages(target){S.imageTarget=target||'create';[S.images,S.catalog]=await Promise.all([api('/images'),api('/badges')]);renderImages();}
function renderImages(){
 const selected=imageSelection();
 drawer(drawerHead('Images & Certification Badges','Your images. Your credentials. Always review before displaying.')+`<div class="drawer-body"><div class="alert">${icon('image')}<span>Up to 3 header badges plus end-of-resume images. ATS Clean exports omit all pictures while keeping your written qualifications.</span></div><label class="dropzone mt16" style="height:125px" data-drop="image"><input type="file" accept="image/png,image/jpeg,image/webp" data-upload="image" aria-label="Upload badge or image"><span class="icon-box">${icon('upload')}</span><strong>Upload an image</strong><p>PNG, JPG or WebP &middot; Up to 4 MB</p></label><div class="section-label">YOUR IMAGE LIBRARY &middot; ${S.images.length}</div><div class="asset-grid">${S.images.map(a=>`<div class="asset ${selected.includes(a.id)?'selected':''}"><img src="/api/images/${a.id}" alt="${esc(a.label)}"><div class="row between"><h4>${esc(a.label)}</h4><button class="icon-btn danger" data-action="delete-image" data-id="${a.id}" title="Delete image" aria-label="Delete image">${icon('trash')}</button></div><select class="compact-select" data-image-placement="${a.id}" aria-label="Image placement"><option value="header" ${a.placement==='header'?'selected':''}>Header badge</option><option value="end" ${a.placement==='end'?'selected':''}>End of resume</option></select><button class="btn tiny ${selected.includes(a.id)?'soft':''}" data-action="select-image" data-id="${a.id}">${icon(selected.includes(a.id)?'check':'plus',true)} ${selected.includes(a.id)?'Selected':'Review & add'}</button><button class="link-button" data-action="rename-image" data-id="${a.id}" style="font-size:10px">Edit label</button></div>`).join('')||'<p class="small muted">Import a DOCX to recover its embedded badges, or upload an image.</p>'}</div><div class="section-label">FETCH FROM ISSUER SOURCES</div><p class="small muted" style="font-size:11px">Adding artwork does not prove certification. Use only credentials you earned and are entitled to display.</p>${S.catalog.map(b=>`<div class="catalog-row"><h4>${esc(b.label)}</h4><p>${esc(b.note)}</p><div class="row"><a href="${esc(b.source)}" target="_blank" rel="noopener noreferrer">View issuer ${icon('external',true)}</a><button class="btn tiny" data-action="fetch-badge" data-id="${b.id}" ${b.available?'':'disabled'}>${b.available?'Fetch badge':'Upload earned badge'}</button></div></div>`).join('')}<div class="alert warning mt16">${icon('info')}<span>The reference's AWS image is Solutions Architect, while its text says Developer. Select the one you actually earned; do not assume they are interchangeable.</span></div></div><div class="drawer-foot"><button class="btn primary full" data-action="done-images">Done &middot; ${selected.length} selected</button></div>`);
}
async function showExport(id){
 if(S.editor?.id===id&&S.dirty){if(!confirm('Save your edits before exporting?'))return;await saveEditor();}
 S.exportId=id;S.exportFormat='pdf';S.exportClean=false;
 const data=await api('/resumes/'+id);const layout=await api('/resumes/'+id+'/layout');S.exportData=data;S.exportLayout=layout;renderExport();
}
function renderExport(){const r=S.exportData,l=S.exportLayout;
 modal(modalHead('Export your resume')+`<div class="modal-body"><div class="row mb12"><span class="icon-box">${icon('document')}</span><div><h3>${esc(r.title)}</h3><p class="small muted mt8">${l.pages} PDF pages &middot; ${r.document.paper==='letter'?'US Letter':'A4'} &middot; ${r.document.font}</p></div></div><div class="section-label">FILE FORMAT</div><div class="export-options">${[['pdf','PDF','Ready to share'],['docx','Word','Fully editable'],['txt','Plain text','Inspect extraction']].map(([v,t,d])=>`<button class="option ${S.exportFormat===v?'active':''}" data-action="export-format" data-value="${v}">${icon('document')}<strong style="display:block">${t}</strong><small>${d}</small></button>`).join('')}</div><label class="checkbox-row mt24"><input type="checkbox" id="export-clean" ${S.exportClean?'checked':''}><span><b>ATS Clean version</b><br>Remove all images, decorative rules and skill tables. Keep the same resume text. Page count may change.</span></label><div class="section-label">FINAL REVIEW</div><label class="checkbox-row"><input type="checkbox" id="export-reviewed"><span>I reviewed contact details, dates, qualifications and any accepted AI suggestions. The resume accurately represents my experience.</span></label><div class="alert mt16">${icon('info')}<span>PDF uses the server's installed font. Word requests ${esc(r.document.font)} and may paginate differently on another computer. No employer ATS score is guaranteed.</span></div></div><div class="modal-foot"><button class="btn" data-action="close-modal">Cancel</button><button class="btn primary" id="download-export" data-action="download-export" disabled>${icon('download')} Download ${S.exportFormat.toUpperCase()}</button></div>`);
}
function showVersions(){const history=S.editor.history||[];modal(modalHead('Saved versions')+`<div class="modal-body"><p class="small muted mb12">The most recent 10 prior versions are kept. Restoring opens that content for review; save to create a new current version.</p><div class="version-row"><span>v${S.editor.revision} &middot; Current version</span><span class="pill success">Current</span></div>${history.slice().reverse().map((h,i)=>`<div class="version-row"><div><b>v${h.revision}</b><span class="muted"> &middot; ${friendlyDate(h.updated)}</span></div><button class="btn tiny" data-action="restore-version" data-index="${history.length-1-i}">Restore</button></div>`).join('')||'<p class="small muted mt16">Save your first edit to start version history.</p>'}</div><div class="modal-foot"><button class="btn" data-action="close-modal">Close</button></div>`);}
function addBlockDialog(target){modal(modalHead('Add a paragraph')+`<div class="modal-body stack"><div class="field"><label for="new-kind">Type</label><select class="input" id="new-kind">${TYPES.map(t=>`<option value="${t}" ${t==='bullet'?'selected':''}>${typeLabel(t)}</option>`).join('')}</select></div><div class="field"><label for="new-text">Text</label><textarea class="input" id="new-text" rows="5" maxlength="6000" placeholder="Add only information supported by your experience."></textarea></div></div><div class="modal-foot"><button class="btn" data-action="close-modal">Cancel</button><button class="btn primary" data-action="insert-block" data-target="${target}">Add paragraph</button></div>`);}
function accountMenu(){modal(modalHead('Your private workspace')+`<div class="modal-body"><p class="muted small">This is a single-owner application protected by the password configured on your server. It is not a multi-user SaaS service.</p><div class="row mt24"><button class="btn full" data-action="backup">${icon('download')} Private backup</button><button class="btn full" data-action="logout">${icon('logout')} Sign out</button></div></div>`);}

/* All dynamic document text is escaped before display. Events are delegated; no inline handlers. */
document.addEventListener('submit',async event=>{
 if(event.target.id!=='login-form')return;event.preventDefault();const button=$('button',event.target);button.disabled=true;
 try{const data=await api('/login',{method:'POST',body:{password:$('#password').value}});S.csrf=data.csrf;await boot();}
 catch(e){$('#login-error').textContent=e.message;button.disabled=false;}
});
document.addEventListener('click',async event=>{
 const nav=event.target.closest('[data-route]');if(nav){event.preventDefault();try{await navigate(nav.dataset.route);}catch(e){toast(e.message,true);}return;}
 const el=event.target.closest('[data-action]');if(!el||el.disabled)return;
 const {action,value,id,index,target}=el.dataset;
 try{
  switch(action){
   case 'close-modal':$('#modal').close();break;
   case 'close-drawer':$('#drawer').close();document.body.dataset.theme=S.me?.settings?.theme||'lavender';break;
   case 'account':accountMenu();break;
   case 'logout':if(!canLeave())break;await api('/logout',{method:'POST'});S.dirty=false;closeDialogs();renderLogin();break;
   case 'background-tab':S.backgroundTab=value;renderCreate();break;
   case 'job-tab':S.jobTab=value;renderCreate();break;
   case 'choose-pages':S.form.target_pages=Number(value);renderCreate();break;
   case 'choose-template':S.form.template=value;renderCreate();break;
   case 'sample-profile':{
    if(S.profile?.document?.blocks.length&&!confirm('Replace your master profile with a fictional sample? Existing tailored resumes are kept.'))break;
    const sample=await api('/sample');S.profile={document:sample.document,confirmed:true};await api('/profile',{method:'PUT',body:S.profile});S.backgroundTab='upload';renderCreate();toast('Fictional sample loaded. Replace it with your own profile before applying.');break;}
   case 'sample-job':{const sample=await api('/sample');S.form.jd=sample.jd;S.form.role='Senior Java Full Stack Developer';S.form.company='Example Organization';S.jobTab='paste';renderCreate();break;}
   case 'parse-paste':{
    const text=$('#manual-background').value;if(text.trim().length<30)throw new Error('Paste your full resume first.');
    if(S.profile?.document?.blocks.length&&!confirm('Replace the master profile with this text?'))break;
    const data=await api('/import-text',{method:'POST',body:{text}});S.profile={document:data.document,confirmed:false};await api('/profile',{method:'PUT',body:S.profile});await navigate('profile');break;}
   case 'save-profile':{
    if($('#profile-confirmed'))S.profile.confirmed=$('#profile-confirmed').checked;
    if(S.profile.document.blocks.some(b=>!b.text.trim()))throw new Error('Remove empty paragraphs or enter their text before saving.');
    S.profile=await api('/profile',{method:'PUT',body:S.profile});S.dirty=false;renderProfile();toast(S.profile.confirmed?'Your reviewed profile is saved.':'Profile saved. Confirm its accuracy before generating.');break;}
   case 'save-create':await saveCreate();break;
   case 'generate':await generateResume();break;
   case 'settings':await showSettings();break;
   case 'theme':S.settingsDraft.theme=value;document.body.dataset.theme=value;renderSettings();break;
   case 'save-settings':await api('/settings',{method:'PUT',body:S.settingsDraft});S.me.settings=clone(S.settingsDraft);document.body.dataset.theme=S.settingsDraft.theme;$('#drawer').close();toast('Workspace settings saved.');break;
   case 'backup':await download('/backup','rolefit-private-backup.json');break;
   case 'delete-data':{
    const typed=prompt('This deletes your profile, saved resumes and image library. Download a backup first. Type DELETE MY DATA to confirm.');if(typed!=='DELETE MY DATA')break;
    await api('/private-data',{method:'DELETE',body:{confirmation:typed}});S.dirty=false;S.form={...S.form,jd:'',role:'',company:'',image_ids:[],consent:false};closeDialogs();await boot();toast('Private documents and images deleted. Usage remains unchanged.');break;}
   case 'images':await showImages(target);break;
   case 'done-images':$('#drawer').close();if(S.imageTarget==='create')renderCreate();else if(S.imageTarget==='profile')renderProfile();else renderEditor();break;
   case 'select-image':{
    const a=S.images.find(x=>x.id===id),selection=[...imageSelection()];
    if(selection.includes(id)){setImageSelection(selection.filter(x=>x!==id));renderImages();break;}
    if(selection.length>=6)throw new Error('Choose at most 6 images. Use up to 3 in the header.');
    if(a.placement==='header'&&S.images.filter(x=>selection.includes(x.id)&&x.placement==='header').length>=3)throw new Error('The header holds up to 3 badges. Set this image to End of resume.');
    if(!a.verified){if(!confirm('I have permission to use this image, and any credential it represents is one I actually earned. Continue?'))break;await api('/images/'+id,{method:'PATCH',body:{label:a.label,verified:true,placement:a.placement}});a.verified=true;}
    selection.push(id);setImageSelection(selection);renderImages();break;}
   case 'delete-image':{
    if(!confirm('Delete this image from your library? Saved resumes using it will no longer display it.'))break;
    await api('/images/'+id,{method:'DELETE'});setImageSelection(imageSelection().filter(x=>x!==id));S.images=await api('/images');renderImages();break;}
   case 'rename-image':{
    const a=S.images.find(x=>x.id===id),name=prompt('Image label',a.label);if(!name?.trim())break;
    await api('/images/'+id,{method:'PATCH',body:{label:name.trim(),verified:a.verified,placement:a.placement}});S.images=await api('/images');renderImages();break;}
   case 'fetch-badge':{
    const b=S.catalog.find(x=>x.id===id);if(!confirm(`Confirm that you earned ${b.label} and are entitled to display its badge. Fetch official artwork?`))break;
    el.disabled=true;el.textContent='Fetching...';await api('/badges/import',{method:'POST',body:{catalog_id:id,confirmed:true}});S.images=await api('/images');renderImages();toast('Issuer artwork added. Select it to include it in your resume.');break;}
   case 'sort':S.sort=value;renderLibrary();break;
   case 'delete-resume':if(confirm('Delete this saved resume and its version history? Your master profile stays unchanged.')){await api('/resumes/'+id,{method:'DELETE'});S.resumes=await api('/resumes');renderLibrary();toast('Resume deleted.');}break;
   case 'duplicate':{const r=await api('/resumes/'+id+'/duplicate',{method:'POST'});toast('Copy created without an AI call.');await navigate('editor/'+r.id);break;}
   case 'rename':{
    const r=await api('/resumes/'+id),title=prompt('Resume name',r.title);if(!title?.trim())break;
    await api('/resumes/'+id,{method:'PUT',body:{title:title.trim(),company:r.company,role:r.role,jd:r.jd,document:r.document,revision:r.revision}});S.resumes=await api('/resumes');renderLibrary();break;}
   case 'editor-tab':S.editorTab=value;renderEditor();if(value==='preview')await refreshPreview();break;
   case 'save-editor':await saveEditor();break;
   case 'undo':if(S.undo.length){S.editor.document=S.undo.pop();setDirty();renderEditor();}break;
   case 'versions':showVersions();break;
   case 'restore-version':rememberUndo();S.editor.document=clone(S.editor.history[Number(index)].document);setDirty();$('#modal').close();S.editorTab='edit';renderEditor();toast('Prior content restored. Save to make it the current version.');break;
   case 'mobile-editor':$('#editor-grid').classList.toggle('show-analysis',value==='analysis');$$('.mobile-editor-tabs button').forEach(b=>b.classList.toggle('active',b.dataset.value===value));break;
   case 'add-block':addBlockDialog(target);break;
   case 'insert-block':{
    const text=$('#new-text').value.trim();if(!text)throw new Error('Enter the paragraph text.');rememberUndo(target);
    const ident='b-'+crypto.randomUUID();targetDoc(target).blocks.push({id:ident,kind:$('#new-kind').value,text,bold:[],source_id:ident});setDirty(target);$('#modal').close();target==='profile'?renderProfile():renderEditorContent();toast('Paragraph added at the end. Use the arrows to move it.');break;}
   case 'move-block':{
    const i=Number(index),j=i+Number(el.dataset.dir),blocks=targetDoc(target).blocks;if(j<0||j>=blocks.length)break;rememberUndo(target);[blocks[i],blocks[j]]=[blocks[j],blocks[i]];setDirty(target);target==='profile'?renderProfile():renderEditorContent();break;}
   case 'remove-block':if(confirm('Remove this paragraph from this document?')){rememberUndo(target);targetDoc(target).blocks.splice(Number(index),1);setDirty(target);target==='profile'?renderProfile():renderEditorContent();}break;
   case 'evidence':{const m=S.editor.analysis.matched[Number(index)];modal(modalHead('Evidence for '+m.term)+`<div class="modal-body"><div class="alert success">${icon('check')}Found in the current resume text.</div><p class="mt16" style="line-height:1.8">${esc(m.evidence)}</p><p class="small muted mt16">Keyword presence is not independent verification of proficiency.</p></div><div class="modal-foot"><button class="btn" data-action="close-modal">Close</button></div>`);break;}
   case 'suggestion':{
    if(S.dirty){if(!confirm('Save your current edits before reviewing this suggestion?'))break;await saveEditor();}
    if(value==='accept'&&!confirm('Confirm that every skill, number, date and statement in this rewrite is accurate and supported by your experience.'))break;
    S.editor=await api(`/resumes/${S.editor.id}/suggestions/${index}`,{method:'POST',body:{action:value,confirmed:value==='accept',revision:S.editor.revision}});S.dirty=false;renderEditor();toast(value==='accept'?'Suggested wording accepted.':'Suggestion dismissed.');break;}
   case 'export':await showExport(id);break;
   case 'export-format':S.exportFormat=value;renderExport();break;
   case 'download-export':{
    if(!$('#export-reviewed').checked)throw new Error('Review the resume and tick the confirmation first.');
    S.exportClean=$('#export-clean').checked;el.disabled=true;
    try{await download(`/resumes/${S.exportId}/export/${S.exportFormat}?clean=${S.exportClean}`);toast('Your resume file is ready.');$('#modal').close();}finally{el.disabled=false;}break;}
  }
 }catch(e){S.busy=false;updateGenerateState();if(action==='generate')closeDialogs();if(el.isConnected)el.disabled=false;toast(e.message,true);}
});
document.addEventListener('input',event=>{
 const el=event.target;
 if(el.dataset.form){const key=el.dataset.form;S.form[key]=el.type==='checkbox'?el.checked:el.value;if(key==='jd'&&$('#jd-count'))$('#jd-count').textContent=`${el.value.length.toLocaleString()} / 12,000 characters`;if(key==='mode'&&$('#consent-row'))$('#consent-row').style.display=el.value==='local'?'none':'';updateGenerateState();}
 if(el.id==='library-search'){S.search=el.value;renderResumeRows();}
 if(el.id==='editor-title'){S.editor.title=el.value;setDirty();}
 if(el.dataset.blockText!==undefined){const target=el.dataset.target;targetDoc(target).blocks[Number(el.dataset.blockText)].text=el.value;setDirty(target);}
 if(el.id==='export-reviewed')$('#download-export').disabled=!el.checked;
 if(el.id==='export-clean')S.exportClean=el.checked;
});
document.addEventListener('focusin',event=>{const el=event.target;if(el.dataset.blockText!==undefined&&el.dataset.target==='editor')rememberUndo();});
document.addEventListener('change',async event=>{
 const el=event.target;
 try{
  if(el.dataset.upload){await uploadFile(el.dataset.upload,el.files?.[0]);el.value='';}
  if(el.dataset.blockKind!==undefined){const target=el.dataset.target;rememberUndo(target);targetDoc(target).blocks[Number(el.dataset.blockKind)].kind=el.value;setDirty(target);}
  if(el.dataset.editorSetting){rememberUndo();const k=el.dataset.editorSetting;S.editor.document[k]=k==='target_pages'?Number(el.value):el.value;setDirty();toast('Layout preference changed. Save to recompute the printable pages.');}
  if(el.dataset.setting){S.settingsDraft[el.dataset.setting]=el.checked;}
  if(el.dataset.provider){const set=new Set(S.settingsDraft.enabled);el.checked?set.add(el.dataset.provider):set.delete(el.dataset.provider);S.settingsDraft.enabled=[...set];}
  if(el.dataset.imagePlacement){const a=S.images.find(x=>x.id===el.dataset.imagePlacement);await api('/images/'+a.id,{method:'PATCH',body:{label:a.label,verified:a.verified,placement:el.value}});a.placement=el.value;renderImages();}
 }catch(e){toast(e.message,true);}
});
document.addEventListener('dragover',e=>{const zone=e.target.closest('[data-drop]');if(zone){e.preventDefault();zone.classList.add('drag');}});
document.addEventListener('dragleave',e=>{const zone=e.target.closest('[data-drop]');if(zone)zone.classList.remove('drag');});
document.addEventListener('drop',async e=>{const zone=e.target.closest('[data-drop]');if(!zone)return;e.preventDefault();zone.classList.remove('drag');try{await uploadFile(zone.dataset.drop,e.dataTransfer.files[0]);}catch(error){toast(error.message,true);}});
window.addEventListener('beforeunload',e=>{if(S.dirty){e.preventDefault();e.returnValue='';}});
window.addEventListener('popstate',async()=>{if(!canLeave()){history.pushState(null,'','#'+S.route);return;}S.dirty=false;try{await loadRoute(location.hash.slice(1)||'create');}catch(e){toast(e.message,true);}});
boot();

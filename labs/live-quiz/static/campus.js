(() => {
  'use strict';
  const root = document.querySelector('[data-campus-week]');
  if (!root) return;
  const $ = s => root.querySelector(s);
  const cost=$('[data-cost-model]');
  cost?.addEventListener('input',()=>{const hours=Number($('[data-cost-hours]').value);const edge=$('[data-cost-edge]').checked?730:hours;const compute=2*.0264*hours+.0132*edge;const storage=72*.096,ipv4=730*.005;$('[data-cost-hours-label]').textContent=`${hours} hours`;$('[data-cost-total]').textContent=`$${(compute+storage+ipv4).toFixed(2)} AWS / month`;$('[data-cost-detail]').textContent=`Compute $${compute.toFixed(2)} + 72 GiB gp3 $${storage.toFixed(2)} + one IPv4 $${ipv4.toFixed(2)}.`;});
  const nodes = [...root.querySelectorAll('[data-flow] li')];
  let step = 0, timer = null, slide = 0;
  function showStep() {
    nodes.forEach((n, i) => {n.classList.toggle('active', i === step); if(i===step)n.setAttribute('aria-current','step');else n.removeAttribute('aria-current');});
    $('[data-flow-status]').textContent = `Step ${step+1} of ${nodes.length}: ${nodes[step].querySelector('strong').textContent}`;
  }
  function stopMotion() {clearInterval(timer);timer=null;if($('[data-flow-play]'))$('[data-flow-play]').textContent='Play sequence';}
  $('[data-flow-next]')?.addEventListener('click',()=>{stopMotion();step=(step+1)%nodes.length;showStep();});
  $('[data-flow-prev]')?.addEventListener('click',()=>{stopMotion();step=(step+nodes.length-1)%nodes.length;showStep();});
  $('[data-flow-play]')?.addEventListener('click',()=>{if(timer){stopMotion();return;} $('[data-flow-play]').textContent='Pause sequence';timer=setInterval(()=>{step=(step+1)%nodes.length;showStep();if(step===nodes.length-1)stopMotion();},2400);});
  document.addEventListener('visibilitychange',()=>{if(document.hidden)stopMotion();});
  const slides=[...root.querySelectorAll('[data-slide]')];
  function showSlide(){slides.forEach((s,i)=>s.hidden=i!==slide);$('[data-slide-count]').textContent=`${slide+1} / ${slides.length}`;}
  $('[data-present]')?.addEventListener('click',()=>{stopMotion();root.classList.add('oc-presentation');$('[data-presentation-bar]').hidden=false;slide=0;showSlide();root.scrollIntoView({block:'start'});$('[data-slide-next]').focus();});
  function closeSlides(){root.classList.remove('oc-presentation');slides.forEach(s=>s.hidden=false);$('[data-presentation-bar]').hidden=true;$('[data-present]').focus();}
  $('[data-present-close]')?.addEventListener('click',closeSlides);
  $('[data-slide-next]')?.addEventListener('click',()=>{slide=(slide+1)%slides.length;showSlide();});
  $('[data-slide-prev]')?.addEventListener('click',()=>{slide=(slide+slides.length-1)%slides.length;showSlide();});
  root.addEventListener('keydown',e=>{if(e.key==='Escape'&&root.classList.contains('oc-presentation'))closeSlides();});
  const model=$('[data-model]');
  model?.addEventListener('change',()=>{const a=model.querySelector('[data-control=identity]').checked,b=model.querySelector('[data-control=boundary]').checked;model.querySelector('output').textContent=a&&b?'Both modeled requirements hold. This is one checked path, not a universal safety claim.':`Requirement ${!a?'1':''}${!a&&!b?' and ':''}${!b?'2':''} fails. A defended design must reject or prevent this operation. Compare the exact mechanism with the worked example.`;});
  async function api(action, data={}) {
    const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),45000);
    try{const r=await fetch(`/campus/api/${action}`,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRF-Token':root.dataset.csrf},body:JSON.stringify(data),signal:controller.signal});let result;try{result=await r.json();}catch{throw new Error('The service could not return a response. Refresh the page and try again.');}if(!r.ok)throw new Error(result.error||'Request was not accepted.');return result;}finally{clearTimeout(timeout);}
  }
  const accountProgress=$('[data-account-progress]');
  if(accountProgress){
    const applyProgress=data=>{for(const box of root.querySelectorAll('[data-campus-check]'))box.checked=(data.progress||[]).some(r=>r.week===Number(root.dataset.campusWeek)&&r.checkpoint===box.dataset.campusCheck&&r.value);$('[data-progress-message]').textContent=`${data.completed} of 57 personal checkpoints recorded. These are self-checks, not grades.`;};
    api('progress').then(applyProgress).catch(()=>{$('[data-progress-message]').textContent='Progress could not be loaded. Refresh before recording changes.';root.querySelectorAll('[data-campus-check]').forEach(b=>b.disabled=true);});
    accountProgress.addEventListener('change',async e=>{const box=e.target;if(!box.dataset.campusCheck)return;box.disabled=true;try{applyProgress(await api('progress',{week:Number(root.dataset.campusWeek),checkpoint:box.dataset.campusCheck,value:box.checked}));}catch(err){box.checked=!box.checked;$('[data-progress-message]').textContent=err.message;}finally{box.disabled=false;}});
  }
  const form=$('[data-guide-form]');
  form?.addEventListener('submit',async e=>{e.preventDefault();const button=form.querySelector('button'),panel=$('.oc-guide'),out=$('[data-guide-result]');button.disabled=true;panel.classList.add('busy');out.replaceChildren();const waiting=document.createElement('p');waiting.textContent='Scout is checking the lesson sources…';out.append(waiting);
    try{const data=await api('guide',{question:form.elements.question.value,week:Number(root.dataset.campusWeek)});out.replaceChildren();const answer=document.createElement('p');answer.className='oc-guide-answer';answer.textContent=data.answer||data.error||'No explanation was returned.';out.append(answer);const list=document.createElement('ul');list.className='oc-guide-sources';for(const s of data.sources||[]){if(!/^\/(?:campus|learn)(?:\/|$)/.test(s.url))continue;const item=document.createElement('li'),link=document.createElement('a');link.href=s.url;link.textContent=`[${s.id}] ${s.title}`;item.append(link);list.append(item);}out.append(list);if(data.notice){const note=document.createElement('p');note.className='oc-small';note.textContent=data.notice;out.append(note);}}catch(err){waiting.textContent=err.name==='AbortError'?'The guide took too long. Your lesson sources remain available.':err.message;}finally{button.disabled=false;panel.classList.remove('busy');}
  });
  const output=$('[data-lab-output]'),select=$('[data-lab-select]');
  if(select){const choice=new URLSearchParams(location.search).get('lab');if([...select.options].some(o=>o.value===choice))select.value=choice;const matchWeek=()=>{root.dataset.campusWeek=select.selectedOptions[0].dataset.week;};select.addEventListener('change',matchWeek);matchWeek();}
  async function lab(action){const buttons=[...root.querySelectorAll('[data-lab-start],[data-lab-status],[data-lab-stop]')];buttons.forEach(b=>b.disabled=true);output.textContent=action==='start'?'Starting a clean copy of your target…':'Checking your workspace…';try{const data=await api(action,action==='start'?{lab:select.value}:{});output.replaceChildren();const p=document.createElement('p');p.textContent=data.error|| (data.state==='running'?`Running: ${data.lab}. Lease expires ${new Date(data.expires*1000).toLocaleTimeString()}.`:'Your target is stopped. Choose a lab to start a fresh copy.');output.append(p);if(data.state==='running'&&data.url){const u=new URL(data.url);if(u.protocol==='https:'&&/^p[1-5]\.team[12]\.labs\.test$/.test(u.hostname)&&u.port==='8443'){const a=document.createElement('a');a.href=u.href;a.target='_blank';a.rel='noreferrer';a.className='oc-button';a.textContent='Open my target ↗';output.append(a);const note=document.createElement('p');note.className='oc-small';note.textContent='Allow a few seconds for startup. Use your assigned VPN and trusted course certificate.';output.append(note);}}}catch(err){output.textContent=err.name==='AbortError'?'The operation timed out. Refresh status before trying to start again.':err.message;}finally{buttons.forEach(b=>b.disabled=false);}}
  $('[data-lab-start]')?.addEventListener('click',()=>lab('start'));$('[data-lab-status]')?.addEventListener('click',()=>lab('status'));$('[data-lab-stop]')?.addEventListener('click',()=>lab('stop'));
})();

let token = localStorage.getItem('token') || '';

document.getElementById('login').onclick = async () => {
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const r = await fetch('/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) });
  if (r.ok) {
    const data = await r.json();
    token = data.token;
    localStorage.setItem('token', token);
    document.getElementById('loginStatus').innerText = 'Logged in';
    refresh();
  } else {
    document.getElementById('loginStatus').innerText = 'Failed';
  }
};

document.getElementById('addNL').onclick = async () => {
  const text = document.getElementById('nl').value;
  if (!token) { alert('Login first'); return; }
  const r = await fetch('/tasks/nl', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`}, body: JSON.stringify({ text }) });
  if (r.ok) { document.getElementById('nl').value=''; refresh(); }
};

async function loadView(view, elId) {
  const r = await fetch(`/tasks/?view=${view}`, { headers: { Authorization: `Bearer ${token}` }});
  if (!r.ok) return;
  const data = await r.json();
  const el = document.getElementById(elId);
  el.innerHTML = '';
  for (const t of data) {
    const li = document.createElement('li');
    const due = t.due ? new Date(t.due).toLocaleString() : '';
    li.textContent = `${t.title} ${due ? '('+due+')' : ''}`;
    el.appendChild(li);
  }
}

async function refresh(){
  await loadView('today', 'today');
  await loadView('upcoming', 'upcoming');
  await loadView('overdue', 'overdue');
}

if (token) refresh();


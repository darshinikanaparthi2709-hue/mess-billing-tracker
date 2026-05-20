// ─── STATE ───
let config = {
  messName: 'Sri Karthikeya Deluxe Mess',
  location: 'Somajiguda, Hyderabad — 500082',
  defaultMeal: 'Egg Meals',
  prices: { egg: 120, veg: 120, chicken: 160, mutton: 275 }
};

let companies = [
  { id: 1, name: 'Everest Infra Ventures India Pvt. Ltd.', since: 'Jan 2025' },
  { id: 2, name: 'MediJourn Solutions Pvt. Ltd.', since: 'Mar 2025' },
  { id: 3, name: 'Wadi Surgicals Pvt. Ltd.', since: 'Jun 2024' },
  { id: 4, name: 'Fristor Foods Pvt. Ltd.', since: 'Nov 2024' },
];

let entries = {}; // key: "YYYY-MM-DD_companyId" => {egg,veg,chicken,mutton}
let currentMonth = new Date();

// Today's date
const today = new Date();
const todayKey = today.toISOString().split('T')[0];
let selectedDailyDate = todayKey;

const API_URL = 'http://localhost:8000/api';

// ─── UTILITIES ───
function calcAmount(egg, veg, chicken, mutton) {
  return egg * config.prices.egg + veg * config.prices.veg + chicken * config.prices.chicken + (mutton || 0) * (config.prices.mutton || 0);
}
function entryKey(compId, date) { return `${date || todayKey}_${compId}`; }
function getEntry(compId, date) { return entries[entryKey(compId, date)] || { egg: 0, veg: 0, chicken: 0, mutton: 0 }; }
function setEntry(compId, egg, veg, chicken, mutton, date) {
  entries[entryKey(compId, date)] = { egg: +egg, veg: +veg, chicken: +chicken, mutton: +mutton };
}

// ─── TOAST ───
function toast(msg, icon='✓') {
  const el = document.createElement('div');
  el.className = 'toast';
  el.innerHTML = `<span>${icon}</span> ${msg}`;
  document.getElementById('toast-wrap').appendChild(el);
  setTimeout(() => el.remove(), 3200);
}

// ─── SERVER FETCH ───
async function fetchState() {
  try {
    const res = await fetch(`${API_URL}/data?_t=${Date.now()}`);
    if (!res.ok) throw new Error("Failed to fetch state");
    const data = await res.json();
    config = data.config;
    companies = data.companies;
    entries = data.entries;
    document.querySelector('.sidebar-footer .sync-badge').innerHTML = '<div class="sync-dot"></div> Connected to SQL';
    document.querySelector('.sidebar-footer .sync-badge').style.color = '#38bdf8';
    return true;
  } catch (err) {
    console.error("Server connection failed, falling back to local memory.", err);
    toast("Local Offline Mode: Server not running", "⚠");
    document.querySelector('.sidebar-footer .sync-badge').innerHTML = '<div class="sync-dot" style="background:#ef4444;box-shadow:0 0 12px #ef4444"></div> Offline Mode';
    document.querySelector('.sidebar-footer .sync-badge').style.color = '#ef4444';
    return false;
  }
}

// ─── PAGE ROUTING ───
function showPage(id, navEl) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelectorAll('.mobile-nav-item').forEach(m => m.classList.remove('active'));
  document.getElementById(`page-${id}`).classList.add('active');
  
  // Set active on corresponding desktop sidebar item
  const desktopNavItems = Array.from(document.querySelectorAll('.nav-item'));
  const desktopItem = desktopNavItems.find(item => item.getAttribute('onclick')?.includes(`'${id}'`));
  if (desktopItem) desktopItem.classList.add('active');
  
  // Set active on corresponding mobile bottom nav item
  const mobileNavItems = Array.from(document.querySelectorAll('.mobile-nav-item'));
  const mobileItem = mobileNavItems.find(item => item.getAttribute('onclick')?.includes(`'${id}'`));
  if (mobileItem) mobileItem.classList.add('active');
  
  if (id === 'dashboard') renderDashboard();
  if (id === 'daily') renderDailyEntry();
  if (id === 'monthly') renderMonthly();
  if (id === 'companies') renderCompanies();
  if (id === 'setup') renderSetup();
}

// ─── DASHBOARD ───
function renderDashboard() {
  const days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  document.getElementById('today-date-display').textContent =
    `${days[today.getDay()]}, ${today.getDate()} ${months[today.getMonth()]} ${today.getFullYear()}`;
  document.getElementById('date-badge-display').textContent =
    `${String(today.getDate()).padStart(2,'0')}-${String(today.getMonth()+1).padStart(2,'0')}-${today.getFullYear()}`;
  document.getElementById('default-meal-display').textContent = config.defaultMeal;

  let totalEgg=0, totalVeg=0, totalChicken=0, totalMutton=0;
  companies.forEach(c => {
    const e = getEntry(c.id);
    totalEgg += e.egg; totalVeg += e.veg; totalChicken += e.chicken; totalMutton += (e.mutton || 0);
  });

  animateNum('dash-egg', totalEgg);
  animateNum('dash-veg', totalVeg);
  animateNum('dash-chicken', totalChicken);
  animateNum('dash-mutton', totalMutton);
  animateNum('dash-total-plates', totalEgg + totalVeg + totalChicken + totalMutton);
  document.getElementById('dash-amount').textContent = `₹${calcAmount(totalEgg, totalVeg, totalChicken, totalMutton).toLocaleString('en-IN')}`;

  const tbody = document.getElementById('dashboard-table-body');
  tbody.innerHTML = companies.map(c => {
    const e = getEntry(c.id);
    const total = e.egg + e.veg + e.chicken + (e.mutton || 0);
    const amt = calcAmount(e.egg, e.veg, e.chicken, e.mutton);
    const pill = (v, type) => v > 0
      ? `<span class="pill ${type}">${v}</span>`
      : `<span class="pill empty">—</span>`;
    return `<tr>
      <td class="company-name">${c.name}</td>
      <td>${pill(e.egg,'egg')}</td>
      <td>${pill(e.veg,'veg')}</td>
      <td>${pill(e.chicken,'chicken')}</td>
      <td>${pill(e.mutton || 0,'mutton')}</td>
      <td>${total > 0 ? `<span class="pill total-p">${total}</span>` : '<span class="pill empty">—</span>'}</td>
      <td class="amount-cell">${amt > 0 ? `₹${amt.toLocaleString('en-IN')}` : '<span style="color:var(--text-dim)">₹—</span>'}</td>
    </tr>`;
  }).join('');
}

function animateNum(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  let start = 0;
  const step = Math.ceil(target / 20) || 1;
  const t = setInterval(() => {
    start = Math.min(start + step, target);
    el.textContent = start;
    if (start >= target) clearInterval(t);
  }, 30);
}

// ─── DAILY ENTRY ───
function renderDailyEntry() {
  const dateInput = document.getElementById('daily-entry-date');
  if (dateInput && !dateInput.value) {
    dateInput.value = selectedDailyDate;
  }

  document.getElementById('price-egg-display').textContent = config.prices.egg;
  document.getElementById('price-veg-display').textContent = config.prices.veg;
  document.getElementById('price-chicken-display').textContent = config.prices.chicken;
  document.getElementById('price-mutton-display').textContent = config.prices.mutton || 250;



  const grid = document.getElementById('entry-cards');
  grid.innerHTML = companies.map(c => {
    const e = getEntry(c.id, selectedDailyDate);
    return `
    <div class="entry-card tilt-card" id="ecard-${c.id}">
      <div class="entry-company">${c.name}<span>Client since ${c.since}</span></div>
      <div class="meal-inputs">
        <div class="meal-input-group">
          <div class="meal-input-label egg">🍳 Egg</div>
          <div class="stepper">
            <button class="step-btn" onclick="step(${c.id},'egg',-1)">−</button>
            <input type="number" class="meal-input egg" id="e${c.id}-egg" value="${e.egg}" min="0" oninput="updateCardTotal(${c.id})">
            <button class="step-btn" onclick="step(${c.id},'egg',1)">+</button>
          </div>
        </div>
        <div class="meal-input-group">
          <div class="meal-input-label veg">🥗 Veg</div>
          <div class="stepper">
            <button class="step-btn" onclick="step(${c.id},'veg',-1)">−</button>
            <input type="number" class="meal-input veg" id="e${c.id}-veg" value="${e.veg}" min="0" oninput="updateCardTotal(${c.id})">
            <button class="step-btn" onclick="step(${c.id},'veg',1)">+</button>
          </div>
        </div>
        <div class="meal-input-group">
          <div class="meal-input-label chicken">🍗 Chicken</div>
          <div class="stepper">
            <button class="step-btn" onclick="step(${c.id},'chicken',-1)">−</button>
            <input type="number" class="meal-input chicken" id="e${c.id}-chicken" value="${e.chicken}" min="0" oninput="updateCardTotal(${c.id})">
            <button class="step-btn" onclick="step(${c.id},'chicken',1)">+</button>
          </div>
        </div>
        <div class="meal-input-group">
          <div class="meal-input-label mutton">🐏 Mutton</div>
          <div class="stepper">
            <button class="step-btn" onclick="step(${c.id},'mutton',-1)">−</button>
            <input type="number" class="meal-input mutton" id="e${c.id}-mutton" value="${e.mutton || 0}" min="0" oninput="updateCardTotal(${c.id})">
            <button class="step-btn" onclick="step(${c.id},'mutton',1)">+</button>
          </div>
        </div>
      </div>
      <div class="entry-total">
        <span class="entry-total-label">${selectedDailyDate === todayKey ? "Today's Amount" : "Amount for " + selectedDailyDate}</span>
        <span class="entry-total-value" id="etotal-${c.id}">₹${calcAmount(e.egg,e.veg,e.chicken,e.mutton).toLocaleString('en-IN')}</span>
      </div>
    </div>`;
  }).join('');

  // Attach tilt
  document.querySelectorAll('.tilt-card').forEach(card => {
    card.addEventListener('mousemove', tilt);
    card.addEventListener('mouseleave', resetTilt);
  });
}

function onDateChange() {
  const dateInput = document.getElementById('daily-entry-date');
  if (dateInput && dateInput.value) {
    selectedDailyDate = dateInput.value;
    renderDailyEntry();
  }
}

function prevDay() {
  const dateObj = new Date(selectedDailyDate);
  dateObj.setDate(dateObj.getDate() - 1);
  selectedDailyDate = dateObj.toISOString().split('T')[0];
  document.getElementById('daily-entry-date').value = selectedDailyDate;
  renderDailyEntry();
}

function nextDay() {
  const dateObj = new Date(selectedDailyDate);
  dateObj.setDate(dateObj.getDate() + 1);
  selectedDailyDate = dateObj.toISOString().split('T')[0];
  document.getElementById('daily-entry-date').value = selectedDailyDate;
  renderDailyEntry();
}

function step(compId, type, dir) {
  const el = document.getElementById(`e${compId}-${type}`);
  el.value = Math.max(0, (+el.value) + dir);
  updateCardTotal(compId);
  document.getElementById('pending-badge').style.display = 'inline-flex';
}

function updateCardTotal(compId) {
  const egg = +document.getElementById(`e${compId}-egg`).value || 0;
  const veg = +document.getElementById(`e${compId}-veg`).value || 0;
  const chicken = +document.getElementById(`e${compId}-chicken`).value || 0;
  const mutton = +document.getElementById(`e${compId}-mutton`).value || 0;
  document.getElementById(`etotal-${compId}`).textContent = `₹${calcAmount(egg, veg, chicken, mutton).toLocaleString('en-IN')}`;
  document.getElementById('pending-badge').style.display = 'inline-flex';
}

async function saveAllEntries() {
  const updates = [];
  companies.forEach(c => {
    const egg = +document.getElementById(`e${c.id}-egg`).value || 0;
    const veg = +document.getElementById(`e${c.id}-veg`).value || 0;
    const chicken = +document.getElementById(`e${c.id}-chicken`).value || 0;
    const mutton = +document.getElementById(`e${c.id}-mutton`).value || 0;
    setEntry(c.id, egg, veg, chicken, mutton, selectedDailyDate);
    updates.push({
      date: selectedDailyDate,
      company_id: c.id,
      egg,
      veg,
      chicken,
      mutton
    });
  });

  try {
    const res = await fetch(`${API_URL}/entries`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });
    if (!res.ok) throw new Error("Failed to save entries to server");
    document.getElementById('pending-badge').style.display = 'none';
    toast('All entries saved and written to SQL!', '✓');
  } catch (err) {
    console.error("Failed to sync entries with server:", err);
    toast('Saved locally! Failed to write to SQL.', '⚠');
  }
}

// ─── MONTHLY ───
function renderMonthly() {
  const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  document.getElementById('month-label').textContent = `${months[currentMonth.getMonth()]} ${currentMonth.getFullYear()}`;

  const prefix = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth()+1).padStart(2,'0')}`;
  let totalRev = 0, totalPlates = 0;

  const rows = companies.map(c => {
    let egg=0, veg=0, chicken=0, mutton=0;
    Object.keys(entries).forEach(k => {
      if (k.startsWith(prefix) && k.endsWith(`_${c.id}`)) {
        egg += entries[k].egg || 0;
        veg += entries[k].veg || 0;
        chicken += entries[k].chicken || 0;
        mutton += entries[k].mutton || 0;
      }
    });
    const total = egg + veg + chicken + mutton;
    const amt = calcAmount(egg, veg, chicken, mutton);
    totalRev += amt; totalPlates += total;
    const pill = (v, type) => v > 0 ? `<span class="pill ${type}">${v}</span>` : `<span class="pill empty">—</span>`;
    return `<tr>
      <td class="company-name">${c.name}</td>
      <td>${pill(egg,'egg')}</td>
      <td>${pill(veg,'veg')}</td>
      <td>${pill(chicken,'chicken')}</td>
      <td>${pill(mutton,'mutton')}</td>
      <td>${total > 0 ? `<span class="pill total-p">${total}</span>` : '<span class="pill empty">—</span>'}</td>
      <td class="amount-cell">${amt > 0 ? `₹${amt.toLocaleString('en-IN')}` : '<span style="color:var(--text-dim)">₹—</span>'}</td>
    </tr>`;
  }).join('');

  document.getElementById('monthly-revenue').textContent = `₹${totalRev.toLocaleString('en-IN')}`;
  document.getElementById('monthly-plates').textContent = totalPlates;
  const daysInMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth()+1, 0).getDate();
  document.getElementById('monthly-avg').textContent = `₹${Math.round(totalRev/daysInMonth).toLocaleString('en-IN')}`;
  document.getElementById('monthly-table-body').innerHTML = rows;

  // Render invoice options
  const select = document.getElementById('invoice-company-select');
  if (select) {
    const currentVal = select.value;
    select.innerHTML = companies.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    if (currentVal && companies.find(c => c.id == currentVal)) {
      select.value = currentVal;
    }
    renderInvoice();
  }
}

function prevMonth() {
  currentMonth.setMonth(currentMonth.getMonth() - 1);
  renderMonthly();
}
function nextMonth() {
  currentMonth.setMonth(currentMonth.getMonth() + 1);
  renderMonthly();
}

// ─── COMPANIES ───
function renderCompanies() {
  document.getElementById('companies-grid').innerHTML = companies.map(c => {
    const e = getEntry(c.id);
    const total = e.egg + e.veg + e.chicken;
    const amt = calcAmount(e.egg, e.veg, e.chicken);
    return `
    <div class="company-card">
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div>
          <div class="company-card-name">${c.name}</div>
          <div class="company-card-meta">Client since ${c.since}</div>
        </div>
        <div style="font-size:22px;opacity:.5">🏢</div>
      </div>
      <div class="company-stats">
        <div class="company-stat">
          <div class="company-stat-val" style="color:var(--egg)">${e.egg}</div>
          <div class="company-stat-lbl">Egg</div>
        </div>
        <div class="company-stat">
          <div class="company-stat-val" style="color:var(--veg)">${e.veg}</div>
          <div class="company-stat-lbl">Veg</div>
        </div>
        <div class="company-stat">
          <div class="company-stat-val" style="color:var(--chicken)">${e.chicken}</div>
          <div class="company-stat-lbl">Chicken</div>
        </div>
        <div class="company-stat">
          <div class="company-stat-val" style="color:var(--gold)">₹${amt.toLocaleString('en-IN')}</div>
          <div class="company-stat-lbl">Today</div>
        </div>
      </div>
    </div>`;
  }).join('');
}

// ─── SETUP ───
function renderSetup() {
  document.getElementById('cfg-egg').value = config.prices.egg;
  document.getElementById('cfg-veg').value = config.prices.veg;
  document.getElementById('cfg-chicken').value = config.prices.chicken;
  document.getElementById('cfg-mutton').value = config.prices.mutton || 250;
  document.getElementById('cfg-default-meal').value = config.defaultMeal;
  document.getElementById('cfg-name').value = config.messName;
  document.getElementById('cfg-loc').value = config.location;
}

async function saveSetup() {
  config.prices.egg = +document.getElementById('cfg-egg').value;
  config.prices.veg = +document.getElementById('cfg-veg').value;
  config.prices.chicken = +document.getElementById('cfg-chicken').value;
  config.prices.mutton = +document.getElementById('cfg-mutton').value;
  config.defaultMeal = document.getElementById('cfg-default-meal').value;
  config.messName = document.getElementById('cfg-name').value;
  config.location = document.getElementById('cfg-loc').value;

  try {
    const res = await fetch(`${API_URL}/setup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    if (!res.ok) throw new Error("Failed to save settings to server");
    
    // Update active visual elements
    document.querySelector('.brand h1').innerHTML = config.messName.replace(/\s(pvt|ltd|solutions|ventures|ventures india)/gi, '').split(' ').slice(0,2).join('<br>') + '<br>' + config.messName.split(' ').slice(2).join(' ');
    document.querySelector('.brand p').textContent = config.location;
    
    toast('Settings saved and written to database!', '⚙');
  } catch (err) {
    console.error("Failed to sync settings with server:", err);
    toast('Saved locally! Failed to sync database.', '⚠');
  }
}

async function addCompanyFromSetup() {
  const name = document.getElementById('new-company-name').value.trim();
  if (!name) { toast('Please enter a company name', '⚠'); return; }
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const since = `${months[today.getMonth()]} ${today.getFullYear()}`;

  try {
    const res = await fetch(`${API_URL}/company`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, since })
    });
    if (!res.ok) throw new Error("Failed to add company to server");
    
    const newComp = await res.json();
    companies.push(newComp);
    document.getElementById('new-company-name').value = '';
    toast(`"${name}" added and SQL schema created!`, '🏢');
    renderCompanies();
  } catch (err) {
    console.error("Failed to add company to server:", err);
    // Local fallback
    companies.push({
      id: Date.now(),
      name,
      since
    });
    document.getElementById('new-company-name').value = '';
    toast(`Added locally! Database sync failed.`, '⚠');
  }
}

function showAddCompany() {
  showPage('setup', document.querySelectorAll('.nav-item')[4]);
  setTimeout(() => document.getElementById('new-company-name').focus(), 400);
}

// ─── 3D TILT ───
function tilt(e) {
  const card = this;
  const rect = card.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  const cx = rect.width / 2, cy = rect.height / 2;
  const rx = (y - cy) / cy * -6;
  const ry = (x - cx) / cx * 6;
  card.style.transform = `perspective(1000px) rotateX(${rx}deg) rotateY(${ry}deg) translateY(-4px)`;
}

function resetTilt() {
  this.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateY(0)';
}

// ─── INVOICE GENERATOR ───
function renderInvoice() {
  const select = document.getElementById('invoice-company-select');
  if (!select) return;
  const compId = select.value;
  if (!compId) return;
  const company = companies.find(c => c.id == compId);
  if (!company) return;

  const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  const monthLabel = `${months[currentMonth.getMonth()]} ${currentMonth.getFullYear()}`;
  const prefix = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth()+1).padStart(2,'0')}`;

  // Filter and gather entries for this company in the current month
  const monthlyEntries = [];
  Object.keys(entries).forEach(k => {
    if (k.startsWith(prefix) && k.endsWith(`_${compId}`)) {
      const datePart = k.split('_')[0];
      const dayNum = parseInt(datePart.split('-')[2]);
      const entry = entries[k];
      monthlyEntries.push({ day: dayNum, ...entry });
    }
  });

  // Meal types config
  const mealTypes = [
    { key: 'veg', label: 'VEG MEALS', priceKey: 'veg' },
    { key: 'egg', label: 'EGG MEALS', priceKey: 'egg' },
    { key: 'chicken', label: 'CHICKEN MEALS', priceKey: 'chicken' },
    { key: 'mutton', label: 'MUTTON', priceKey: 'mutton' }
  ];

  let invoiceItems = [];
  let serialNo = 1;

  mealTypes.forEach(m => {
    // Filter entries where this meal type was taken
    const activeEntries = monthlyEntries.filter(e => e[m.key] > 0);
    if (activeEntries.length === 0) return;

    // Group by meal count (persons per day)
    const groups = {};
    activeEntries.forEach(e => {
      const count = e[m.key];
      if (!groups[count]) groups[count] = [];
      groups[count].push(e.day);
    });

    // For each count group, create an invoice item
    Object.keys(groups).sort((a,b) => parseInt(b) - parseInt(a)).forEach(countStr => {
      const count = parseInt(countStr);
      const days = groups[count].sort((a,b) => a-b);
      const daysCount = days.length;
      const totalMeals = count * daysCount;
      const rate = config.prices[m.priceKey] || 0;
      const amount = totalMeals * rate;

      invoiceItems.push({
        sno: serialNo++,
        label: m.label,
        daysList: days.join(','),
        personsPerDay: count,
        daysCount: daysCount,
        totalMeals: totalMeals,
        rate: rate,
        amount: amount
      });
    });
  });

  const totalAmount = invoiceItems.reduce((sum, item) => sum + item.amount, 0);

  const container = document.getElementById('invoice-container');
  if (!container) return;

  if (invoiceItems.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 40px; color: var(--text-dim); border: 1px dashed var(--glass-border); border-radius: 12px;">
        No meal records found for ${company.name} in ${monthLabel}.
      </div>`;
    return;
  }

  // Draw the custom invoice table
  let tableRows = '';
  invoiceItems.forEach(item => {
    tableRows += `
      <tr class="invoice-item-group-header">
        <td rowspan="2" class="invoice-sno">${item.sno}</td>
        <td colspan="6" class="invoice-meal-title">${item.label}</td>
      </tr>
      <tr class="invoice-item-group-details">
        <td class="invoice-desc-days">${item.daysList}</td>
        <td class="invoice-val-center">${item.personsPerDay}</td>
        <td class="invoice-val-center">${item.daysCount}</td>
        <td class="invoice-val-center">${item.totalMeals}</td>
        <td class="invoice-val-center">${item.rate}</td>
        <td class="invoice-val-right">₹${item.amount.toLocaleString('en-IN')}</td>
      </tr>
    `;
  });

  container.innerHTML = `
    <div class="print-invoice-card">
      <div class="invoice-header">
        <div class="invoice-mess-name">${config.messName}</div>
        <div class="invoice-mess-loc">${config.location}</div>
        <div class="invoice-bill-title">${monthLabel.toUpperCase()} MONTH BILL</div>
        <div class="invoice-company-details">
          <strong>BILL TO:</strong> ${company.name}
        </div>
      </div>
      
      <div class="invoice-table-wrap">
        <table class="invoice-table">
          <thead>
            <tr>
              <th style="width: 6%">SNO</th>
              <th style="width: 35%">DESCRIPTION</th>
              <th style="width: 23%">NO. OF PERSONS (Per Day)</th>
              <th style="width: 8%">DAYS</th>
              <th style="width: 10%">TOTAL MEALS</th>
              <th style="width: 8%">RATE</th>
              <th style="width: 10%">AMOUNT</th>
            </tr>
          </thead>
          <tbody>
            ${tableRows}
            <tr class="invoice-total-row">
              <td colspan="6" class="invoice-total-label">TOTAL</td>
              <td class="invoice-total-value">₹${totalAmount.toLocaleString('en-IN')}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function printInvoice() {
  window.print();
}

// ─── INIT ───
(async function init() {
  document.querySelectorAll('.tilt-card').forEach(card => {
    card.addEventListener('mousemove', tilt);
    card.addEventListener('mouseleave', resetTilt);
  });
  
  await fetchState();
  
  // Format Mess Name inside Sidebar
  const words = config.messName.split(' ');
  if (words.length >= 2) {
    document.querySelector('.brand h1').innerHTML = words.slice(0, 2).join(' ') + '<br>' + words.slice(2).join(' ');
  } else {
    document.querySelector('.brand h1').textContent = config.messName;
  }
  document.querySelector('.brand p').textContent = config.location;
  
  renderDashboard();
})();

function dismissIntro() {
  const intro = document.getElementById('intro-screen');
  if (intro) {
    intro.classList.add('fade-out');
  }
}

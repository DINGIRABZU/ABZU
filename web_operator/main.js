async function memoryScan() {
  const query = document.getElementById('memory-query').value;
  const resp = await fetch('/memory/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });
  const data = await resp.json();
  renderMemoryResults(Array.isArray(data) ? data : []);
}

function renderMemoryResults(data) {
  const container = document.getElementById('memory-results');
  container.innerHTML = '';
  if (data.length === 0) {
    container.textContent = 'No results';
    return;
  }
  const table = document.createElement('table');
  table.className = 'retro-table';
  const thead = document.createElement('thead');
  const headerRow = document.createElement('tr');
  const keys = Object.keys(data[0]);
  keys.forEach(key => {
    const th = document.createElement('th');
    th.textContent = key;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);
  const tbody = document.createElement('tbody');
  data.forEach(item => {
    const row = document.createElement('tr');
    keys.forEach(key => {
      const cell = document.createElement('td');
      cell.textContent = item[key];
      row.appendChild(cell);
    });
    tbody.appendChild(row);
  });
  table.appendChild(tbody);
  container.appendChild(table);
}

document.getElementById('memory-scan-btn').addEventListener('click', memoryScan);

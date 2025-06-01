* TRAXORA - Mobile-friendly table transformations
*
* This script transforms tables into card views on mobile devices
* for improved readability and usability.
*/
document.addEventListener('DOMContentLoaded', function() {
const tables = document.querySelectorAll('.mobile-card-view');
const isMobile = window.innerWidth < 768;
function transformTablesToCards() {
tables.forEach(table => {
if (window.innerWidth < 768) {
if (!table.classList.contains('transformed')) {
createCardView(table);
}
} else {
if (table.classList.contains('transformed')) {
restoreTableView(table);
}
}
});
}
function createCardView(table) {
table.setAttribute('data-original-html', table.innerHTML);
const headers = [];
const headerRow = table.querySelector('thead tr');
if (headerRow) {
headerRow.querySelectorAll('th').forEach(th => {
headers.push(th.textContent.trim());
});
}
const cardContainer = document.createElement('div');
cardContainer.className = 'mobile-cards';
const rows = table.querySelectorAll('tbody tr');
rows.forEach(row => {
const card = document.createElement('div');
card.className = 'mobile-card mb-3 p-3 rounded bg-dark';
const cells = row.querySelectorAll('td');
cells.forEach((cell, index) => {
if (index >= headers.length) return;
if (!cell.textContent.trim() && !cell.querySelector('*')) return;
const cardItem = document.createElement('div');
cardItem.className = 'mobile-card-item mb-2 d-flex justify-content-between align-items-start';
const cardHeader = document.createElement('div');
cardHeader.className = 'mobile-card-header text-muted small';
cardHeader.textContent = headers[index];
const cardContent = document.createElement('div');
cardContent.className = 'mobile-card-content ms-auto text-end';
cardContent.innerHTML = cell.innerHTML;
cardItem.appendChild(cardHeader);
cardItem.appendChild(cardContent);
card.appendChild(cardItem);
});
if (row.hasAttribute('data-actions')) {
const actions = document.createElement('div');
actions.className = 'mobile-card-actions d-flex justify-content-end mt-3 pt-2 border-top';
actions.innerHTML = row.getAttribute('data-actions');
card.appendChild(actions);
}
cardContainer.appendChild(card);
});
table.innerHTML = '';
table.appendChild(cardContainer);
table.classList.add('transformed');
}
function restoreTableView(table) {
if (table.hasAttribute('data-original-html')) {
table.innerHTML = table.getAttribute('data-original-html');
table.classList.remove('transformed');
}
}
if (tables.length > 0) {
transformTablesToCards();
window.addEventListener('resize', function() {
transformTablesToCards();
});
}
window.refreshMobileTables = function() {
transformTablesToCards();
};
});
* TRAXORA Report Generator
*
* This script handles the report generator interface, including
* selecting report types, configuring options, and generating
* PDF and CSV reports with preview thumbnails.
*/
document.addEventListener('DOMContentLoaded', function() {
const reportTypeSelect = document.getElementById('report-type');
const reportDescription = document.getElementById('report-description');
const filterOptions = document.getElementById('filter-options');
const groupBySelect = document.getElementById('group-by');
const dateStart = document.getElementById('date-start');
const dateEnd = document.getElementById('date-end');
const previewReportBtn = document.getElementById('preview-report-btn');
const generateReportBtn = document.getElementById('generate-report-btn');
const refreshReportsBtn = document.getElementById('refresh-reports-btn');
const reportPreviewsContainer = document.getElementById('report-previews-container');
const noReportsMessage = document.getElementById('no-reports-message');
const previewModal = new bootstrap.Modal(document.getElementById('report-preview-modal'));
const previewLoading = document.getElementById('preview-loading');
const previewContent = document.getElementById('preview-content');
const previewImage = document.getElementById('preview-image');
const previewError = document.getElementById('preview-error');
const previewErrorMessage = document.getElementById('preview-error-message');
const downloadReportLink = document.getElementById('download-report-link');
const reportDescriptions = {
'daily_driver': 'Daily driver activity report showing late starts, early ends, and not-on-job incidents.',
'pm_allocation': 'Preventive maintenance allocation report showing original and updated values with reconciliation.',
'asset_status': 'Current status of all assets including location, driver, and last update time.',
'maintenance': 'Maintenance schedule and history for equipment with upcoming service dates.',
'job_zone_efficiency': 'Job zone efficiency report showing equipment time in zone vs expected time.',
'attendance_metrics': 'Attendance metrics report showing trends, patterns, and flags.'
};
const reportFilters = {
'daily_driver': [
{ id: 'driver-filter', label: 'Driver', type: 'select', options: [], endpoint: '/api/drivers' },
{ id: 'region-filter', label: 'Region', type: 'select', options: [], endpoint: '/api/regions' },
{ id: 'incident-type-filter', label: 'Incident Type', type: 'checkbox',
options: [
{ value: 'late_start', label: 'Late Start' },
{ value: 'early_end', label: 'Early End' },
{ value: 'not_on_job', label: 'Not On Job' }
]
}
],
'pm_allocation': [
{ id: 'asset-type-filter', label: 'Asset Type', type: 'select', options: [], endpoint: '/api/asset_types' },
{ id: 'location-filter', label: 'Location', type: 'select', options: [], endpoint: '/api/locations' },
{ id: 'difference-threshold', label: 'Difference Threshold (%)', type: 'range', min: 0, max: 100, default: 5 }
],
'asset_status': [
{ id: 'status-filter', label: 'Status', type: 'select',
options: [
{ value: 'all', label: 'All' },
{ value: 'active', label: 'Active' },
{ value: 'maintenance', label: 'In Maintenance' },
{ value: 'inactive', label: 'Inactive' }
]
},
{ id: 'asset-type-filter', label: 'Asset Type', type: 'select', options: [], endpoint: '/api/asset_types' },
{ id: 'location-filter', label: 'Location', type: 'select', options: [], endpoint: '/api/locations' }
],
'maintenance': [
{ id: 'maintenance-status', label: 'Status', type: 'select',
options: [
{ value: 'all', label: 'All' },
{ value: 'scheduled', label: 'Scheduled' },
{ value: 'overdue', label: 'Overdue' },
{ value: 'completed', label: 'Completed' }
]
},
{ id: 'asset-type-filter', label: 'Asset Type', type: 'select', options: [], endpoint: '/api/asset_types' },
{ id: 'priority-filter', label: 'Priority', type: 'checkbox',
options: [
{ value: 'high', label: 'High' },
{ value: 'medium', label: 'Medium' },
{ value: 'low', label: 'Low' }
]
}
],
'job_zone_efficiency': [
{ id: 'job-site-filter', label: 'Job Site', type: 'select', options: [], endpoint: '/api/job_sites' },
{ id: 'efficiency-threshold', label: 'Efficiency Threshold (%)', type: 'range', min: 0, max: 100, default: 75 }
],
'attendance_metrics': [
{ id: 'driver-filter', label: 'Driver', type: 'select', options: [], endpoint: '/api/drivers' },
{ id: 'region-filter', label: 'Region', type: 'select', options: [], endpoint: '/api/regions' },
{ id: 'trend-type', label: 'Trend Type', type: 'radio',
options: [
{ value: 'daily', label: 'Daily' },
{ value: 'weekly', label: 'Weekly' },
{ value: 'monthly', label: 'Monthly' }
]
}
]
};
const groupByOptions = {
'daily_driver': [
{ value: 'driver', label: 'Driver' },
{ value: 'asset', label: 'Asset' },
{ value: 'job_site', label: 'Job Site' },
{ value: 'incident_type', label: 'Incident Type' }
],
'pm_allocation': [
{ value: 'asset_type', label: 'Asset Type' },
{ value: 'region', label: 'Region' },
{ value: 'difference_category', label: 'Difference Category' }
],
'asset_status': [
{ value: 'status', label: 'Status' },
{ value: 'asset_type', label: 'Asset Type' },
{ value: 'region', label: 'Region' }
],
'maintenance': [
{ value: 'status', label: 'Status' },
{ value: 'asset_type', label: 'Asset Type' },
{ value: 'assigned_to', label: 'Assigned To' },
{ value: 'priority', label: 'Priority' }
],
'job_zone_efficiency': [
{ value: 'job_site', label: 'Job Site' },
{ value: 'asset_type', label: 'Asset Type' },
{ value: 'efficiency_category', label: 'Efficiency Category' }
],
'attendance_metrics': [
{ value: 'driver', label: 'Driver' },
{ value: 'job_site', label: 'Job Site' },
{ value: 'region', label: 'Region' },
{ value: 'incident_type', label: 'Incident Type' }
]
};
function setDefaultDates() {
const today = new Date();
const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
dateStart.valueAsDate = firstDay;
dateEnd.valueAsDate = lastDay;
}
function init() {
setDefaultDates();
refreshReportPreviews();
reportTypeSelect.addEventListener('change', handleReportTypeChange);
previewReportBtn.addEventListener('click', previewReport);
generateReportBtn.addEventListener('click', generateReport);
refreshReportsBtn.addEventListener('click', refreshReportPreviews);
previewReportBtn.disabled = true;
generateReportBtn.disabled = true;
}
function handleReportTypeChange() {
const selectedType = reportTypeSelect.value;
if (!selectedType) {
reportDescription.classList.add('d-none');
previewReportBtn.disabled = true;
generateReportBtn.disabled = true;
return;
}
reportDescription.classList.remove('d-none');
reportDescription.querySelector('.description-text').textContent = reportDescriptions[selectedType] || 'No description available.';
previewReportBtn.disabled = false;
generateReportBtn.disabled = false;
updateFilterOptions(selectedType);
updateGroupByOptions(selectedType);
}
function updateFilterOptions(reportType) {
filterOptions.innerHTML = '';
const filters = reportFilters[reportType] || [];
if (filters.length === 0) {
const noFiltersDiv = document.createElement('div');
noFiltersDiv.className = 'alert alert-info';
noFiltersDiv.innerHTML = '<small>No filters available for this report type</small>';
filterOptions.appendChild(noFiltersDiv);
return;
}
filters.forEach(filter => {
const filterDiv = document.createElement('div');
filterDiv.className = 'mb-3';
const filterLabel = document.createElement('label');
filterLabel.className = 'form-label';
filterLabel.textContent = filter.label;
filterDiv.appendChild(filterLabel);
if (filter.type === 'select') {
const select = document.createElement('select');
select.id = filter.id;
select.className = 'form-select';
const defaultOption = document.createElement('option');
defaultOption.value = 'all';
defaultOption.textContent = 'All';
select.appendChild(defaultOption);
if (filter.options && filter.options.length > 0) {
filter.options.forEach(option => {
const optionEl = document.createElement('option');
optionEl.value = option.value;
optionEl.textContent = option.label;
select.appendChild(optionEl);
});
}
if (filter.endpoint) {
loadFilterOptions(filter.endpoint, select);
}
filterDiv.appendChild(select);
} else if (filter.type === 'checkbox' || filter.type === 'radio') {
const optionsDiv = document.createElement('div');
optionsDiv.className = 'mt-2';
filter.options.forEach(option => {
const wrapper = document.createElement('div');
wrapper.className = filter.type === 'checkbox' ? 'form-check' : 'form-check form-check-inline';
const input = document.createElement('input');
input.className = 'form-check-input';
input.type = filter.type;
input.name = filter.id;
input.id = `${filter.id}-${option.value}`;
input.value = option.value;
if (option.checked) input.checked = true;
const label = document.createElement('label');
label.className = 'form-check-label';
label.htmlFor = `${filter.id}-${option.value}`;
label.textContent = option.label;
wrapper.appendChild(input);
wrapper.appendChild(label);
optionsDiv.appendChild(wrapper);
});
filterDiv.appendChild(optionsDiv);
} else if (filter.type === 'range') {
const rangeDiv = document.createElement('div');
rangeDiv.className = 'd-flex align-items-center';
const range = document.createElement('input');
range.type = 'range';
range.className = 'form-range flex-grow-1 me-2';
range.id = filter.id;
range.min = filter.min || 0;
range.max = filter.max || 100;
range.value = filter.default || 50;
const valueDisplay = document.createElement('span');
valueDisplay.className = 'badge bg-primary';
valueDisplay.textContent = range.value;
valueDisplay.id = `${filter.id}-value`;
range.addEventListener('input', () => {
valueDisplay.textContent = range.value;
});
rangeDiv.appendChild(range);
rangeDiv.appendChild(valueDisplay);
filterDiv.appendChild(rangeDiv);
}
filterOptions.appendChild(filterDiv);
});
}
function loadFilterOptions(endpoint, selectElement) {
setTimeout(() => {
const sampleOptions = [
{ value: 'option1', label: 'Option 1' },
{ value: 'option2', label: 'Option 2' },
{ value: 'option3', label: 'Option 3' }
];
sampleOptions.forEach(option => {
const optionEl = document.createElement('option');
optionEl.value = option.value;
optionEl.textContent = option.label;
selectElement.appendChild(optionEl);
});
}, 200);
}
function updateGroupByOptions(reportType) {
groupBySelect.innerHTML = '';
const defaultOption = document.createElement('option');
defaultOption.value = '';
defaultOption.textContent = 'None';
groupBySelect.appendChild(defaultOption);
const options = groupByOptions[reportType] || [];
if (options.length === 0) {
groupBySelect.disabled = true;
return;
}
options.forEach(option => {
const optionEl = document.createElement('option');
optionEl.value = option.value;
optionEl.textContent = option.label;
groupBySelect.appendChild(optionEl);
});
groupBySelect.disabled = false;
}
function previewReport() {
const reportType = reportTypeSelect.value;
if (!reportType) {
showFeedback('Error', 'Please select a report type', 'danger');
return;
}
previewModal.show();
previewLoading.classList.remove('d-none');
previewContent.classList.add('d-none');
previewError.classList.add('d-none');
const reportOptions = getReportOptions();
setTimeout(() => {
const isCsv = document.getElementById('format-csv').checked;
const previewPath = isCsv
? '/static/images/previews/csv_preview.png'
: '/static/images/previews/pdf_preview.png';
const reportPath = isCsv
? `/exports/csv/${reportType}_sample.csv`
: `/exports/pdf/${reportType}_sample.pdf`;
previewImage.src = previewPath;
downloadReportLink.href = reportPath;
downloadReportLink.download = isCsv
? `${reportType}_report.csv`
: `${reportType}_report.pdf`;
previewLoading.classList.add('d-none');
previewContent.classList.remove('d-none');
}, 1000);
}
function generateReport() {
const reportType = reportTypeSelect.value;
if (!reportType) {
showFeedback('Error', 'Please select a report type', 'danger');
return;
}
generateReportBtn.disabled = true;
generateReportBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
const reportOptions = getReportOptions();
const isCsv = document.getElementById('format-csv').checked;
const format = isCsv ? 'csv' : 'pdf';
setTimeout(() => {
const reportId = Math.floor(Math.random() * 1000000);
const reportData = {
id: reportId,
type: reportType,
format: format,
title: getReportTitle(reportType),
timestamp: new Date().toISOString(),
previewUrl: isCsv
? '/static/images/previews/csv_preview.png'
: '/static/images/previews/pdf_preview.png',
downloadUrl: isCsv
? `/exports/csv/${reportType}_${reportId}.csv`
: `/exports/pdf/${reportType}_${reportId}.pdf`
};
addReportPreview(reportData);
generateReportBtn.disabled = false;
generateReportBtn.innerHTML = '<i class="bi bi-file-earmark-arrow-down me-1"></i> Generate Report';
showFeedback('Success', `Report generated successfully! You can download it now.`, 'success');
}, 2000);
}
function getReportOptions() {
const reportType = reportTypeSelect.value;
const startDate = dateStart.value;
const endDate = dateEnd.value;
const groupBy = groupBySelect.value;
const filters = {};
document.querySelectorAll('#filter-options select').forEach(select => {
filters[select.id] = select.value;
});
const checkboxGroups = {};
document.querySelectorAll('#filter-options input[type="checkbox"]').forEach(checkbox => {
const name = checkbox.name;
if (!checkboxGroups[name]) {
checkboxGroups[name] = [];
}
if (checkbox.checked) {
checkboxGroups[name].push(checkbox.value);
}
});
Object.assign(filters, checkboxGroups);
document.querySelectorAll('#filter-options input[type="radio"]:checked').forEach(radio => {
filters[radio.name] = radio.value;
});
document.querySelectorAll('#filter-options input[type="range"]').forEach(range => {
filters[range.id] = range.value;
});
return {
reportType,
startDate,
endDate,
groupBy,
filters
};
}
function getReportTitle(reportType) {
const titles = {
'daily_driver': 'Daily Driver Report',
'pm_allocation': 'PM Allocation Report',
'asset_status': 'Asset Status Report',
'maintenance': 'Maintenance Report',
'job_zone_efficiency': 'Job Zone Efficiency Report',
'attendance_metrics': 'Attendance Metrics Report'
};
return titles[reportType] || 'Report';
}
function refreshReportPreviews() {
reportPreviewsContainer.innerHTML = '';
noReportsMessage.classList.remove('d-none');
setTimeout(() => {
const sampleReports = [
{
id: 123456,
type: 'daily_driver',
format: 'pdf',
title: 'Daily Driver Report',
timestamp: '2025-05-17T14:30:00Z',
previewUrl: '/static/images/previews/pdf_preview.png',
downloadUrl: '/exports/pdf/daily_driver_123456.pdf'
},
{
id: 123457,
type: 'pm_allocation',
format: 'csv',
title: 'PM Allocation Report',
timestamp: '2025-05-16T10:15:00Z',
previewUrl: '/static/images/previews/csv_preview.png',
downloadUrl: '/exports/csv/pm_allocation_123457.csv'
}
];
if (sampleReports.length > 0) {
noReportsMessage.classList.add('d-none');
sampleReports.forEach(report => {
addReportPreview(report);
});
}
}, 500);
}
function addReportPreview(report) {
noReportsMessage.classList.add('d-none');
const cardCol = document.createElement('div');
cardCol.className = 'col-md-6 col-lg-4 col-xl-3 mb-4';
const card = document.createElement('div');
card.className = 'card shadow-sm h-100';
const cardHeader = document.createElement('div');
cardHeader.className = 'card-header d-flex justify-content-between align-items-center';
const title = document.createElement('h6');
title.className = 'mb-0';
title.textContent = report.title;
const formatBadge = document.createElement('span');
formatBadge.className = `badge ${report.format === 'pdf' ? 'bg-danger' : 'bg-success'}`;
formatBadge.textContent = report.format.toUpperCase();
cardHeader.appendChild(title);
cardHeader.appendChild(formatBadge);
const cardBody = document.createElement('div');
cardBody.className = 'card-body text-center';
const previewContainer = document.createElement('div');
previewContainer.className = 'preview-thumbnail mb-3';
previewContainer.style.height = '150px';
previewContainer.style.display = 'flex';
previewContainer.style.alignItems = 'center';
previewContainer.style.justifyContent = 'center';
previewContainer.style.overflow = 'hidden';
const previewImage = document.createElement('img');
previewImage.className = 'img-fluid';
previewImage.src = report.previewUrl;
previewImage.alt = report.title;
previewImage.style.maxHeight = '100%';
previewImage.style.maxWidth = '100%';
previewImage.style.cursor = 'pointer';
previewImage.addEventListener('click', () => {
previewModal.show();
previewLoading.classList.add('d-none');
previewError.classList.add('d-none');
previewContent.classList.remove('d-none');
previewImage.src = report.previewUrl;
downloadReportLink.href = report.downloadUrl;
downloadReportLink.download = `${report.type}_report.${report.format}`;
});
previewContainer.appendChild(previewImage);
cardBody.appendChild(previewContainer);
const timestamp = document.createElement('small');
timestamp.className = 'text-muted d-block mb-3';
const date = new Date(report.timestamp);
timestamp.textContent = date.toLocaleString();
cardBody.appendChild(timestamp);
const cardFooter = document.createElement('div');
cardFooter.className = 'card-footer bg-transparent';
const downloadLink = document.createElement('a');
downloadLink.className = 'btn btn-sm btn-primary d-block';
downloadLink.href = report.downloadUrl;
downloadLink.download = `${report.type}_report.${report.format}`;
downloadLink.innerHTML = '<i class="bi bi-download me-1"></i> Download';
cardFooter.appendChild(downloadLink);
card.appendChild(cardHeader);
card.appendChild(cardBody);
card.appendChild(cardFooter);
cardCol.appendChild(card);
reportPreviewsContainer.prepend(cardCol);
}
function showFeedback(title, message, type) {
if (typeof window.showFeedback === 'function') {
window.showFeedback(title, message, type);
} else {
alert(`${title}: ${message}`);
}
}
init();
});
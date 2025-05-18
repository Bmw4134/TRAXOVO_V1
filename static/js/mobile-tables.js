/**
 * TRAXORA - Mobile-friendly table transformations
 * 
 * This script transforms tables into card views on mobile devices
 * for improved readability and usability.
 */

document.addEventListener('DOMContentLoaded', function() {
  // Detect tables that should be transformed on mobile
  const tables = document.querySelectorAll('.mobile-card-view');
  const isMobile = window.innerWidth < 768;
  
  // Convert selected tables to card view on mobile
  function transformTablesToCards() {
    tables.forEach(table => {
      // Only transform on mobile
      if (window.innerWidth < 768) {
        if (!table.classList.contains('transformed')) {
          createCardView(table);
        }
      } else {
        // If viewport is larger, restore table view
        if (table.classList.contains('transformed')) {
          restoreTableView(table);
        }
      }
    });
  }
  
  // Create card view from a table
  function createCardView(table) {
    // Store original table HTML for restoration later
    table.setAttribute('data-original-html', table.innerHTML);
    
    // Get headers from the table
    const headers = [];
    const headerRow = table.querySelector('thead tr');
    if (headerRow) {
      headerRow.querySelectorAll('th').forEach(th => {
        headers.push(th.textContent.trim());
      });
    }
    
    // Create card container
    const cardContainer = document.createElement('div');
    cardContainer.className = 'mobile-cards';
    
    // Process each row into a card
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
      const card = document.createElement('div');
      card.className = 'mobile-card mb-3 p-3 rounded bg-dark';
      
      // Process each cell with its header
      const cells = row.querySelectorAll('td');
      cells.forEach((cell, index) => {
        // Skip if we don't have a header for this column
        if (index >= headers.length) return;
        
        // Don't create empty entries
        if (!cell.textContent.trim() && !cell.querySelector('*')) return;
        
        const cardItem = document.createElement('div');
        cardItem.className = 'mobile-card-item mb-2 d-flex justify-content-between align-items-start';
        
        // Add header
        const cardHeader = document.createElement('div');
        cardHeader.className = 'mobile-card-header text-muted small';
        cardHeader.textContent = headers[index];
        
        // Add content
        const cardContent = document.createElement('div');
        cardContent.className = 'mobile-card-content ms-auto text-end';
        cardContent.innerHTML = cell.innerHTML;
        
        // Add to card
        cardItem.appendChild(cardHeader);
        cardItem.appendChild(cardContent);
        card.appendChild(cardItem);
      });
      
      // Add actions from data attributes if available
      if (row.hasAttribute('data-actions')) {
        const actions = document.createElement('div');
        actions.className = 'mobile-card-actions d-flex justify-content-end mt-3 pt-2 border-top';
        actions.innerHTML = row.getAttribute('data-actions');
        card.appendChild(actions);
      }
      
      // Add the card to the container
      cardContainer.appendChild(card);
    });
    
    // Replace table contents with cards
    table.innerHTML = '';
    table.appendChild(cardContainer);
    table.classList.add('transformed');
  }
  
  // Restore original table view
  function restoreTableView(table) {
    if (table.hasAttribute('data-original-html')) {
      table.innerHTML = table.getAttribute('data-original-html');
      table.classList.remove('transformed');
    }
  }
  
  // Initialize and handle resize events
  if (tables.length > 0) {
    transformTablesToCards();
    
    // Handle resize events
    window.addEventListener('resize', function() {
      transformTablesToCards();
    });
  }
  
  // Public method to manually trigger transformation
  window.refreshMobileTables = function() {
    transformTablesToCards();
  };
});
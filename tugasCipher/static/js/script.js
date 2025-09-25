/**
 * CRYPTOSYSTEM - JavaScript Functions
 * Handles input type toggling and tab persistence (session-based)
 */

/**
 * Toggle between text input and file upload modes
 * @param {string} cipherName - Name of the cipher (e.g., 'shift', 'sub', etc.)
 * @param {string} inputType - Type of input ('text' or 'file')
 */
function toggleInputType(cipherName, inputType) {
  const textArea = document.getElementById(cipherName + '_text_area');
  const fileArea = document.getElementById(cipherName + '_file_area');
  const formatArea = document.getElementById(cipherName + '_format_area');
  
  if (inputType === 'text') {
    // Show text input, hide file input
    textArea.style.display = 'block';
    fileArea.style.display = 'none';
    
    // Show format options for text mode
    if (formatArea) {
      formatArea.style.display = 'block';
    }
  } else {
    // Show file input, hide text input
    textArea.style.display = 'none';
    fileArea.style.display = 'block';
    
    // Hide format options for file mode
    if (formatArea) {
      formatArea.style.display = 'none';
    }
  }
}

/**
 * Initialize all cipher tabs to text mode when page loads
 */
function initializeTabs() {
  const ciphers = ['shift', 'sub', 'affine', 'vig', 'hill', 'perm', 'playfair', 'otp'];
  ciphers.forEach(cipher => {
    toggleInputType(cipher, 'text');
  });
}

/**
 * Save the currently active tab to sessionStorage
 * @param {Event} e - Tab show event
 */
function saveActiveTab(e) {
  const activeTabHref = e.target.getAttribute('href');
  sessionStorage.setItem('activeTab', activeTabHref);
}

/**
 * Restore the last active tab from sessionStorage
 */
function restoreActiveTab() {
  let activeTab = sessionStorage.getItem('activeTab');
  
  // Default ke shift tab kalau belum ada tersimpan
  if (!activeTab) {
    activeTab = '#shift-tab'; 
  }

  const tabTrigger = document.querySelector(`#cipherTabs a[href="${activeTab}"]`);
  
  if (tabTrigger && window.bootstrap) {
    new bootstrap.Tab(tabTrigger).show();
  }
}

/**
 * Set up event listeners for tab persistence
 */
function setupTabPersistence() {
  const tabElements = document.querySelectorAll('#cipherTabs a');
  tabElements.forEach(tab => {
    tab.addEventListener('shown.bs.tab', saveActiveTab);
  });
}

/**
 * Initialize the application when DOM is fully loaded
 */
document.addEventListener('DOMContentLoaded', function() {
  // Initialize all tabs to text mode
  initializeTabs();
  
  // Set up tab persistence
  setupTabPersistence();
});

/**
 * Restore active tab when page loads
 */
window.addEventListener('load', function() {
  restoreActiveTab();
});

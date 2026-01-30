/**
 * D2D Stats Widget
 * 
 * Usage:
 *   <script src="https://raw.githubusercontent.com/Soulfra/d2d/main/widget.js"></script>
 *   <d2d-stats></d2d-stats>
 * 
 * Or with options:
 *   <d2d-stats theme="light" show="mrr,customers"></d2d-stats>
 */

(function() {
  const STATS_URL = 'https://raw.githubusercontent.com/Soulfra/d2d/main/stats.json';
  
  class D2DStats extends HTMLElement {
    connectedCallback() {
      const theme = this.getAttribute('theme') || 'dark';
      const show = (this.getAttribute('show') || 'mrr,customers').split(',');
      
      const bg = theme === 'dark' ? '#0a0a0a' : '#fff';
      const fg = theme === 'dark' ? '#0f0' : '#000';
      const border = theme === 'dark' ? '#222' : '#ddd';
      const muted = theme === 'dark' ? '#666' : '#888';
      
      this.innerHTML = `
        <div style="
          display: inline-flex;
          gap: 20px;
          background: ${bg};
          border: 1px solid ${border};
          padding: 12px 20px;
          font-family: monospace;
          font-size: 14px;
        ">
          ${show.includes('mrr') ? `
            <div style="text-align: center;">
              <div id="d2d-w-mrr" style="font-size: 20px; color: ${fg};">...</div>
              <div style="font-size: 10px; color: ${muted};">MRR</div>
            </div>
          ` : ''}
          ${show.includes('customers') ? `
            <div style="text-align: center;">
              <div id="d2d-w-customers" style="font-size: 20px; color: ${fg};">...</div>
              <div style="font-size: 10px; color: ${muted};">MEMBERS</div>
            </div>
          ` : ''}
        </div>
      `;
      
      this.loadStats();
    }
    
    loadStats() {
      fetch(STATS_URL)
        .then(r => r.json())
        .then(data => {
          const mrr = this.querySelector('#d2d-w-mrr');
          const customers = this.querySelector('#d2d-w-customers');
          if (mrr) mrr.textContent = '$' + data.mrr_dollars;
          if (customers) customers.textContent = data.customers;
        })
        .catch(() => {
          const mrr = this.querySelector('#d2d-w-mrr');
          if (mrr) mrr.textContent = '$?';
        });
    }
  }
  
  customElements.define('d2d-stats', D2DStats);
})();

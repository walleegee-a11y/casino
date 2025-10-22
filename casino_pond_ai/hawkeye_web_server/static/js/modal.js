/**
 * modal.js - Modal dialog functions for run details
 *
 * This file contains functions for showing and closing modal dialogs
 * that display detailed information about runs:
 * - showRunDetailsModal: Opens modal with run details
 * - closeRunDetailsModal: Closes the modal
 * - Escape key listener for closing modals
 * - Click-outside listener for closing modals
 */

/**
 * Show run details in a modal dialog
 * @param {number} index - Index of the run in allRunVersions array
 */
function showRunDetailsModal(index) {
    const run = allRunVersions[index];
    const modal = document.getElementById('runDetailsModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    // Set modal title
    modalTitle.textContent = `Run Details: ${run.run_version}`;

    // Build modal content
    let html = `
        <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                <div><strong>Run Version:</strong> ${run.run_version}</div>
                <div><strong>User:</strong> ${run.user_name}</div>
                <div><strong>Block:</strong> ${run.block_name}</div>
                <div><strong>DK Ver/Tag:</strong> ${run.dk_ver_tag}</div>
                <div><strong>Base Dir:</strong> ${run.base_dir}</div>
                <div><strong>Top Name:</strong> ${run.top_name}</div>
            </div>
        </div>
    `;

    if (Object.keys(run.keywords).length === 0) {
        html += '<p style="color: #7f8c8d; font-style: italic; text-align: center; padding: 40px;">No keywords found for this run.</p>';
    } else {
        html += '<h3 style="margin-bottom: 15px; color: #2c3e50;">Tasks & Keywords</h3>';

        Object.entries(run.keywords).forEach(([taskName, keywords]) => {
            const taskKeywordCount = keywords.length;

            html += `
                <div style="margin-bottom: 25px; border: 1px solid #ddd; border-radius: 6px; overflow: hidden;">
                    <div style="background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%); color: white; padding: 12px 15px; font-weight: bold; display: flex; justify-content: space-between; align-items: center;">
                        <span>${taskName}</span>
                        <span style="background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 12px; font-size: 12px;">${taskKeywordCount} keywords</span>
                    </div>
                    <div style="padding: 15px;">
                        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px;">
            `;

            keywords.forEach(keyword => {
                const value = keyword.keyword_value;
                const unit = keyword.keyword_unit;
                const displayValue = unit ? `${value} ${unit}` : value;

                html += `
                    <div style="background: white; border: 1px solid #e0e6ed; border-radius: 4px; padding: 10px; transition: box-shadow 0.2s;" onmouseover="this.style.boxShadow='0 2px 8px rgba(0,0,0,0.1)'" onmouseout="this.style.boxShadow='none'">
                        <div style="font-weight: 600; color: #2c3e50; margin-bottom: 6px; font-size: 13px;">${keyword.keyword_name}</div>
                        <div style="color: #e74c3c; font-weight: bold; font-size: 15px;">${displayValue}</div>
                    </div>
                `;
            });

            html += `
                        </div>
                    </div>
                </div>
            `;
        });
    }

    modalBody.innerHTML = html;
    modal.style.display = 'block';

    // Close modal when clicking outside of it
    window.onclick = function(event) {
        if (event.target == modal) {
            closeRunDetailsModal();
        }
    };
}

/**
 * Close the run details modal
 */
function closeRunDetailsModal() {
    document.getElementById('runDetailsModal').style.display = 'none';
}

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeRunDetailsModal();
    }
});

/**
 * Project Selection functionality for Hawkeye Web Server
 */

function selectProject(projectName) {
    console.log('Selecting project:', projectName);

    fetch('/api/select-project', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ project: projectName })
    })
    .then(response => {
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        if (data.success) {
            window.location.href = '/';
        } else {
            alert('Error selecting project: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
        alert('Error selecting project: ' + error.message + '\n\nCheck browser console for details.');
    });
}

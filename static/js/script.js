// Inside static/js/script.js
document.addEventListener('DOMContentLoaded', function () {
    console.log("Patient script.js loaded"); // Check if script loads

    // Ensure authentication check is happening (add console logs inside if needed)
    checkAuthenticationAndRole('patient');

    const headawayBtn = document.getElementById('headaway-btn');
    const reactledBtn = document.getElementById('reactled-btn'); // Assuming this maps to arduino
    const gazeaidBtn = document.getElementById('gazeaid-btn');   // Assuming this maps to eyetracking

    if (headawayBtn) {
        headawayBtn.addEventListener('click', () => {
            console.log("HeadAway button clicked"); // Check if listener fires
            runScriptOnServer("headaway.py");
        });
    } else {
        console.error("HeadAway button not found");
    }

    if (reactledBtn) {
        reactledBtn.addEventListener('click', () => {
            console.log("ReactLED button clicked"); // Check if listener fires
            runScriptOnServer("arduino_control.py"); // Map to correct script
        });
    } else {
        console.error("ReactLED button not found");
    }

     if (gazeaidBtn) {
        gazeaidBtn.addEventListener('click', () => {
            console.log("GazeAid button clicked"); // Check if listener fires
            runScriptOnServer("eyetracking.py"); // Map to correct script
        });
    } else {
        console.error("GazeAid button not found");
    }


    // ... (rest of your script.js, including runScriptOnServer, checkAuthenticationAndRole, logout etc.)
});

async function runScriptOnServer(scriptName) {
    console.log(`Attempting to run script: ${scriptName}`); // Check script name being sent
    try {
        const response = await fetch('/api/run-script', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // Cookies should be sent automatically if CORS is set up correctly with credentials
            },
            body: JSON.stringify({ script: scriptName })
        });

        // Log the raw response status
        console.log(`Response status for ${scriptName}: ${response.status}`);

        const result = await response.json();
        console.log(`Response body for ${scriptName}:`, result); // Log the response body

        if (response.ok && result.success) {
            alert(`${scriptName} ${result.already_running ? 'is already running' : 'started successfully'} (PID: ${result.pid || 'N/A'}).`);
        } else {
            alert(`Error starting ${scriptName}: ${result.error || `Server responded with status ${response.status}`}`);
        }
    } catch (error) {
        console.error(`Network or JSON parsing error running ${scriptName}:`, error);
        alert(`Failed to communicate with the server to run ${scriptName}. Check console.`);
    }
}

// --- Make sure checkAuthenticationAndRole and logout functions are also present ---
// (Include the versions from the previous answer)
async function checkAuthenticationAndRole(requiredRole = null) {
    // ... (function as provided before)
}
// Add logout button listener if you have one on this page
const logoutBtn = document.getElementById('logout-btn');
if(logoutBtn) {
   // ... (logout listener as provided before)
}
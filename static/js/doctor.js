document.addEventListener('DOMContentLoaded', function () {
    // --- DOM Elements ---
    const doctorNameDisplay = document.getElementById('doctor-name-display');
    const logoutBtn = document.getElementById('logout-btn');
    const patientSearchInput = document.getElementById('patient-search-input');
    const patientListUl = document.getElementById('patient-list-ul');
    const loadingPatientsLi = document.getElementById('loading-patients');
    const noPatientSelectedDiv = document.getElementById('no-patient-selected');
    const patientInfoContentDiv = document.getElementById('patient-info-content');

    // Patient details fields
    const detailsPatientNameH2 = document.getElementById('details-patient-name');
    const detailsInfoName = document.getElementById('details-info-name');
    const detailsInfoEmail = document.getElementById('details-info-email');
    const detailsInfoAge = document.getElementById('details-info-age');
    const detailsInfoGender = document.getElementById('details-info-gender');
    const detailsMedicalHistory = document.getElementById('details-medical-history');
    const detailsSessionListTbody = document.getElementById('details-session-list');
    const startSessionBtn = document.getElementById('start-session-btn');

    // --- State ---
    let allPatientsData = [];
    let selectedPatientEmail = null;

    // --- Initialization ---
    checkAuthenticationAndRole('doctor');
    fetchAndDisplayPatients();

    // --- Event Listeners ---
    logoutBtn?.addEventListener('click', logout);
    patientSearchInput?.addEventListener('input', handleSearch);
    startSessionBtn?.addEventListener('click', startPatientSession);

    // --- Auth Check ---
    async function checkAuthenticationAndRole(requiredRole = null) {
        try {
            const res = await fetch('/api/check-auth');
            if (!res.ok) return redirectToLanding();
            const data = await res.json();
            if (!data.authenticated || (requiredRole && data.role !== requiredRole)) {
                return redirectToLanding();
            }
            if (doctorNameDisplay && data.name) {
                doctorNameDisplay.textContent = `Welcome, Dr. ${data.name}`;
            }
        } catch (err) {
            console.error('Auth error:', err);
            redirectToLanding();
        }
    }

    function redirectToLanding() {
        window.location.href = '/';
    }

    // --- Fetch Patients ---
    async function fetchAndDisplayPatients() {
        try {
            const res = await fetch('/api/doctor/patients');
            const data = await res.json();
            if (res.ok && data.success && Array.isArray(data.patients)) {
                allPatientsData = data.patients;
                populatePatientList(allPatientsData);
                loadingPatientsLi?.remove();
            } else {
                showError("Error loading patients.");
            }
        } catch (err) {
            console.error('Fetch error:', err);
            showError("Error loading patients.");
        }
    }

    function showError(message) {
        if (loadingPatientsLi) loadingPatientsLi.textContent = message;
        patientListUl.innerHTML = `<li>${message}</li>`;
    }

    // --- Populate List ---
    function populatePatientList(patients) {
        patientListUl.innerHTML = '';
        if (!patients.length) {
            const li = document.createElement('li');
            li.textContent = 'No patients found.';
            li.classList.add('no-patients');
            patientListUl.appendChild(li);
            return;
        }

        patients.forEach(patient => {
            const li = document.createElement('li');
            li.textContent = patient.name;
            li.dataset.email = patient.email;
            if (patient.email === selectedPatientEmail) li.classList.add('active');
            li.addEventListener('click', () => selectPatient(patient.email));
            patientListUl.appendChild(li);
        });
    }

    // --- Select Patient ---
    function selectPatient(email) {
        selectedPatientEmail = email;
        populatePatientList(filterPatients(patientSearchInput.value));
        const patient = allPatientsData.find(p => p.email === email);
        if (patient) {
            displayPatientDetails(patient);
        } else {
            console.error("Patient not found:", email);
            hidePatientDetails();
        }
    }

    // --- Display Patient Details ---
    function displayPatientDetails(patient) {
        noPatientSelectedDiv.classList.remove('active');
        patientInfoContentDiv.classList.add('active');

        detailsPatientNameH2.textContent = patient.name || 'N/A';
        detailsInfoName.textContent = patient.name || 'N/A';
        detailsInfoEmail.textContent = patient.email || 'N/A';
        detailsInfoAge.textContent = patient.age || 'N/A';
        detailsInfoGender.textContent = patient.gender || 'N/A';
        detailsMedicalHistory.textContent = patient.medicalHistory || 'No history available.';

        detailsSessionListTbody.innerHTML = '';
        if (Array.isArray(patient.sessions) && patient.sessions.length > 0) {
            patient.sessions.forEach(session => {
                const row = detailsSessionListTbody.insertRow();
                row.insertCell().textContent = session.date || 'N/A';
                row.insertCell().textContent = session.duration || 'N/A';
                row.insertCell().textContent = session.notes || 'N/A';
            });
        } else {
            detailsSessionListTbody.innerHTML = '<tr><td colspan="3">No session records.</td></tr>';
        }
    }

    // --- Hide Patient Details ---
    function hidePatientDetails() {
        selectedPatientEmail = null;
        noPatientSelectedDiv.classList.add('active');
        patientInfoContentDiv.classList.remove('active');
        populatePatientList(filterPatients(patientSearchInput.value));
    }

    // --- Handle Search ---
    function handleSearch() {
        const filtered = filterPatients(patientSearchInput.value);
        populatePatientList(filtered);
        if (selectedPatientEmail && !filtered.some(p => p.email === selectedPatientEmail)) {
            hidePatientDetails();
        }
    }

    function filterPatients(term) {
        const search = term.toLowerCase().trim();
        return !search ? allPatientsData : allPatientsData.filter(p =>
            p.name.toLowerCase().includes(search) || p.email.toLowerCase().includes(search)
        );
    }

    // --- Start Session ---
    function startPatientSession() {
        if (!selectedPatientEmail) {
            alert("Please select a patient first.");
            return;
        }
        const patient = allPatientsData.find(p => p.email === selectedPatientEmail);
        if (patient) {
            window.location.href = `/home?patient_email=${encodeURIComponent(patient.email)}&patient_name=${encodeURIComponent(patient.name)}`;
        } else {
            alert("Patient not found. Please re-select.");
        }
    }

    // --- Logout ---
    async function logout() {
        try {
            const res = await fetch('/api/logout', { method: 'POST' });
            const data = await res.json();
            if (res.ok && data.success) {
                window.location.href = '/';
            } else {
                alert('Logout failed: ' + (data.error || 'Unknown reason'));
            }
        } catch (err) {
            console.error('Logout error:', err);
            alert('An error occurred during logout.');
        }
    }
});

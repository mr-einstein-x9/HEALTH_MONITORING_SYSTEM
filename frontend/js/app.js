const API_BASE = "http://localhost:8000";

// Check Auth
function checkAuth() {
    const token = localStorage.getItem("token");
    if (!token && !window.location.pathname.includes("login.html") && !window.location.pathname.includes("signup.html")) {
        window.location.href = "login.html";
    }
}

// Set Authorization Header
function getAuthHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + localStorage.getItem("token")
    };
}

// Logout
function logout() {
    localStorage.removeItem("token");
    window.location.href = "login.html";
}

// Login
async function login(e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);

        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem("token", data.access_token);
            window.location.href = "dashboard.html";
        } else {
            alert("Login failed. Please check your credentials.");
        }
    } catch (error) {
        console.error("Error logging in:", error);
        alert("An error occurred. Make sure backend is running.");
    }
}

// Signup
async function signup(e) {
    e.preventDefault();
    const name = document.getElementById('name').value;
    const age = document.getElementById('age').value;
    const gender = document.getElementById('gender').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, age: parseInt(age), gender, email, password })
        });

        if (response.ok) {
            alert("Signup successful! Please login.");
            window.location.href = "login.html";
        } else {
            alert("Signup failed.");
        }
    } catch (error) {
        console.error("Error signing up:", error);
    }
}

// Load Dashboard
async function loadDashboard() {
    try {
        const [dashRes, alertRes, histRes] = await Promise.all([
            fetch(`${API_BASE}/dashboard`, { headers: getAuthHeaders() }).catch(() => ({ok: false})),
            fetch(`${API_BASE}/alerts`, { headers: getAuthHeaders() }).catch(() => ({ok: false})),
            fetch(`${API_BASE}/health-data?limit=7`, { headers: getAuthHeaders() }).catch(() => ({ok: false}))
        ]);

        if (dashRes.ok) {
            const data = await dashRes.json();
            document.getElementById('health-score').innerText = data.health_score || "N/A";
            document.getElementById('heart-rate').innerText = data.latest_heart_rate ? data.latest_heart_rate + " bpm" : "N/A";
            document.getElementById('steps').innerText = data.latest_steps || "N/A";
            document.getElementById('sleep').innerText = data.latest_sleep ? data.latest_sleep + " hrs" : "N/A";
        }

        if (alertRes.ok) {
            const alerts = await alertRes.json();
            if (alerts && alerts.length > 0) {
                const alertsContainer = document.getElementById('alerts-container');
                const alertsList = document.getElementById('alerts-list');
                alertsContainer.style.display = 'block';
                alerts.forEach(alert => {
                    const li = document.createElement('li');
                    li.innerText = alert.message || alert;
                    alertsList.appendChild(li);
                });
            }
        }

        if (histRes.ok) {
            const history = await histRes.json();
            renderCharts(history);
        }

    } catch (error) {
        console.error("Error loading dashboard:", error);
    }
}

// Render Charts
function renderCharts(data) {
    if (!data || data.length === 0) return;
    
    // Reverse to show chronological order
    const reversedData = [...data].reverse();
    const labels = reversedData.map(item => new Date(item.date).toLocaleDateString() || `Day ${item.id}`);
    const hrData = reversedData.map(item => item.heart_rate);
    const sleepData = reversedData.map(item => item.sleep_hours);

    const hrCtx = document.getElementById('hrChart')?.getContext('2d');
    if (hrCtx) {
        new Chart(hrCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Heart Rate (bpm)',
                    data: hrData,
                    borderColor: 'rgb(255, 99, 132)',
                    tension: 0.1
                }]
            }
        });
    }

    const sleepCtx = document.getElementById('sleepChart')?.getContext('2d');
    if (sleepCtx) {
        new Chart(sleepCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Sleep (hours)',
                    data: sleepData,
                    backgroundColor: 'rgb(54, 162, 235)'
                }]
            }
        });
    }
}

// Add Health Data
async function addHealthData(e) {
    e.preventDefault();
    const heart_rate = document.getElementById('heart_rate').value;
    const steps = document.getElementById('steps').value;
    const sleep_hours = document.getElementById('sleep_hours').value;
    const calories = document.getElementById('calories').value;

    try {
        const response = await fetch(`${API_BASE}/health-data`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                heart_rate: parseInt(heart_rate),
                steps: parseInt(steps),
                sleep_hours: parseFloat(sleep_hours),
                calories: parseInt(calories),
                date: new Date().toISOString()
            })
        });

        if (response.ok) {
            alert("Data added successfully!");
            window.location.href = "dashboard.html";
        } else {
            alert("Failed to add data.");
        }
    } catch (error) {
        console.error("Error adding data:", error);
    }
}

// Load History
async function loadHistory() {
    const filter = document.getElementById('history-filter')?.value || 30;
    try {
        const response = await fetch(`${API_BASE}/health-data?days=${filter}`, {
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            const tbody = document.getElementById('history-body');
            tbody.innerHTML = "";

            data.forEach(item => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${new Date(item.date).toLocaleDateString()}</td>
                    <td>${item.heart_rate} bpm</td>
                    <td>${item.steps}</td>
                    <td>${item.sleep_hours} hrs</td>
                    <td>${item.calories} kcal</td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (error) {
        console.error("Error loading history:", error);
    }
}

// Load Profile
async function loadProfile() {
    try {
        const response = await fetch(`${API_BASE}/profile`, {
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            document.getElementById('name').value = data.name || "";
            document.getElementById('email').value = data.email || "";
            document.getElementById('age').value = data.age || "";
            document.getElementById('gender').value = data.gender || "";
        }
    } catch (error) {
        console.error("Error loading profile:", error);
    }
}

// Update Profile
async function updateProfile(e) {
    e.preventDefault();
    const name = document.getElementById('name').value;
    const age = document.getElementById('age').value;
    const gender = document.getElementById('gender').value;

    try {
        const response = await fetch(`${API_BASE}/profile`, {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify({ name, age: parseInt(age), gender })
        });

        if (response.ok) {
            alert("Profile updated successfully!");
        } else {
            alert("Failed to update profile.");
        }
    } catch (error) {
        console.error("Error updating profile:", error);
    }
}

// Init
document.addEventListener("DOMContentLoaded", () => {
    checkAuth();

    const path = window.location.pathname;

    if (path.includes("login.html")) {
        document.getElementById("login-form")?.addEventListener("submit", login);
    } else if (path.includes("signup.html")) {
        document.getElementById("signup-form")?.addEventListener("submit", signup);
    } else if (path.includes("dashboard.html")) {
        loadDashboard();
    } else if (path.includes("add-data.html")) {
        document.getElementById("add-data-form")?.addEventListener("submit", addHealthData);
    } else if (path.includes("history.html")) {
        loadHistory();
        document.getElementById("history-filter")?.addEventListener("change", loadHistory);
    } else if (path.includes("profile.html")) {
        loadProfile();
        document.getElementById("profile-form")?.addEventListener("submit", updateProfile);
    }
});

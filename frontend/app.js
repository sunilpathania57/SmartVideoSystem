// ============================================================
// LOAD ALL CAMERAS
// ============================================================

async function loadCameras() {

    try {

        const response = await fetch("/cameras");

        if (!response.ok) {
            throw new Error("Failed to load cameras");
        }

        const cameras = await response.json();

        const cameraList = document.getElementById("cameraList");

        cameraList.innerHTML = "";


        // No cameras
        if (cameras.length === 0) {

            cameraList.innerHTML = "<p>No cameras found.</p>";

            return;
        }


        // Display each camera
        cameras.forEach(camera => {

            const cameraDiv = document.createElement("div");

            cameraDiv.className = "camera";


            cameraDiv.innerHTML = `
                <div>
                    <strong>${camera.name}</strong>
                    <p>IP: ${camera.ip_address}</p>
                </div>

                <div>

                    <span class="${camera.status}">
                        ${camera.status.toUpperCase()}
                    </span>

                    <button onclick="editCamera(${camera.id})">
                        Edit
                    </button>

                    <button onclick="deleteCamera(${camera.id})">
                        Delete
                    </button>

                </div>
            `;


            cameraList.appendChild(cameraDiv);

        });

    }
    catch (error) {

        console.error(error);

        document.getElementById("cameraList").innerHTML =
            "<p>Unable to load cameras.</p>";
    }
}



// ============================================================
// ADD CAMERA
// ============================================================

document
    .getElementById("cameraForm")
    .addEventListener("submit", async function(event) {

        event.preventDefault();


        const camera = {

            name: document.getElementById("name").value,

            ip_address:
                document.getElementById("ip_address").value,

            status:
                document.getElementById("status").value
        };


        try {

            const response = await fetch("/cameras", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(camera)

            });


            if (!response.ok) {

                throw new Error("Failed to add camera");

            }


            // Clear form
            document.getElementById("cameraForm").reset();


            // Reload camera list
            loadCameras();

        }
        catch (error) {

            console.error(error);

            alert("Failed to add camera.");

        }

    });



// ============================================================
// EDIT CAMERA
// ============================================================

async function editCamera(cameraId) {

    try {

        // Get current camera information

        const response = await fetch(
            `/cameras/${cameraId}`
        );


        if (!response.ok) {

            throw new Error("Camera not found");

        }


        const camera = await response.json();


        // Ask user for new values

        const newName = prompt(
            "Enter camera name:",
            camera.name
        );


        if (newName === null) {
            return;
        }


        const newIP = prompt(
            "Enter IP address:",
            camera.ip_address
        );


        if (newIP === null) {
            return;
        }


        const newStatus = prompt(
            "Enter status (online/offline):",
            camera.status
        );


        if (newStatus === null) {
            return;
        }


        // Updated camera object

        const updatedCamera = {

            name: newName,

            ip_address: newIP,

            status: newStatus

        };


        // Send PUT request

        const updateResponse = await fetch(
            `/cameras/${cameraId}`,
            {

                method: "PUT",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(updatedCamera)

            }
        );


        if (!updateResponse.ok) {

            throw new Error("Update failed");

        }


        // Reload cameras

        loadCameras();

    }
    catch (error) {

        console.error(error);

        alert("Failed to update camera.");

    }

}



// ============================================================
// DELETE CAMERA
// ============================================================

async function deleteCamera(cameraId) {

    const confirmDelete = confirm(
        "Are you sure you want to delete this camera?"
    );


    if (!confirmDelete) {
        return;
    }


    try {

        const response = await fetch(
            `/cameras/${cameraId}`,
            {
                method: "DELETE"
            }
        );


        if (!response.ok) {

            throw new Error("Delete failed");

        }


        // Reload camera list

        loadCameras();

    }
    catch (error) {

        console.error(error);

        alert("Failed to delete camera.");

    }

}



// ============================================================
// LOAD CAMERAS WHEN PAGE OPENS
// ============================================================

loadCameras();
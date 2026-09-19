// ============================================================
// SMART VIDEO MANAGEMENT SYSTEM
// FRONTEND JAVASCRIPT
// ============================================================


// ============================================================
// WHEN PAGE IS READY
// ============================================================

document.addEventListener("DOMContentLoaded", () => {

    console.log("Smart Video System JavaScript started.");

    setupCameraForm();

    loadCameras();

});


// ============================================================
// LOAD ALL CAMERAS
// ============================================================

async function loadCameras() {

    const cameraList =
        document.getElementById("cameraList");


    if (!cameraList) {

        console.error(
            "cameraList element not found."
        );

        return;

    }


    cameraList.innerHTML =
        "<p>Loading cameras...</p>";


    try {

        console.log(
            "Requesting GET /cameras..."
        );


        const response =
            await fetch(
                "/cameras",
                {
                    method: "GET",
                    cache: "no-store"
                }
            );


        console.log(
            "Camera API status:",
            response.status
        );


        if (!response.ok) {

            throw new Error(
                `Camera API returned ${response.status}`
            );

        }


        const cameras =
            await response.json();


        console.log(
            "Cameras received:",
            cameras
        );


        cameraList.innerHTML = "";


        // ----------------------------------------------------
        // NO CAMERAS
        // ----------------------------------------------------

        if (
            !Array.isArray(cameras) ||
            cameras.length === 0
        ) {

            cameraList.innerHTML =
                "<p>No cameras found.</p>";

            return;

        }


        // ----------------------------------------------------
        // CREATE CAMERA CARDS
        // ----------------------------------------------------

        cameras.forEach(
            camera => {

                createCameraCard(
                    camera,
                    cameraList
                );

            }
        );

    }


    catch (error) {

        console.error(
            "Error loading cameras:",
            error
        );


        cameraList.innerHTML = `

            <p style="color:red;">
                Unable to load cameras.
            </p>

            <p>
                Error:
                ${escapeHtml(error.message)}
            </p>

        `;

    }

}


// ============================================================
// CREATE CAMERA CARD
// ============================================================

function createCameraCard(
    camera,
    cameraList
) {

    const cameraDiv =
        document.createElement("div");


    cameraDiv.className =
        "camera-card";


    // --------------------------------------------------------
    // CAMERA STATUS
    // --------------------------------------------------------

    const status =
        camera.status || "offline";


    // --------------------------------------------------------
    // CAMERA TYPE
    // --------------------------------------------------------

    const cameraType =
        camera.camera_type || "IP";


    // --------------------------------------------------------
    // DEVICE INDEX
    // --------------------------------------------------------

    const deviceIndex =
        (
            camera.device_index !== null &&
            camera.device_index !== undefined
        )
            ? camera.device_index
            : "-";


    // --------------------------------------------------------
    // CHECK VIDEO SOURCE
    // --------------------------------------------------------

    let hasVideoSource = false;


    if (
        cameraType.toUpperCase() === "USB"
        &&
        camera.device_index !== null
        &&
        camera.device_index !== undefined
    ) {

        hasVideoSource = true;

    }


    if (
        cameraType.toUpperCase() === "IP"
        &&
        camera.rtsp_url
    ) {

        hasVideoSource = true;

    }


    // --------------------------------------------------------
    // CREATE CARD
    // --------------------------------------------------------

    cameraDiv.innerHTML = `

        <div class="camera-card-header">

            <h3>
                ${escapeHtml(
                    camera.name || "Unnamed Camera"
                )}
            </h3>

            <span
                class="status-badge ${escapeHtml(status)}"
            >

                ${escapeHtml(
                    status
                ).toUpperCase()}

            </span>

        </div>


        <div class="camera-card-body">

            <p>
                <strong>Camera ID:</strong>
                ${camera.id}
            </p>


            <p>
                <strong>IP:</strong>
                ${escapeHtml(
                    camera.ip_address || "-"
                )}
            </p>


            <p>
                <strong>Type:</strong>
                ${escapeHtml(cameraType)}
            </p>


            <p>
                <strong>Location:</strong>
                ${escapeHtml(
                    camera.location || "-"
                )}
            </p>


            <p>
                <strong>Device Index:</strong>
                ${deviceIndex}
            </p>

        </div>


        <div class="camera-card-actions">

            <button
                class="live-button"
            >
                View Live
            </button>


            <button
                class="edit-button"
            >
                Edit
            </button>


            <button
                class="delete-button"
            >
                Delete
            </button>

        </div>

    `;


    // --------------------------------------------------------
    // VIEW LIVE BUTTON
    // --------------------------------------------------------

    const liveButton =
        cameraDiv.querySelector(
            ".live-button"
        );


    if (hasVideoSource) {

        liveButton.addEventListener(
            "click",
            () => {

                viewLiveCamera(
                    camera.id,
                    camera.name
                );

            }
        );

    }

    else {

        liveButton.disabled = true;

        liveButton.textContent =
            "No Video Source";

    }


    // --------------------------------------------------------
    // EDIT BUTTON
    // --------------------------------------------------------

    const editButton =
        cameraDiv.querySelector(
            ".edit-button"
        );


    editButton.addEventListener(
        "click",
        () => {

            editCamera(
                camera.id
            );

        }
    );


    // --------------------------------------------------------
    // DELETE BUTTON
    // --------------------------------------------------------

    const deleteButton =
        cameraDiv.querySelector(
            ".delete-button"
        );


    deleteButton.addEventListener(
        "click",
        () => {

            deleteCamera(
                camera.id
            );

        }
    );


    // --------------------------------------------------------
    // ADD CARD TO PAGE
    // --------------------------------------------------------

    cameraList.appendChild(
        cameraDiv
    );

}


// ============================================================
// VIEW LIVE CAMERA
// ============================================================

function viewLiveCamera(
    cameraId,
    cameraName
) {

    const liveVideo =
        document.getElementById(
            "liveVideo"
        );


    const videoMessage =
        document.getElementById(
            "videoMessage"
        );


    const liveCameraTitle =
        document.getElementById(
            "liveCameraTitle"
        );


    if (!liveVideo) {

        alert(
            "Live video element not found."
        );

        return;

    }


    // --------------------------------------------------------
    // CHANGE TITLE
    // --------------------------------------------------------

    if (liveCameraTitle) {

        liveCameraTitle.textContent =
            `Live Camera View — ${cameraName}`;

    }


    // --------------------------------------------------------
    // SET CAMERA STREAM
    // --------------------------------------------------------

    liveVideo.src =
        `/video-feed/${cameraId}`;


    // --------------------------------------------------------
    // SHOW VIDEO
    // --------------------------------------------------------

    liveVideo.style.display =
        "block";


    // --------------------------------------------------------
    // HIDE MESSAGE
    // --------------------------------------------------------

    if (videoMessage) {

        videoMessage.style.display =
            "none";

    }


    // --------------------------------------------------------
    // SCROLL TO VIDEO
    // --------------------------------------------------------

    const videoContainer =
        document.querySelector(
            ".video-container"
        );


    if (videoContainer) {

        videoContainer.scrollIntoView({

            behavior: "smooth",

            block: "center"

        });

    }


    console.log(
        "Viewing camera:",
        cameraId,
        cameraName
    );

}


// ============================================================
// STOP LIVE CAMERA
// ============================================================

function stopLiveCamera() {

    const liveVideo =
        document.getElementById(
            "liveVideo"
        );


    const videoMessage =
        document.getElementById(
            "videoMessage"
        );


    const liveCameraTitle =
        document.getElementById(
            "liveCameraTitle"
        );


    if (liveVideo) {

        liveVideo.src = "";

        liveVideo.style.display =
            "none";

    }


    if (videoMessage) {

        videoMessage.style.display =
            "block";

    }


    if (liveCameraTitle) {

        liveCameraTitle.textContent =
            "Live Camera View";

    }

}


// ============================================================
// SETUP ADD CAMERA FORM
// ============================================================

function setupCameraForm() {

    const form =
        document.getElementById(
            "cameraForm"
        );


    if (!form) {

        console.error(
            "cameraForm element not found."
        );

        return;

    }


    form.addEventListener(
        "submit",
        async event => {

            event.preventDefault();


            // ------------------------------------------------
            // DEVICE INDEX
            // ------------------------------------------------

            const deviceIndexElement =
                document.getElementById(
                    "device_index"
                );


            const deviceIndexValue =
                deviceIndexElement
                    ? deviceIndexElement.value
                    : "";


            let deviceIndex = null;


            if (
                deviceIndexValue !== ""
            ) {

                deviceIndex =
                    Number(
                        deviceIndexValue
                    );


                if (
                    !Number.isInteger(
                        deviceIndex
                    )
                    ||
                    deviceIndex < 0
                ) {

                    alert(
                        "Device Index must be 0 or greater."
                    );

                    return;

                }

            }


            // ------------------------------------------------
            // CAMERA DATA
            // ------------------------------------------------

            const camera = {

                name:
                    getInputValue("name"),


                ip_address:
                    getInputValue(
                        "ip_address"
                    ),


                camera_type:
                    getInputValue(
                        "camera_type"
                    ),


                location:
                    getInputValue(
                        "location"
                    ),


                username:
                    getInputValue(
                        "username"
                    ),


                rtsp_url:
                    getInputValue(
                        "rtsp_url"
                    ),


                status:
                    getInputValue(
                        "status"
                    ),


                device_index:
                    deviceIndex

            };


            // ------------------------------------------------
            // VALIDATION
            // ------------------------------------------------

            if (
                camera.name === "" ||
                camera.ip_address === ""
            ) {

                alert(
                    "Camera name and IP address are required."
                );

                return;

            }


            // ------------------------------------------------
            // SEND POST
            // ------------------------------------------------

            try {

                console.log(
                    "Adding camera:",
                    camera
                );


                const response =
                    await fetch(
                        "/cameras",
                        {

                            method: "POST",

                            headers: {

                                "Content-Type":
                                    "application/json"

                            },

                            body:
                                JSON.stringify(
                                    camera
                                )

                        }
                    );


                if (!response.ok) {

                    const errorText =
                        await response.text();


                    console.error(
                        "Add camera failed:",
                        errorText
                    );


                    throw new Error(
                        `Server returned ${response.status}`
                    );

                }


                const newCamera =
                    await response.json();


                console.log(
                    "Camera added:",
                    newCamera
                );


                // ------------------------------------------------
                // RESET FORM
                // ------------------------------------------------

                form.reset();


                // Restore device index
                if (deviceIndexElement) {

                    deviceIndexElement.value =
                        "0";

                }


                // ------------------------------------------------
                // RELOAD LIST
                // ------------------------------------------------

                await loadCameras();


                alert(
                    "Camera added successfully!"
                );

            }


            catch (error) {

                console.error(
                    "Add camera error:",
                    error
                );


                alert(
                    "Failed to add camera: " +
                    error.message
                );

            }

        }
    );

}


// ============================================================
// EDIT CAMERA
// ============================================================

async function editCamera(
    cameraId
) {

    try {

        const response =
            await fetch(
                `/cameras/${cameraId}`
            );


        if (!response.ok) {

            throw new Error(
                "Camera not found"
            );

        }


        const camera =
            await response.json();


        const newName =
            prompt(
                "Camera name:",
                camera.name || ""
            );


        if (newName === null) {
            return;
        }


        const newIP =
            prompt(
                "IP address:",
                camera.ip_address || ""
            );


        if (newIP === null) {
            return;
        }


        const newType =
            prompt(
                "Camera type (IP / USB / NORMAL):",
                camera.camera_type || "IP"
            );


        if (newType === null) {
            return;
        }


        const newLocation =
            prompt(
                "Location:",
                camera.location || ""
            );


        if (newLocation === null) {
            return;
        }


        const newUsername =
            prompt(
                "Username:",
                camera.username || ""
            );


        if (newUsername === null) {
            return;
        }


        const newRtsp =
            prompt(
                "RTSP URL:",
                camera.rtsp_url || ""
            );


        if (newRtsp === null) {
            return;
        }


        const newStatus =
            prompt(
                "Status (online/offline):",
                camera.status || "offline"
            );


        if (newStatus === null) {
            return;
        }


        const newDeviceIndex =
            prompt(
                "Device Index (0 for laptop webcam):",
                camera.device_index ?? 0
            );


        if (newDeviceIndex === null) {
            return;
        }


        let deviceIndex = null;


        if (
            newDeviceIndex.trim() !== ""
        ) {

            deviceIndex =
                Number(
                    newDeviceIndex
                );


            if (
                !Number.isInteger(
                    deviceIndex
                )
                ||
                deviceIndex < 0
            ) {

                alert(
                    "Device Index must be 0 or greater."
                );

                return;

            }

        }


        const updatedCamera = {

            name:
                newName.trim(),

            ip_address:
                newIP.trim(),

            camera_type:
                newType
                    .trim()
                    .toUpperCase(),

            location:
                newLocation.trim(),

            username:
                newUsername.trim(),

            rtsp_url:
                newRtsp.trim(),

            status:
                newStatus
                    .trim()
                    .toLowerCase(),

            device_index:
                deviceIndex

        };


        const updateResponse =
            await fetch(
                `/cameras/${cameraId}`,
                {

                    method: "PUT",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify(
                            updatedCamera
                        )

                }
            );


        if (!updateResponse.ok) {

            throw new Error(
                "Update failed"
            );

        }


        await loadCameras();


        alert(
            "Camera updated successfully!"
        );

    }


    catch (error) {

        console.error(
            "Edit camera error:",
            error
        );


        alert(
            "Failed to update camera."
        );

    }

}


// ============================================================
// DELETE CAMERA
// ============================================================

async function deleteCamera(
    cameraId
) {

    const confirmed =
        confirm(
            "Are you sure you want to delete this camera?"
        );


    if (!confirmed) {
        return;
    }


    try {

        const response =
            await fetch(
                `/cameras/${cameraId}`,
                {
                    method: "DELETE"
                }
            );


        if (!response.ok) {

            throw new Error(
                "Delete failed"
            );

        }


        stopLiveCamera();


        await loadCameras();


        alert(
            "Camera deleted successfully!"
        );

    }


    catch (error) {

        console.error(
            "Delete camera error:",
            error
        );


        alert(
            "Failed to delete camera."
        );

    }

}


// ============================================================
// GET INPUT VALUE
// ============================================================

function getInputValue(
    elementId
) {

    const element =
        document.getElementById(
            elementId
        );


    if (!element) {

        console.warn(
            `Element not found: ${elementId}`
        );

        return "";

    }


    return element.value.trim();

}


// ============================================================
// ESCAPE HTML
// ============================================================

function escapeHtml(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }


    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );

}
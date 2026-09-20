// ============================================================
// SMART VIDEO MANAGEMENT SYSTEM
// FRONTEND JAVASCRIPT
// ============================================================


// ============================================================
// RECORDING STATE
// ============================================================

const recordingCameras = new Set();

// 4 x 4 CCTV monitoring wall = 16 camera positions.
const DASHBOARD_CAMERA_SLOTS = 16;


// ============================================================
// PAGE READY
// ============================================================

document.addEventListener("DOMContentLoaded", () => {

    console.log("Smart Video System started.");

    setupCameraForm();

    loadCameras();

    loadRecordings();

});


// ============================================================
// LOAD ALL CAMERAS
// ============================================================

async function loadCameras() {

    const cameraList =
        document.getElementById("cameraList");


    if (!cameraList) {

        console.error("cameraList not found.");

        return;
    }


    cameraList.innerHTML =
        "<p>Loading cameras...</p>";


    try {

        const response =
            await fetch(
                "/cameras",
                {
                    cache: "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                `Camera API returned ${response.status}`
            );

        }


        const cameras =
            await response.json();


        cameraList.innerHTML = "";


        if (!Array.isArray(cameras) || cameras.length === 0) {

            cameraList.innerHTML =
                "<p>No cameras found.</p>";

            return;
        }


        cameras.forEach(camera => {

            createCameraCard(
                camera,
                cameraList
            );

        });

        // Keep a 4x4 dashboard visible while testing.
        // Empty positions are visual placeholders only and are NOT
        // added to the database as fake cameras.
        addEmptyCameraSlots(
            cameras.length,
            DASHBOARD_CAMERA_SLOTS,
            cameraList
        );

    }


    catch (error) {

        console.error(
            "Camera loading error:",
            error
        );


        cameraList.innerHTML = `

            <p style="color:red;">
                Unable to load cameras.
            </p>

            <p>
                ${escapeHtml(error.message)}
            </p>

        `;

    }

}


// ============================================================
// EMPTY CAMERA GRID SLOTS
// ============================================================

function addEmptyCameraSlots(cameraCount, totalSlots, cameraList) {

    if (!cameraList || cameraCount >= totalSlots) {
        return;
    }

    for (
        let slot = cameraCount + 1;
        slot <= totalSlots;
        slot++
    ) {

        const emptyCard =
            document.createElement("div");

        emptyCard.className =
            "camera-card empty-camera-card";

        emptyCard.innerHTML = `

            <div class="camera-card-header">
                <h3>Camera Slot ${slot}</h3>
                <span class="status-badge offline">EMPTY</span>
            </div>

            <div class="camera-card-body">
                <p>
                    <strong>Status:</strong>
                    No camera assigned
                </p>
                <p>
                    Connect an additional USB or IP camera
                    later and add it from the form above.
                </p>
            </div>

            <div class="camera-card-actions">
                <button type="button" disabled>
                    No Camera
                </button>
            </div>

        `;

        cameraList.appendChild(emptyCard);
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


    const cameraType =
        String(
            camera.camera_type || "IP"
        ).toUpperCase();


    const status =
        String(
            camera.status || "offline"
        ).toLowerCase();


    const deviceIndex =
        camera.device_index !== null &&
        camera.device_index !== undefined
            ? camera.device_index
            : "-";


    // --------------------------------------------------------
    // CHECK VIDEO SOURCE
    // --------------------------------------------------------

    const hasUsbSource =
        cameraType === "USB" &&
        camera.device_index !== null &&
        camera.device_index !== undefined;


    const hasRtspSource =
        cameraType === "IP" &&
        camera.rtsp_url;


    const hasVideoSource =
        hasUsbSource ||
        hasRtspSource;


    // --------------------------------------------------------
    // RECORDING STATE
    // --------------------------------------------------------

    const isRecording =
        recordingCameras.has(
            camera.id
        );


    // --------------------------------------------------------
    // CAMERA CARD
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


        <div class="camera-live-preview">

            ${
                hasVideoSource
                    ? `
                        <img
                            class="camera-live-image"
                            id="camera-live-${camera.id}"
                            alt="${escapeHtml(camera.name || "Camera")}"
                            style="display:none;"
                        >

                        <div
                            class="camera-no-signal"
                            id="camera-no-signal-${camera.id}"
                        >
                            <div class="no-signal-icon">⚫</div>
                            <strong>LIVE PREVIEW</strong>
                            <span>Click "Live Tile" to start</span>
                        </div>
                      `
                    : `
                        <div class="camera-no-signal">
                            <div class="no-signal-icon">⚫</div>
                            <strong>NO SIGNAL</strong>
                            <span>No video source</span>
                        </div>
                      `
            }

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


            <p>
                <strong>Recording:</strong>

                <span
                    class="recording-status"
                    style="
                        font-weight:bold;
                        color:${isRecording ? "red" : "inherit"};
                    "
                >

                    ${
                        isRecording
                            ? "🔴 RECORDING"
                            : "Not Recording"
                    }

                </span>

            </p>

        </div>


        <div class="camera-card-actions">

            ${
                hasVideoSource
                    ? `
                        <button
                            type="button"
                            class="live-button"
                        >
                            View Live
                        </button>

                        <button
                            type="button"
                            class="grid-live-button"
                        >
                            ▶ Live Tile
                        </button>

                        <button
                            type="button"
                            class="test-camera-button"
                        >
                            Test Camera
                        </button>
                      `
                    : `
                        <button
                            type="button"
                            disabled
                        >
                            No Video Source
                        </button>
                      `
            }


            ${
                hasVideoSource && !isRecording
                    ? `
                        <button
                            type="button"
                            class="record-button"
                        >
                            🔴 Start Recording
                        </button>
                      `
                    : ""
            }


            ${
                hasVideoSource && isRecording
                    ? `
                        <button
                            type="button"
                            class="stop-record-button"
                        >
                            ⏹ Stop Recording
                        </button>
                      `
                    : ""
            }


            <button
                type="button"
                class="edit-button"
            >
                Edit
            </button>


            <button
                type="button"
                class="delete-button"
            >
                Delete
            </button>

        </div>

    `;


    // ========================================================
    // VIEW LIVE
    // ========================================================

    const liveButton =
        cameraDiv.querySelector(
            ".live-button"
        );


    if (liveButton) {

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


    // ========================================================
    // LIVE TILE
    // ========================================================

    const gridLiveButton =
        cameraDiv.querySelector(
            ".grid-live-button"
        );


    if (gridLiveButton) {

        gridLiveButton.dataset.tileActive = "false";

        gridLiveButton.addEventListener(
            "click",
            () => {

                if (
                    gridLiveButton.dataset.tileActive === "true"
                ) {

                    stopCameraTile(
                        camera.id,
                        gridLiveButton
                    );

                }
                else {

                    startCameraTile(
                        camera.id,
                        gridLiveButton
                    );

                }

            }
        );

    }


    // ========================================================
    // TEST CAMERA
    // ========================================================

    const testButton =
        cameraDiv.querySelector(
            ".test-camera-button"
        );


    if (testButton) {

        testButton.addEventListener(
            "click",
            () => {

                testCamera(
                    camera.id,
                    testButton
                );

            }
        );

    }


    // ========================================================
    // START RECORDING
    // ========================================================

    const recordButton =
        cameraDiv.querySelector(
            ".record-button"
        );


    if (recordButton) {

        recordButton.addEventListener(
            "click",
            () => {

                startRecording(
                    camera.id
                );

            }
        );

    }


    // ========================================================
    // STOP RECORDING
    // ========================================================

    const stopButton =
        cameraDiv.querySelector(
            ".stop-record-button"
        );


    if (stopButton) {

        stopButton.addEventListener(
            "click",
            () => {

                stopRecording(
                    camera.id
                );

            }
        );

    }


    // ========================================================
    // EDIT
    // ========================================================

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


    // ========================================================
    // DELETE
    // ========================================================

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


    cameraList.appendChild(
        cameraDiv
    );

}


// ============================================================
// TEST CAMERA
// ============================================================

async function testCamera(cameraId, buttonElement) {

    if (buttonElement) {
        buttonElement.disabled = true;
        buttonElement.textContent = "Testing...";
    }

    try {

        console.log(
            "Testing camera:",
            cameraId
        );


        const response =
            await fetch(
                `/cameras/${cameraId}/test`,
                {
                    method: "POST",
                    cache: "no-store"
                }
            );


        const responseText =
            await response.text();


        let result = {};

        try {
            result = responseText
                ? JSON.parse(responseText)
                : {};
        }
        catch {
            result = {
                detail: responseText
            };
        }


        if (!response.ok) {

            throw new Error(
                result.detail ||
                result.message ||
                `Server returned ${response.status}`
            );

        }


        console.log(
            "Camera test result:",
            result
        );


        if (result.success) {

            let message =
                "Camera is working.\n\n" +
                `Status: ${result.status || "online"}`;

            if (result.resolution) {
                message +=
                    `\nResolution: ${result.resolution}`;
            }

            if (result.camera_type) {
                message +=
                    `\nType: ${result.camera_type}`;
            }

            alert(message);

        }
        else {

            alert(
                result.message ||
                "Camera test failed."
            );

        }


        // The backend updates the camera status.
        await loadCameras();

    }
    catch (error) {

        console.error(
            "Camera test error:",
            error
        );


        alert(
            "Camera test failed.\n\n" +
            error.message
        );

        // Refresh so the displayed status remains
        // synchronized with the database.
        await loadCameras();

    }
    finally {

        if (buttonElement) {
            buttonElement.disabled = false;
            buttonElement.textContent = "Test Camera";
        }

    }

}


// ============================================================
// START CAMERA TILE
// ============================================================

function startCameraTile(
    cameraId,
    buttonElement
) {

    // Stop the large live preview first.
    // This helps avoid opening two capture sessions
    // on the same USB webcam.
    stopLiveCamera();


    const image =
        document.getElementById(
            `camera-live-${cameraId}`
        );

    const noSignal =
        document.getElementById(
            `camera-no-signal-${cameraId}`
        );


    if (!image) {

        alert(
            "Camera preview element not found."
        );

        return;

    }


    image.src =
        `/video-feed/${cameraId}?tile=${Date.now()}`;

    image.style.display =
        "block";


    if (noSignal) {

        noSignal.style.display =
            "none";

    }


    if (buttonElement) {

        buttonElement.textContent =
            "■ Stop Tile";

        buttonElement.dataset.tileActive = "true";

    }

}


// ============================================================
// STOP CAMERA TILE
// ============================================================

function stopCameraTile(
    cameraId,
    buttonElement
) {

    const image =
        document.getElementById(
            `camera-live-${cameraId}`
        );

    const noSignal =
        document.getElementById(
            `camera-no-signal-${cameraId}`
        );


    if (image) {

        image.src = "";

        image.style.display =
            "none";

    }


    if (noSignal) {

        noSignal.style.display =
            "flex";

    }


    if (buttonElement) {

        buttonElement.textContent =
            "▶ Live Tile";

        buttonElement.dataset.tileActive = "false";

    }

}


// ============================================================
// START RECORDING
// ============================================================

async function startRecording(cameraId) {

    // Stop preview first because the webcam
    // may not support two simultaneous capture sessions.
    stopLiveCamera();


    try {

        console.log(
            "Starting recording:",
            cameraId
        );


        const response =
            await fetch(
                `/record/start/${cameraId}`,
                {
                    method: "POST"
                }
            );


        const responseText =
            await response.text();


        if (!response.ok) {

            throw new Error(
                responseText
            );

        }


        const result =
            JSON.parse(responseText);


        console.log(
            "Recording started:",
            result
        );


        // Mark camera as recording
        recordingCameras.add(
            Number(cameraId)
        );


        // Immediately redraw buttons
        await loadCameras();


        alert(
            "Recording started successfully."
        );

    }


    catch (error) {

        console.error(
            "Start recording error:",
            error
        );


        alert(
            "Could not start recording.\n\n" +
            error.message
        );

    }

}


// ============================================================
// STOP RECORDING
// ============================================================

async function stopRecording(cameraId) {

    try {

        console.log(
            "Stopping recording:",
            cameraId
        );


        const response =
            await fetch(
                `/record/stop/${cameraId}`,
                {
                    method: "POST"
                }
            );


        const responseText =
            await response.text();


        if (!response.ok) {

            throw new Error(
                responseText
            );

        }


        const result =
            JSON.parse(responseText);


        console.log(
            "Recording stopped:",
            result
        );


        // Remove recording state
        recordingCameras.delete(
            Number(cameraId)
        );


        // Refresh camera buttons
        await loadCameras();


        // Refresh recording history
        await loadRecordings();


        alert(
            "Recording stopped successfully.\n\n" +
            `Duration: ${result.duration_seconds} seconds`
        );

    }


    catch (error) {

        console.error(
            "Stop recording error:",
            error
        );


        alert(
            "Could not stop recording.\n\n" +
            error.message
        );

    }

}


// ============================================================
// LOAD RECORDINGS
// ============================================================

async function loadRecordings() {

    const recordingList =
        document.getElementById(
            "recordingList"
        );


    if (!recordingList) {

        return;

    }


    try {

        const response =
            await fetch(
                "/recordings",
                {
                    cache: "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                "Failed to load recordings"
            );

        }


        const recordings =
            await response.json();


        recordingList.innerHTML = "";


        if (
            !Array.isArray(recordings) ||
            recordings.length === 0
        ) {

            recordingList.innerHTML =
                "<p>No recordings found.</p>";

            return;

        }


        recordings.forEach(
            recording => {

                const item =
                    document.createElement(
                        "div"
                    );


                item.className =
                    "recording-item";


                item.innerHTML = `

                    <div>

                        <strong>
                            Recording #${recording.id}
                        </strong>

                        <p>
                            Camera ID:
                            ${recording.camera_id}
                        </p>

                        <p>
                            File:
                            ${escapeHtml(
                                recording.filename
                            )}
                        </p>

                        <p>
                            Start:
                            ${escapeHtml(
                                recording.start_time || "-"
                            )}
                        </p>

                        <p>
                            End:
                            ${escapeHtml(
                                recording.end_time || "-"
                            )}
                        </p>

                        <p>
                            Duration:
                            ${
                                recording.duration_seconds ?? 0
                            }
                            seconds
                        </p>

                        <p>
                            Status:
                            ${escapeHtml(
                                recording.status || "-"
                            )}
                        </p>

                    </div>


                    <div class="recording-actions">

    <button
        type="button"
        class="play-recording-button"
        data-recording-id="${recording.id}"
        data-recording-name="${escapeHtml(
            recording.filename
        )}"
    >
        ▶ Play
    </button>

    <a
        href="/recordings/${recording.id}/download"
        class="download-recording-button"
    >
        ⬇ Download
    </a>

</div>

                `;


                recordingList.appendChild(
                    item
                );
                const playButton =
    item.querySelector(
        ".play-recording-button"
    );


if (playButton) {

    playButton.addEventListener(
        "click",
        () => {

            playRecording(
                recording.id,
                recording.filename
            );

        }
    );

}

            }
        );

    }


    catch (error) {

        console.error(
            "Recording history error:",
            error
        );


        recordingList.innerHTML =
            "<p>Unable to load recordings.</p>";

    }

}


// ============================================================
// PLAY RECORDING IN NEW WINDOW
// ============================================================

function playRecording(
    recordingId,
    filename
) {

    // Open the recording directly in a new browser tab/window.
    // The frontend page will stay unchanged.
    const videoUrl =
        `/recordings/${recordingId}/video`;

    const newWindow =
        window.open(
            videoUrl,
            "_blank",
            "noopener,noreferrer"
        );

    if (!newWindow) {

        alert(
            "The recording window was blocked by your browser. Please allow pop-ups for this site."
        );

    }

}


// ============================================================
// VIEW LIVE CAMERA
// ============================================================

function viewLiveCamera(
    cameraId,
    cameraName
) {

    // Stop any card-level tile preview first.
    stopAllCameraTiles();


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

        return;

    }


    if (liveCameraTitle) {

        liveCameraTitle.textContent =
            `Live Camera View — ${cameraName}`;

    }


    liveVideo.src =
        `/video-feed/${cameraId}`;


    liveVideo.style.display =
        "block";


    if (videoMessage) {

        videoMessage.style.display =
            "none";

    }


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

}


// ============================================================
// STOP ALL CAMERA TILES
// ============================================================

function stopAllCameraTiles() {

    const tileImages =
        document.querySelectorAll(
            ".camera-live-image"
        );

    tileImages.forEach(image => {

        image.src = "";

        image.style.display =
            "none";

    });


    const noSignalElements =
        document.querySelectorAll(
            ".camera-no-signal"
        );

    noSignalElements.forEach(element => {

        element.style.display =
            "flex";

    });


    const tileButtons =
        document.querySelectorAll(
            ".grid-live-button"
        );

    tileButtons.forEach(button => {

        button.textContent =
            "▶ Live Tile";

        button.dataset.tileActive =
            "false";

    });

}


// ============================================================
// STOP LIVE CAMERA
// ============================================================

function stopLiveCamera() {

    // Stop any card-level tile preview.
    stopAllCameraTiles();


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
// ADD CAMERA FORM
// ============================================================

function setupCameraForm() {

    const form =
        document.getElementById(
            "cameraForm"
        );


    if (!form) {

        return;

    }


    form.addEventListener(
        "submit",
        async event => {

            event.preventDefault();


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

            }


            const camera = {

                name:
                    getInputValue(
                        "name"
                    ),

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


            try {

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

                    throw new Error(
                        `Server returned ${response.status}`
                    );

                }


                form.reset();


                if (deviceIndexElement) {

                    deviceIndexElement.value =
                        "0";

                }


                await loadCameras();


                alert(
                    "Camera added successfully."
                );

            }


            catch (error) {

                console.error(
                    "Add camera error:",
                    error
                );


                alert(
                    "Failed to add camera.\n\n" +
                    error.message
                );

            }

        }
    );

}


// ============================================================
// EDIT CAMERA
// ============================================================

async function editCamera(cameraId) {

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

        if (newName === null) return;


        const newIP =
            prompt(
                "IP address:",
                camera.ip_address || ""
            );

        if (newIP === null) return;


        const newType =
            prompt(
                "Camera type (IP / USB / NORMAL):",
                camera.camera_type || "IP"
            );

        if (newType === null) return;


        const newLocation =
            prompt(
                "Location:",
                camera.location || ""
            );

        if (newLocation === null) return;


        const newUsername =
            prompt(
                "Username:",
                camera.username || ""
            );

        if (newUsername === null) return;


        const newRtsp =
            prompt(
                "RTSP URL:",
                camera.rtsp_url || ""
            );

        if (newRtsp === null) return;


        const newStatus =
            prompt(
                "Status (online/offline):",
                camera.status || "offline"
            );

        if (newStatus === null) return;


        const newDeviceIndex =
            prompt(
                "Device Index (0 for laptop webcam):",
                camera.device_index ?? 0
            );

        if (newDeviceIndex === null) return;


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
                ) ||
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
                newType.trim().toUpperCase(),

            location:
                newLocation.trim(),

            username:
                newUsername.trim(),

            rtsp_url:
                newRtsp.trim(),

            status:
                newStatus.trim().toLowerCase(),

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
            "Camera updated successfully."
        );

    }


    catch (error) {

        console.error(
            "Edit camera error:",
            error
        );


        alert(
            "Failed to update camera.\n\n" +
            error.message
        );

    }

}


// ============================================================
// DELETE CAMERA
// ============================================================

async function deleteCamera(cameraId) {

    const confirmed =
        confirm(
            "Are you sure you want to delete this camera?"
        );


    if (!confirmed) return;


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


        recordingCameras.delete(
            Number(cameraId)
        );


        stopLiveCamera();


        await loadCameras();

        await loadRecordings();


        alert(
            "Camera deleted successfully."
        );

    }


    catch (error) {

        console.error(
            "Delete camera error:",
            error
        );


        alert(
            "Failed to delete camera.\n\n" +
            error.message
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
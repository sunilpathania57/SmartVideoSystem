// ============================================================
// SMART VIDEO MANAGEMENT SYSTEM
// FRONTEND JAVASCRIPT
// ============================================================


// ============================================================
// RECORDING STATE
// ============================================================

const recordingCameras = new Set();

// Dynamic CCTV wall screen modes.
const CAMERA_SCREEN_OPTIONS = [4, 8, 12, 16];

let selectedScreenMode = "auto";
let currentScreenSlots = 4;

// Automatically refresh Recording History so newly completed
// segments saved by the backend appear without manual refresh.
let recordingRefreshTimer = null;
let recordingRefreshInProgress = false;


// ============================================================
// PAGE READY
// ============================================================

document.addEventListener("DOMContentLoaded", () => {

    console.log("Smart Video System started.");

    setupCameraForm();

    setupLiveWallControls();

    setupAllRecordingControls();

    setupScreenModeControls();

    loadCameras();

    loadRecordings();

    startRecordingHistoryRefresh();

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

        window.smartVideoCameras =
            Array.isArray(cameras)
                ? cameras
                : [];


        cameraList.innerHTML = "";


        if (!Array.isArray(cameras) || cameras.length === 0) {

            currentScreenSlots = 4;

            updateScreenModeDisplay(0);

            cameraList.innerHTML =
                "<p>No cameras found.</p>";

            return;
        }


        currentScreenSlots =
            getScreenSlotCount(cameras.length);

        updateScreenModeDisplay(cameras.length);


        cameras.forEach(camera => {

            createCameraCard(
                camera,
                cameraList
            );

        });

        // Keep four dashboard positions visible while testing.
        // Empty positions are visual placeholders only and are NOT
        // added to the database as fake cameras.
        addEmptyCameraSlots(
            cameras.length,
            currentScreenSlots,
            cameraList
        );

        // Start live view for every configured camera source.
        // USB cameras should use unique device indexes.
        startAllCameraTiles(cameras);

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
// DYNAMIC CAMERA SCREEN MODE
// ============================================================

function getScreenSlotCount(cameraCount) {

    if (selectedScreenMode !== "auto") {
        return Number(selectedScreenMode);
    }

    if (cameraCount <= 4) {
        return 4;
    }

    if (cameraCount <= 8) {
        return 8;
    }

    if (cameraCount <= 12) {
        return 12;
    }

    return 16;
}


function updateScreenModeDisplay(cameraCount) {

    const label =
        document.getElementById("screenModeLabel");

    if (label) {

        label.textContent =
            selectedScreenMode === "auto"
                ? `Auto: ${currentScreenSlots} Screens`
                : `${currentScreenSlots} Screens`;
    }

    const select =
        document.getElementById("screenModeSelect");

    if (select) {
        select.value = selectedScreenMode;
    }

    const cameraList =
        document.getElementById("cameraList");

    if (cameraList) {

        cameraList.classList.remove(
            "screen-4",
            "screen-8",
            "screen-12",
            "screen-16"
        );

        cameraList.classList.add(
            `screen-${currentScreenSlots}`
        );
    }
}


function setupScreenModeControls() {

    const select =
        document.getElementById("screenModeSelect");

    if (!select) {
        return;
    }

    select.addEventListener(
        "change",
        function () {

            selectedScreenMode =
                select.value;

            const cameras =
                window.smartVideoCameras || [];

            currentScreenSlots =
                getScreenSlotCount(cameras.length);

            updateScreenModeDisplay(cameras.length);

            const cameraList =
                document.getElementById("cameraList");

            if (!cameraList) {
                return;
            }

            cameraList.innerHTML = "";

            cameras.forEach(
                camera => {
                    createCameraCard(
                        camera,
                        cameraList
                    );
                }
            );

            addEmptyCameraSlots(
                cameras.length,
                currentScreenSlots,
                cameraList
            );

            startAllCameraTiles(cameras);
        }
    );
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

            <div class="camera-title-area">

                <h3>
                    CAM ${camera.id}
                </h3>

            </div>

            <div class="camera-status-area">

                <span
                    class="status-badge ${escapeHtml(status)}"
                >
                    ${escapeHtml(
                        status
                    ).toUpperCase()}
                </span>

                <span
                    class="recording-indicator ${isRecording ? "recording-on" : ""}"
                >
                    ${isRecording ? "● REC" : "● LIVE"}
                </span>

            </div>

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

            <div class="camera-overlay">

                <span class="camera-live-label">
                    ${hasVideoSource ? "LIVE VIEW" : "NO SIGNAL"}
                </span>

                <span class="camera-location-label">
                    ${escapeHtml(camera.location || "")}
                </span>

            </div>

        </div>


        <div class="camera-card-body">

            <p class="camera-location-only">
                <strong>Location:</strong>
                ${escapeHtml(
                    camera.location || "-"
                )}
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

    const image =
        document.getElementById(
            `camera-live-${cameraId}`
        );

    const noSignal =
        document.getElementById(
            `camera-no-signal-${cameraId}`
        );

    if (!image) {

        return false;

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

        buttonElement.dataset.tileActive =
            "true";

    }

    return true;

}


// ============================================================
// START ALL CAMERA TILES
// ============================================================

function startAllCameraTiles(
    cameras = []
) {

    const seenUsbDevices =
        new Set();

    cameras.forEach(
        camera => {

            const cameraType =
                String(
                    camera.camera_type || "IP"
                )
                .trim()
                .toUpperCase();

            const hasUsbSource =
                cameraType === "USB"
                &&
                camera.device_index !== null
                &&
                camera.device_index !== undefined;

            const hasRtspSource =
                cameraType === "IP"
                &&
                Boolean(camera.rtsp_url);

            if (
                !hasUsbSource
                &&
                !hasRtspSource
            ) {

                return;

            }

            // A USB camera used for recording should not also be
            // opened by the live tile. After recording stops,
            // loadCameras() will start the live tile again.
            if (
                hasUsbSource
                &&
                recordingCameras.has(
                    Number(camera.id)
                )
            ) {

                return;

            }

            // A physical USB device should not be opened twice.
            if (hasUsbSource) {

                const deviceIndex =
                    Number(
                        camera.device_index
                    );

                if (
                    seenUsbDevices.has(
                        deviceIndex
                    )
                ) {

                    console.warn(
                        `USB device ${deviceIndex} `
                        + "is already used by another camera."
                    );

                    return;

                }

                seenUsbDevices.add(
                    deviceIndex
                );

            }

            const image =
                document.getElementById(
                    `camera-live-${camera.id}`
                );

            const button =
                image
                    ? image
                        .closest(".camera-card")
                        ?.querySelector(
                            ".grid-live-button"
                        )
                    : null;

            startCameraTile(
                camera.id,
                button
            );

        }
    );

}


function stopAllCameraTiles() {

    const tileImages =
        document.querySelectorAll(
            ".camera-live-image"
        );

    tileImages.forEach(
        image => {

            image.src = "";

            image.style.display =
                "none";

        }
    );

    const noSignalElements =
        document.querySelectorAll(
            ".camera-no-signal"
        );

    noSignalElements.forEach(
        element => {

            element.style.display =
                "flex";

        }
    );

    const tileButtons =
        document.querySelectorAll(
            ".grid-live-button"
        );

    tileButtons.forEach(
        button => {

            button.textContent =
                "▶ Live Tile";

            button.dataset.tileActive =
                "false";

        }
    );

}


// ============================================================
// STOP ONE CAMERA TILE
// ============================================================

function stopCameraTileById(
    cameraId
) {

    const image =
        document.getElementById(
            `camera-live-${cameraId}`
        );

    const noSignal =
        document.getElementById(
            `camera-no-signal-${cameraId}`
        );

    const button =
        image
            ? image
                .closest(".camera-card")
                ?.querySelector(
                    ".grid-live-button"
                )
            : null;

    if (image) {

        image.src = "";

        image.style.display =
            "none";

    }

    if (noSignal) {

        noSignal.style.display =
            "flex";

    }

    if (button) {

        button.textContent =
            "▶ Live Tile";

        button.dataset.tileActive =
            "false";

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

    // Stop the selected tile and large preview first.
    // This prevents the same USB webcam from being opened twice.
    stopCameraTileById(cameraId);
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

        // Refresh recording history as well.
        await loadRecordings();


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

    if (recordingRefreshInProgress) {
        return;
    }

    recordingRefreshInProgress = true;

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
    finally {

        recordingRefreshInProgress = false;

    }

}


// ============================================================
// AUTOMATIC RECORDING HISTORY REFRESH
// ============================================================

function startRecordingHistoryRefresh() {

    if (recordingRefreshTimer !== null) {
        clearInterval(recordingRefreshTimer);
    }

    // The recorder saves completed segments to PostgreSQL.
    // Refresh every 3 seconds so the webpage shows new segments
    // without requiring Ctrl + F5.
    recordingRefreshTimer = setInterval(
        () => {
            loadRecordings();
        },
        3000
    );

}


// ============================================================
// LIVE WALL BUTTON SETUP
// ============================================================

function setupLiveWallControls() {

    const startButton =
        document.getElementById(
            "startAllLive"
        );

    const stopButton =
        document.getElementById(
            "stopAllLive"
        );

    if (startButton) {

        startButton.addEventListener(
            "click",
            startAllLiveFromDashboard
        );

    }

    if (stopButton) {

        stopButton.addEventListener(
            "click",
            stopAllLiveFromDashboard
        );

    }

}


// ============================================================
// MANUAL LIVE WALL CONTROLS
// ============================================================

function startAllLiveFromDashboard() {

    const cameras =
        window.smartVideoCameras || [];

    startAllCameraTiles(
        cameras
    );

}


function stopAllLiveFromDashboard() {

    stopAllCameraTiles();

}


// ============================================================
// START ALL RECORDINGS
// ============================================================

async function startAllRecordingsFromDashboard() {

    const cameras =
        window.smartVideoCameras || [];

    const availableCameras =
        cameras.filter(
            camera => {

                const cameraType =
                    String(
                        camera.camera_type || "IP"
                    )
                    .trim()
                    .toUpperCase();

                const hasUsbSource =
                    cameraType === "USB"
                    &&
                    camera.device_index !== null
                    &&
                    camera.device_index !== undefined;

                const hasRtspSource =
                    cameraType === "IP"
                    &&
                    Boolean(camera.rtsp_url);

                return (
                    (hasUsbSource || hasRtspSource)
                    &&
                    !recordingCameras.has(
                        Number(camera.id)
                    )
                );
            }
        );

    if (availableCameras.length === 0) {

        alert(
            "No available cameras to start recording."
        );

        return;
    }

    // Stop all live tiles before starting recordings.
    // This prevents the same USB source being opened twice.
    stopAllCameraTiles();

    let started = 0;
    let failed = 0;

    for (const camera of availableCameras) {

        try {

            const response =
                await fetch(
                    `/record/start/${camera.id}`,
                    {
                        method: "POST"
                    }
                );

            const responseText =
                await response.text();

            let result = {};

            try {

                result = responseText
                    ? JSON.parse(responseText)
                    : {};

            } catch {

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

            recordingCameras.add(
                Number(camera.id)
            );

            started += 1;

        } catch (error) {

            failed += 1;

            console.error(
                `Could not start recording for camera ${camera.id}:`,
                error
            );
        }
    }

    await loadCameras();
    await loadRecordings();

    alert(
        "Start All Recording completed.\n\n" +
        `Started: ${started}\n` +
        `Failed: ${failed}`
    );
}


// ============================================================
// STOP ALL RECORDINGS
// ============================================================

async function stopAllRecordingsFromDashboard() {

    const ids =
        Array.from(
            recordingCameras
        );

    if (ids.length === 0) {

        alert(
            "No cameras are currently recording."
        );

        return;
    }

    let stopped = 0;
    let failed = 0;

    for (const cameraId of ids) {

        try {

            const response =
                await fetch(
                    `/record/stop/${cameraId}`,
                    {
                        method: "POST"
                    }
                );

            const responseText =
                await response.text();

            let result = {};

            try {

                result = responseText
                    ? JSON.parse(responseText)
                    : {};

            } catch {

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

            recordingCameras.delete(
                Number(cameraId)
            );

            stopped += 1;

        } catch (error) {

            failed += 1;

            console.error(
                `Could not stop recording for camera ${cameraId}:`,
                error
            );
        }
    }

    await loadCameras();
    await loadRecordings();

    // Cameras no longer recording can return to live view.
    startAllCameraTiles(
        window.smartVideoCameras || []
    );

    alert(
        "Stop All Recording completed.\n\n" +
        `Stopped: ${stopped}\n` +
        `Failed: ${failed}`
    );
}


// ============================================================
// SETUP GLOBAL RECORDING BUTTONS
// ============================================================

function setupAllRecordingControls() {

    const startButton =
        document.getElementById(
            "startAllRecording"
        );

    const stopButton =
        document.getElementById(
            "stopAllRecording"
        );

    if (startButton) {

        startButton.addEventListener(
            "click",
            startAllRecordingsFromDashboard
        );
    }

    if (stopButton) {

        stopButton.addEventListener(
            "click",
            stopAllRecordingsFromDashboard
        );
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

    // Grid tiles remain active while the large live view is displayed.


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

    // The grid live wall is independent from the large live view.


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

                password:
                    getInputValue(
                        "password"
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


        const newPassword =
            prompt(
                "Password:",
                camera.password || ""
            );

        if (newPassword === null) return;


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

            password:
                newPassword,

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
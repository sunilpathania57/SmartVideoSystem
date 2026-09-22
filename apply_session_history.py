from pathlib import Path
import shutil

BASE = Path(r"D:\SmartVideoSystem")
APP = BASE / "frontend" / "app.js"
HTML = BASE / "frontend" / "recordings.html"

if not APP.exists():
    raise SystemExit(f"Not found: {APP}")
if not HTML.exists():
    raise SystemExit(f"Not found: {HTML}")

shutil.copy2(APP, BASE / "frontend" / "app.js.before_session")
shutil.copy2(HTML, BASE / "frontend" / "recordings.html.before_session")

app = APP.read_text(encoding="utf-8")

start_marker = """// ============================================================
// LOAD RECORDINGS
// ============================================================"""

end_marker = """// ============================================================
// AUTOMATIC RECORDING HISTORY REFRESH
// ============================================================"""

start = app.find(start_marker)
end = app.find(end_marker)

if start < 0 or end < 0 or end <= start:
    raise SystemExit("Could not find LOAD RECORDINGS section in app.js")

new_section = """// ============================================================
// LOAD RECORDINGS - SESSION VIEW
// ============================================================
//
// The recorder still creates physical 5-minute segments.
// This page groups adjacent segments into one logical session.
// No database schema or recording mechanism is changed.
//

const RECORDING_SESSION_GAP_SECONDS = 90;
let recordingHistoryData = [];

function recordingTime(value) {
    if (!value) return null;
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date;
}

function formatRecordingDate(value) {
    const date = recordingTime(value);
    if (!date) return "-";
    return date.toLocaleDateString(undefined, {
        day: "2-digit", month: "short", year: "numeric"
    });
}

function formatRecordingTime(value) {
    const date = recordingTime(value);
    if (!date) return "-";
    return date.toLocaleTimeString(undefined, {
        hour: "2-digit", minute: "2-digit", second: "2-digit"
    });
}

function formatSessionDuration(totalSeconds) {
    const seconds = Math.max(0, Math.round(Number(totalSeconds) || 0));
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;

    if (hours > 0) return `${hours}h ${minutes}m ${remainingSeconds}s`;
    if (minutes > 0) return `${minutes}m ${remainingSeconds}s`;
    return `${remainingSeconds}s`;
}

function recordingMatchesFilters(recording) {
    const search = (
        document.getElementById("recordingSearch")?.value || ""
    ).trim().toLowerCase();

    const cameraFilter = (
        document.getElementById("recordingCameraFilter")?.value || ""
    ).trim();

    const statusFilter = (
        document.getElementById("recordingStatusFilter")?.value || ""
    ).trim().toLowerCase();

    const text = [
        recording.filename || "",
        recording.camera_id ?? "",
        recording.status || ""
    ].join(" ").toLowerCase();

    if (search && !text.includes(search)) return false;
    if (cameraFilter && String(recording.camera_id) !== cameraFilter) return false;
    if (
        statusFilter &&
        String(recording.status || "").toLowerCase() !== statusFilter
    ) return false;

    return true;
}

function groupRecordingsIntoSessions(recordings) {
    const sorted = recordings
        .filter(recordingMatchesFilters)
        .slice()
        .sort((a, b) => {
            const at = recordingTime(a.start_time)?.getTime() || 0;
            const bt = recordingTime(b.start_time)?.getTime() || 0;
            return at - bt;
        });

    const sessions = [];

    sorted.forEach(recording => {
        const cameraId = Number(recording.camera_id);
        const start = recordingTime(recording.start_time);
        const end = recordingTime(recording.end_time) || start;

        let session = sessions[sessions.length - 1];
        let newSession = true;

        if (session && session.cameraId === cameraId) {
            const previousEnd = recordingTime(session.end_time);
            const gapSeconds =
                previousEnd && start
                    ? (start.getTime() - previousEnd.getTime()) / 1000
                    : Infinity;

            newSession = gapSeconds > RECORDING_SESSION_GAP_SECONDS;
        }

        if (newSession) {
            session = {
                cameraId,
                start_time: recording.start_time,
                end_time: recording.end_time,
                duration_seconds: Number(recording.duration_seconds) || 0,
                status: recording.status || "completed",
                segments: []
            };
            sessions.push(session);
        } else {
            session.end_time = recording.end_time || session.end_time;
            session.duration_seconds += Number(recording.duration_seconds) || 0;
            if (recording.status !== "completed") {
                session.status = recording.status || session.status;
            }
        }

        session.segments.push(recording);
    });

    return sessions.reverse();
}

function renderRecordingSessions(sessions) {
    const list = document.getElementById("recordingList");
    if (!list) return;

    list.innerHTML = "";

    if (!sessions.length) {
        list.innerHTML = "<p>No recordings found.</p>";
        return;
    }

    sessions.forEach((session, sessionIndex) => {
        const item = document.createElement("div");
        item.className = "recording-session-item";

        const first = session.segments[0];

        item.innerHTML = `
            <div class="recording-session-main">
                <div class="recording-session-info">
                    <strong>Camera ${escapeHtml(session.cameraId)}</strong>
                    <span>${escapeHtml(formatRecordingDate(session.start_time))}</span>
                    <span>
                        ${escapeHtml(formatRecordingTime(session.start_time))}
                        →
                        ${escapeHtml(formatRecordingTime(session.end_time))}
                    </span>
                    <span>
                        Duration: ${escapeHtml(formatSessionDuration(session.duration_seconds))}
                    </span>
                    <span>
                        ${session.segments.length}
                        segment${session.segments.length === 1 ? "" : "s"}
                    </span>
                    <span class="recording-status ${escapeHtml(
                        String(session.status || "").toLowerCase()
                    )}">
                        ${escapeHtml(String(session.status || "-").toUpperCase())}
                    </span>
                </div>

                <div class="recording-session-actions">
                    <button type="button" class="view-session-button">
                        VIEW
                    </button>

                    <button
                        type="button"
                        class="play-recording-button"
                        data-recording-id="${first ? first.id : ""}"
                    >
                        ▶ Play
                    </button>
                </div>
            </div>

            <div class="recording-session-details" hidden>
                <div class="session-details-header">
                    <strong>Recording Segments</strong>
                    <span>${session.segments.length} physical files</span>
                </div>
                <div class="session-segment-list"></div>
            </div>
        `;

        const details = item.querySelector(".recording-session-details");
        const viewButton = item.querySelector(".view-session-button");
        const segmentList = item.querySelector(".session-segment-list");

        session.segments.forEach((segment, index) => {
            const row = document.createElement("div");
            row.className = "recording-segment-row";

            row.innerHTML = `
                <div class="recording-segment-info">
                    <strong>Segment ${index + 1}</strong>
                    <span>
                        ${escapeHtml(formatRecordingTime(segment.start_time))}
                        →
                        ${escapeHtml(formatRecordingTime(segment.end_time))}
                    </span>
                    <span>
                        ${escapeHtml(formatSessionDuration(segment.duration_seconds))}
                    </span>
                    <span class="recording-filename"
                          title="${escapeHtml(segment.filename || "")}">
                        ${escapeHtml(segment.filename || "-")}
                    </span>
                </div>

                <div class="recording-actions">
                    <button
                        type="button"
                        class="play-recording-button"
                        data-recording-id="${segment.id}"
                    >
                        ▶ Play
                    </button>

                    <a
                        href="/recordings/${segment.id}/download"
                        class="download-recording-button"
                    >
                        ⬇ Download
                    </a>
                </div>
            `;

            segmentList.appendChild(row);
        });

        list.appendChild(item);

        viewButton.addEventListener("click", () => {
            details.hidden = !details.hidden;
            viewButton.textContent = details.hidden ? "VIEW" : "HIDE";
        });

        item.querySelectorAll(".play-recording-button").forEach(button => {
            button.addEventListener("click", () => {
                const id = Number(button.dataset.recordingId);
                if (id) playRecording(id);
            });
        });
    });
}

async function loadRecordings() {
    if (recordingRefreshInProgress) return;

    recordingRefreshInProgress = true;

    const list = document.getElementById("recordingList");

    if (!list) {
        recordingRefreshInProgress = false;
        return;
    }

    try {
        const response = await fetch(
            `/recordings?_t=${Date.now()}`,
            { cache: "no-store" }
        );

        if (!response.ok) {
            throw new Error("Failed to load recordings");
        }

        const recordings = await response.json();

        recordingHistoryData =
            Array.isArray(recordings) ? recordings : [];

        renderRecordingSessions(
            groupRecordingsIntoSessions(recordingHistoryData)
        );
    }
    catch (error) {
        console.error("Recording history error:", error);
        list.innerHTML = "<p>Unable to load recordings.</p>";
    }
    finally {
        recordingRefreshInProgress = false;
    }
}

function setupRecordingHistoryFilters() {
    const search = document.getElementById("recordingSearch");
    const camera = document.getElementById("recordingCameraFilter");
    const status = document.getElementById("recordingStatusFilter");
    const clearButton = document.getElementById("clearRecordingFilters");

    [search, camera, status].filter(Boolean).forEach(element => {
        element.addEventListener("input", () => {
            renderRecordingSessions(
                groupRecordingsIntoSessions(recordingHistoryData)
            );
        });

        element.addEventListener("change", () => {
            renderRecordingSessions(
                groupRecordingsIntoSessions(recordingHistoryData)
            );
        });
    });

    clearButton?.addEventListener("click", () => {
        if (search) search.value = "";
        if (camera) camera.value = "";
        if (status) status.value = "";

        renderRecordingSessions(
            groupRecordingsIntoSessions(recordingHistoryData)
        );
    });
}

// ============================================================
// AUTOMATIC RECORDING HISTORY REFRESH
// ============================================================"""

app = app[:start] + new_section + app[end + len(end_marker):]

old = """    setupScreenModeControls();

    loadCameras();"""
new = """    setupScreenModeControls();

    setupRecordingHistoryFilters();

    loadCameras();"""

if old not in app:
    raise SystemExit("Could not find DOMContentLoaded insertion point")

app = app.replace(old, new, 1)
APP.write_text(app, encoding="utf-8")

html = HTML.read_text(encoding="utf-8")

css = """
        /* Recording session history */
        .recording-session-item {
            border: 1px solid #d8dde5;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
            background: #ffffff;
        }

        .recording-session-main {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }

        .recording-session-info {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
            min-width: 0;
        }

        .recording-session-info > span {
            font-size: 13px;
        }

        .recording-session-actions,
        .recording-actions {
            display: flex;
            align-items: center;
            gap: 6px;
            flex-wrap: wrap;
        }

        .recording-session-details {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #e3e7ed;
        }

        .session-details-header {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 8px;
            font-size: 13px;
        }

        .recording-segment-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            padding: 8px 0;
            border-top: 1px solid #edf0f4;
        }

        .recording-segment-info {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
            min-width: 0;
        }

        .recording-segment-info > span {
            font-size: 12px;
        }

        .recording-filename {
            max-width: 360px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .recording-status {
            font-weight: 600;
        }

        .recording-status.completed {
            color: #16743a;
        }

        .recording-status.recording {
            color: #b36b00;
        }

        .recording-status.failed {
            color: #b42318;
        }

        @media (max-width: 800px) {
            .recording-session-main,
            .recording-segment-row {
                align-items: flex-start;
                flex-direction: column;
            }

            .recording-session-actions,
            .recording-actions {
                width: 100%;
            }

            .recording-filename {
                max-width: 100%;
            }
        }
"""

if "</style>" not in html:
    raise SystemExit("Could not find </style> in recordings.html")

html = html.replace("</style>", css + "\n</style>", 1)
html = html.replace(
    'placeholder="Search filename..."',
    'placeholder="Search camera / filename..."',
    1
)

HTML.write_text(html, encoding="utf-8")

print("SUCCESS - Session History update applied.")
print("Recorder and PostgreSQL schema were NOT changed.")
print("Backups: frontend/app.js.before_session and frontend/recordings.html.before_session")

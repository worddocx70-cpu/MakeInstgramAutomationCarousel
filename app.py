from flask import Flask, render_template_string, request, jsonify
from pathlib import Path
import os
import re
import time
import requests

from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader


# ============================================================
# APP / ENV
# ============================================================

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE, override=True)


# ============================================================
# CLOUDINARY
# ============================================================

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "").strip()
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "").strip()

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True
)


# ============================================================
# MAKE.COM
# ============================================================

BASE_URL = "https://eu1.make.com/api/v2"

SOURCE_SCENARIO_ID = 7507633
SOURCE_HOOK_ID = 3753533
TEAM_ID = 2866418
ORGANIZATION_ID = 9045277

EXECUTION_TIMEOUT = 180
EXECUTION_POLL_INTERVAL = 2


# ============================================================
# HTML
# ============================================================

HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Instagram Carousel Manager</title>

<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: Arial, Helvetica, sans-serif;
    background: #f4f4f4;
    color: #111;
    padding: 30px 15px;
}

.container {
    max-width: 1050px;
    margin: auto;
}

h1 {
    text-align: center;
    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    color: #666;
    margin-top: 0;
    margin-bottom: 25px;
}

.box {
    background: white;
    border: 1px solid #d5d5d5;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
}

.scenario-label {
    display: block;
    font-weight: bold;
    margin-bottom: 8px;
}

.scenario-input {
    width: 100%;
    padding: 13px;
    border: 1px solid #bbb;
    border-radius: 7px;
    font-size: 16px;
    outline: none;
}

.scenario-input:focus {
    border-color: #111;
}

.drop {
    display: block;
    border: 2px dashed #999;
    border-radius: 10px;
    padding: 45px 20px;
    text-align: center;
    cursor: pointer;
    margin-top: 20px;
}

.drop:hover {
    background: #fafafa;
}

.drop.drag {
    border-color: #111;
    background: #f5f5f5;
}

.drop strong {
    font-size: 18px;
}

.drop span {
    display: block;
    margin-top: 8px;
    color: #666;
}

input[type="file"] {
    display: none;
}

.actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 18px;
}

button {
    border: none;
    border-radius: 7px;
    padding: 11px 15px;
    font-size: 14px;
    font-weight: bold;
    cursor: pointer;
}

button:disabled {
    opacity: .45;
    cursor: not-allowed;
}

.primary {
    background: #111;
    color: white;
}

.secondary {
    background: #e8e8e8;
    color: #111;
}

.danger {
    background: #eee;
    color: #a00000;
}

#list {
    margin-top: 25px;
}

.image-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
    gap: 18px;
    margin-top: 15px;
}

.image-card {
    border: 1px solid #ccc;
    border-radius: 10px;
    background: #fafafa;
    overflow: hidden;
    position: relative;
}

.preview {
    width: 100%;
    aspect-ratio: 9 / 16;
    object-fit: contain;
    display: block;
    background: #222;
}

.image-number {
    position: absolute;
    top: 8px;
    left: 8px;
    background: #111;
    color: white;
    padding: 5px 9px;
    border-radius: 5px;
    font-size: 13px;
    font-weight: bold;
}

.image-name {
    padding: 9px;
    font-size: 13px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.card-buttons {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 6px;
    padding: 8px;
}

.card-buttons button {
    padding: 8px 5px;
    font-size: 12px;
}

.progress {
    height: 10px;
    background: #ddd;
    border-radius: 10px;
    overflow: hidden;
    margin-top: 20px;
}

.bar {
    height: 100%;
    width: 0%;
    background: #111;
    transition: width .2s;
}

.status {
    margin-top: 18px;
    white-space: pre-wrap;
    line-height: 1.5;
}

.success {
    background: #e8f5e9;
    color: #116b34;
    padding: 15px;
    border-radius: 7px;
}

.error {
    background: #ffebee;
    color: #a21d1d;
    padding: 15px;
    border-radius: 7px;
}

.info {
    background: #eeeeee;
    color: #222;
    padding: 15px;
    border-radius: 7px;
}

.small {
    color: #666;
    font-size: 13px;
    line-height: 1.6;
}

code {
    background: #eee;
    padding: 2px 5px;
    border-radius: 4px;
}

@media (max-width: 600px) {
    body { padding: 15px 8px; }
    .box { padding: 15px; }
    .image-grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
    }
}
</style>
</head>

<body>

<div class="container">

<h1>Instagram Carousel Manager</h1>

<p class="subtitle">
Select → Arrange → Upload → Create Make Scenario → Post
</p>

<div class="box">

<label class="scenario-label" for="scenarioName">
Scenario Name
</label>

<input
    id="scenarioName"
    class="scenario-input"
    type="text"
    placeholder="Example: Birds"
    autocomplete="off"
>

<label class="drop" id="drop">

    <input
        id="files"
        type="file"
        accept="image/*"
        multiple
    >

    <strong>Select Images</strong>

    <span>or drag & drop images here</span>

</label>

<div class="actions">

    <button class="secondary" id="clear" type="button">
        Clear All
    </button>

    <button class="secondary" id="reverse" type="button" disabled>
        Reverse Order
    </button>

    <button class="primary" id="run" type="button" disabled>
        UPLOAD & CREATE MAKE SCENARIO
    </button>

</div>

<div id="list"></div>

<div class="progress">
    <div class="bar" id="bar"></div>
</div>

<div id="status" class="status"></div>

</div>

<div class="box">

<b>How it works</b>

<p class="small">
1. Select your images.<br>
2. Arrange them using Left / Right / Front / Back.<br>
3. Enter the scenario name.<br>
4. Images are uploaded directly to Cloudinary.<br>
5. Cloudinary provides public HTTPS image URLs.<br>
6. URLs are sent directly to your Make webhook.<br>
7. Make creates the Instagram carousel.<br>
8. The newly created Make scenario is deactivated after execution.
<br><br>
No TXT files are required.<br>
No permanent local image copies are created.
</p>

</div>

</div>

<script>

const input = document.getElementById("files");
const drop = document.getElementById("drop");
const list = document.getElementById("list");
const runBtn = document.getElementById("run");
const clearBtn = document.getElementById("clear");
const reverseBtn = document.getElementById("reverse");
const statusEl = document.getElementById("status");
const bar = document.getElementById("bar");
const scenarioNameInput = document.getElementById("scenarioName");

let items = [];


function addFiles(fileList) {

    for (const file of fileList) {

        if (file.type && file.type.startsWith("image/")) {
            items.push(file);
        }

    }

    render();
}


function render() {

    list.innerHTML = "";

    const hasImages = items.length > 0;

    runBtn.disabled = !hasImages;
    reverseBtn.disabled = !hasImages;

    if (!hasImages) {
        return;
    }

    const grid = document.createElement("div");
    grid.className = "image-grid";

    items.forEach((file, index) => {

        const card = document.createElement("div");
        card.className = "image-card";

        const number = document.createElement("div");
        number.className = "image-number";
        number.textContent = `#${index + 1}`;

        const img = document.createElement("img");
        img.className = "preview";
        img.alt = file.name;
        img.src = URL.createObjectURL(file);

        const name = document.createElement("div");
        name.className = "image-name";
        name.textContent = file.name;

        const buttons = document.createElement("div");
        buttons.className = "card-buttons";


        const left = document.createElement("button");
        left.type = "button";
        left.className = "secondary";
        left.textContent = "← Left";
        left.disabled = index === 0;

        left.onclick = () => {

            if (index <= 0) return;

            [
                items[index - 1],
                items[index]
            ] = [
                items[index],
                items[index - 1]
            ];

            render();
        };


        const right = document.createElement("button");
        right.type = "button";
        right.className = "secondary";
        right.textContent = "Right →";
        right.disabled = index === items.length - 1;

        right.onclick = () => {

            if (index >= items.length - 1) return;

            [
                items[index],
                items[index + 1]
            ] = [
                items[index + 1],
                items[index]
            ];

            render();
        };


        const front = document.createElement("button");
        front.type = "button";
        front.className = "secondary";
        front.textContent = "⇤ Front";
        front.disabled = index === 0;

        front.onclick = () => {

            if (index <= 0) return;

            const item = items.splice(index, 1)[0];
            items.unshift(item);

            render();
        };


        const back = document.createElement("button");
        back.type = "button";
        back.className = "secondary";
        back.textContent = "Back ⇥";
        back.disabled = index === items.length - 1;

        back.onclick = () => {

            if (index >= items.length - 1) return;

            const item = items.splice(index, 1)[0];
            items.push(item);

            render();
        };


        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "danger";
        remove.textContent = "Remove";

        remove.onclick = () => {

            items.splice(index, 1);
            render();
        };


        buttons.appendChild(left);
        buttons.appendChild(right);
        buttons.appendChild(front);
        buttons.appendChild(back);
        buttons.appendChild(remove);

        card.appendChild(number);
        card.appendChild(img);
        card.appendChild(name);
        card.appendChild(buttons);

        grid.appendChild(card);

    });

    list.appendChild(grid);
}


input.addEventListener("change", () => {

    addFiles(input.files);
    input.value = "";

});


["dragenter", "dragover"].forEach(eventName => {

    drop.addEventListener(eventName, event => {

        event.preventDefault();
        drop.classList.add("drag");

    });

});


["dragleave", "drop"].forEach(eventName => {

    drop.addEventListener(eventName, event => {

        event.preventDefault();
        drop.classList.remove("drag");

    });

});


drop.addEventListener("drop", event => {

    addFiles(event.dataTransfer.files);

});


clearBtn.addEventListener("click", () => {

    items = [];
    input.value = "";

    statusEl.className = "status";
    statusEl.textContent = "";

    bar.style.width = "0%";

    render();

});


reverseBtn.addEventListener("click", () => {

    items.reverse();
    render();

});


runBtn.addEventListener("click", async () => {

    if (!items.length) return;

    const scenarioName =
        scenarioNameInput.value.trim();

    if (!scenarioName) {

        statusEl.className = "status error";
        statusEl.textContent =
            "Please enter a scenario name.";

        scenarioNameInput.focus();

        return;
    }

    if (items.length < 2) {

        statusEl.className = "status error";
        statusEl.textContent =
            "Please select at least 2 images.";

        return;
    }

    runBtn.disabled = true;
    clearBtn.disabled = true;
    reverseBtn.disabled = true;
    scenarioNameInput.disabled = true;

    bar.style.width = "5%";

    statusEl.className = "status info";
    statusEl.textContent =
        `Preparing ${items.length} image(s)...`;

    const form = new FormData();

    form.append(
        "scenario_name",
        scenarioName
    );

    items.forEach(file => {

        form.append(
            "images",
            file,
            file.name
        );

    });


    try {

        statusEl.textContent =
            "Uploading images to Cloudinary...";

        bar.style.width = "15%";

        const response = await fetch(
            "/api/process",
            {
                method: "POST",
                body: form
            }
        );

        const data = await response.json();

        if (!response.ok || !data.success) {

            throw new Error(
                data.error || "Process failed."
            );

        }

        bar.style.width = "100%";

        statusEl.className = "status success";

        let message = "SUCCESS!\n\n";

        message +=
            `Scenario: ${data.scenario_name}\n`;

        message +=
            `Scenario ID: ${data.scenario_id}\n`;

        message +=
            `Images: ${data.count}\n`;

        message +=
            `Execution ID: ${data.execution_id}\n`;

        message +=
            `Execution status: ${data.execution_result}\n`;

        message +=
            "\nCloudinary upload completed successfully.";

        statusEl.textContent = message;

    } catch (error) {

        bar.style.width = "0%";

        statusEl.className = "status error";
        statusEl.textContent = error.message;

    } finally {

        runBtn.disabled = items.length < 2;
        clearBtn.disabled = false;
        reverseBtn.disabled = items.length === 0;
        scenarioNameInput.disabled = false;

    }

});


render();

</script>

</body>
</html>
"""


# ============================================================
# HELPERS
# ============================================================

def get_make_token():
    return os.getenv("MAKE_API_TOKEN", "").strip()


def cloudinary_is_configured():
    return all([
        CLOUDINARY_CLOUD_NAME,
        CLOUDINARY_API_KEY,
        CLOUDINARY_API_SECRET
    ])


def clean_scenario_name(name):

    name = name.strip()

    name = re.sub(
        r"\s+",
        " ",
        name
    )

    name = re.sub(
        r"[^A-Za-z0-9 _-]",
        "",
        name
    )

    return name.strip()


# ============================================================
# CLOUDINARY UPLOAD
# ============================================================

def upload_to_cloudinary(file_storage):

    if not cloudinary_is_configured():

        raise Exception(
            "Cloudinary credentials are missing from .env."
        )

    filename = (
        file_storage.filename
        or "image.jpg"
    )

    try:

        result = cloudinary.uploader.upload(
            file_storage,
            resource_type="image"
        )

    except Exception as e:

        raise Exception(
            f"Cloudinary upload failed for "
            f"{filename}: {str(e)}"
        )

    url = result.get("secure_url")

    if not url:

        raise Exception(
            f"Cloudinary did not return a secure URL "
            f"for {filename}."
        )

    return url


# ============================================================
# MAKE
# ============================================================

def get_make_headers():

    token = get_make_token()

    if not token:

        raise Exception(
            "MAKE_API_TOKEN is missing from .env."
        )

    return {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }


def create_webhook(name, headers):

    data = {
        "name": f"{name} Webhook",
        "teamId": TEAM_ID,
        "typeName": "gateway-webhook",
        "method": False,
        "headers": False,
        "stringify": False
    }

    response = requests.post(
        f"{BASE_URL}/hooks",
        headers=headers,
        json=data,
        timeout=30
    )

    if not response.ok:

        raise Exception(
            "Webhook creation failed: "
            + response.text
        )

    hook = response.json().get("hook")

    if not hook:

        raise Exception(
            "Make did not return a webhook."
        )

    return hook


def create_scenario(name, hook_id, headers):

    data = {
        "name": name,
        "teamId": TEAM_ID,
        "hook": {
            str(SOURCE_HOOK_ID): hook_id
        },
        "states": False
    }

    url = (
        f"{BASE_URL}/scenarios/"
        f"{SOURCE_SCENARIO_ID}/clone"
        f"?organizationId={ORGANIZATION_ID}"
    )

    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=30
    )

    if not response.ok:

        raise Exception(
            "Scenario creation failed: "
            + response.text
        )

    scenario = response.json().get("scenario")

    if not scenario:

        raise Exception(
            "Make did not return the cloned scenario."
        )

    return scenario


def activate_scenario(scenario_id, headers):

    url = (
        f"{BASE_URL}/scenarios/"
        f"{scenario_id}/start"
    )

    response = requests.post(
        url,
        headers=headers,
        timeout=30
    )

    if not response.ok:

        raise Exception(
            "Scenario activation failed: "
            + response.text
        )

    return response.json()


def deactivate_scenario(scenario_id, headers):

    url = (
        f"{BASE_URL}/scenarios/"
        f"{scenario_id}/stop"
    )

    response = requests.post(
        url,
        headers=headers,
        timeout=30
    )

    # Make IM307 = scenario is already stopped.
    if not response.ok:

        if "IM307" in response.text:

            print("Scenario already stopped.")

            return {}

        raise Exception(
            "Scenario deactivation failed: "
            + response.text
        )

    return response.json()


def get_execution_logs(scenario_id, headers):

    url = (
        f"{BASE_URL}/scenarios/"
        f"{scenario_id}/logs"
    )

    response = requests.get(
        url,
        headers=headers,
        params={"limit": 20},
        timeout=30
    )

    if not response.ok:

        raise Exception(
            "Reading Make execution logs failed: "
            + response.text
        )

    data = response.json()

    logs = data.get(
        "scenarioLogs",
        []
    )

    if isinstance(logs, dict):

        logs = logs.get(
            "data",
            logs.get("logs", [])
        )

    if not isinstance(logs, list):

        logs = []

    return logs


def get_log_execution_id(log):

    if not isinstance(log, dict):
        return None

    return (
        log.get("executionId")
        or log.get("id")
        or log.get("imtId")
    )


def get_log_status(log):

    if not isinstance(log, dict):
        return None

    status = log.get("status")

    try:
        return int(status)

    except (TypeError, ValueError):

        return status


def extract_make_error(log):

    if not isinstance(log, dict):
        return str(log)

    candidates = [
        log.get("error"),
        log.get("errors"),
        log.get("message"),
        log.get("details")
    ]

    for value in candidates:

        if value:

            return str(value)

    return str(log)


def wait_for_new_execution(
    scenario_id,
    headers,
    previous_ids
):

    deadline = (
        time.time()
        + EXECUTION_TIMEOUT
    )

    while time.time() < deadline:

        logs = get_execution_logs(
            scenario_id,
            headers
        )

        for log in logs:

            execution_id = get_log_execution_id(log)

            if not execution_id:
                continue

            if execution_id in previous_ids:
                continue

            status = get_log_status(log)

            # Make:
            # 1 = success
            # 2 = warning
            # 3 = error
            if status in (1, 2, 3):

                return {
                    "execution_id": execution_id,
                    "status": status,
                    "log": log
                }

        time.sleep(
            EXECUTION_POLL_INTERVAL
        )

    raise TimeoutError(
        "The Make execution did not finish "
        f"within {EXECUTION_TIMEOUT} seconds."
    )


def send_links(webhook_url, links):

    clean_links = []

    for url in links:

        if not isinstance(url, str):
            continue

        url = url.strip()

        # Remove Markdown URL wrappers if present.
        markdown_match = re.match(
            r"^\[.*?\]\((https?://[^)]+)\)$",
            url
        )

        if markdown_match:
            url = markdown_match.group(1)

        if (
            url.startswith("http://")
            or
            url.startswith("https://")
        ):

            clean_links.append(url)

    if len(clean_links) < 2:

        raise Exception(
            "Less than 2 valid image URLs were generated."
        )

    payload = {
        "images": clean_links
    }

    print()
    print("========== MAKE PAYLOAD ==========")
    print(payload)
    print("==================================")

    for index, url in enumerate(
        clean_links,
        start=1
    ):

        print(
            f"MAKE IMAGE {index}: {url}"
        )

    response = requests.post(
        webhook_url,
        json=payload,
        timeout=30
    )

    if not response.ok:

        raise Exception(
            "Sending image links to Make failed: "
            + response.text
        )

    return clean_links


# ============================================================
# ROUTES
# ============================================================

@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML)


@app.route("/api/process", methods=["POST"])
def process():

    uploaded_files = request.files.getlist("images")

    scenario_name = request.form.get(
        "scenario_name",
        ""
    ).strip()

    scenario_name = clean_scenario_name(
        scenario_name
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not scenario_name:

        return jsonify({
            "success": False,
            "error": "Please enter a scenario name."
        }), 400

    if len(uploaded_files) < 2:

        return jsonify({
            "success": False,
            "error": "Please select at least 2 images."
        }), 400

    if not cloudinary_is_configured():

        return jsonify({
            "success": False,
            "error": (
                "Cloudinary credentials are missing. "
                "Check CLOUDINARY_CLOUD_NAME, "
                "CLOUDINARY_API_KEY and "
                "CLOUDINARY_API_SECRET in .env."
            )
        }), 500

    if not get_make_token():

        return jsonify({
            "success": False,
            "error": "MAKE_API_TOKEN is missing from .env."
        }), 500


    try:

        # ----------------------------------------------------
        # CLOUDINARY
        # ----------------------------------------------------

        links = []

        print()
        print(
            "========== CLOUDINARY UPLOAD =========="
        )

        for index, file in enumerate(
            uploaded_files,
            start=1
        ):

            if not file.filename:

                raise Exception(
                    f"Image {index} has no filename."
                )

            print(
                f"Uploading image "
                f"{index}/{len(uploaded_files)}: "
                f"{file.filename}"
            )

            url = upload_to_cloudinary(file)

            links.append(url)

            print(
                f"URL: {url}"
            )

        print(
            "======================================="
        )


        # ----------------------------------------------------
        # FINAL URL LIST
        # ----------------------------------------------------

        print()
        print(
            "========== FINAL URL LIST =========="
        )

        for index, url in enumerate(
            links,
            start=1
        ):

            print(
                f"{index}. {url}"
            )

        print(
            "===================================="
        )


        # ----------------------------------------------------
        # MAKE
        # ----------------------------------------------------

        headers = get_make_headers()


        print(
            f"Creating webhook: {scenario_name}"
        )

        hook = create_webhook(
            scenario_name,
            headers
        )


        print(
            f"Creating Make scenario: {scenario_name}"
        )

        scenario = create_scenario(
            scenario_name,
            hook["id"],
            headers
        )

        scenario_id = scenario["id"]

        print(
            f"Scenario ID: {scenario_id}"
        )


        # ----------------------------------------------------
        # PREVIOUS EXECUTIONS
        # ----------------------------------------------------

        previous_logs = get_execution_logs(
            scenario_id,
            headers
        )

        previous_ids = {
            get_log_execution_id(log)
            for log in previous_logs
            if get_log_execution_id(log)
        }


        # ----------------------------------------------------
        # ACTIVATE
        # ----------------------------------------------------

        print(
            "Activating Make scenario..."
        )

        activate_scenario(
            scenario_id,
            headers
        )


        # ----------------------------------------------------
        # SEND
        # ----------------------------------------------------

        print(
            "Sending image URLs to Make..."
        )

        clean_links = send_links(
            hook["url"],
            links
        )


        # ----------------------------------------------------
        # WAIT
        # ----------------------------------------------------

        print()
        print(
            "Waiting for Make execution..."
        )

        execution = wait_for_new_execution(
            scenario_id,
            headers,
            previous_ids
        )

        execution_id = execution[
            "execution_id"
        ]

        execution_status = execution[
            "status"
        ]

        print(
            f"Execution status: {execution_status}"
        )


        # ----------------------------------------------------
        # DEACTIVATE
        # ----------------------------------------------------

        print(
            "Deactivating Make scenario..."
        )

        deactivate_scenario(
            scenario_id,
            headers
        )


        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        if execution_status == 1:

            execution_result = "success"

        elif execution_status == 2:

            execution_result = "warning"

        elif execution_status == 3:

            execution_result = "error"

        else:

            execution_result = str(
                execution_status
            )


        if execution_status == 3:

            make_error = extract_make_error(
                execution["log"]
            )

            print()
            print(
                "========== MAKE ERROR =========="
            )

            print(
                make_error
            )

            print(
                "================================"
            )

            return jsonify({

                "success": False,

                "error": (
                    "Make execution failed.\n\n"
                    f"Scenario: {scenario_name}\n"
                    f"Scenario ID: {scenario_id}\n"
                    f"Execution ID: {execution_id}\n\n"
                    f"Make error:\n{make_error}"
                ),

                "scenario_name": scenario_name,
                "scenario_id": scenario_id,
                "execution_id": execution_id,
                "execution_result": execution_result,
                "cloudinary_urls": clean_links

            }), 500


        return jsonify({

            "success": True,

            "count": len(clean_links),

            "scenario_name": scenario_name,

            "scenario_id": scenario_id,

            "execution_id": execution_id,

            "execution_result": execution_result,

            "cloudinary_urls": clean_links

        })


    except Exception as e:

        print()
        print(
            "========== ERROR =========="
        )

        print(
            str(e)
        )

        print(
            "==========================="
        )

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )

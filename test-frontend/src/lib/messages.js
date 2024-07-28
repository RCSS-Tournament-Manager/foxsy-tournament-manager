import { v4 as uuidv4 } from "uuid";

export function buildMessage({
    build_id,
    team_name,
    image_name,
    image_tag,
    file_id,
    bucket
}) {

    build_id = build_id || uuidv4()
    team_name = team_name || "default"
    image_name = image_name || "default"
    image_tag = image_tag || "latest"

    const m = {
        "command": "build",
        "data": {
            "build_id": build_id,
            "team_name": team_name,
            "image_name": image_name,
            "image_tag": image_tag,
            "file": {
                "_type": "minio",
                "bucket": bucket,
                "file_id": file_id
            },
            "registry": {
                "_type": "docker"
            }
        }
    }

    return JSON.stringify(m)
}



export function buildStatusMessage({mode,fetch}) {

    mode = mode || "subscribe";
    fetch = fetch || "all";

    const m = {
        "command": "status",
        "data": {
            fetch,
            mode
        }
    }

    return JSON.stringify(m)
}


export function killBuildMessage({build_id}) {

    const m = {
        "command": "kill_build",
        "data": {
            "build_id": build_id
        }
    }

    return JSON.stringify(m)
}
import { writable } from 'svelte/store';

export const connectionStateStore = writable('init'); // init, connecting, connected, failed

export async function connect() {
    connectionStateStore.set('connecting');
    try {
        // Connection logic if needed, for now, we'll assume it's always connected
        connectionStateStore.set('connected');
    } catch (error) {
        connectionStateStore.set('failed');
        console.error('Connection error:', error);
    }
}

export async function uploadFile(bucket, file, name) {
    try {
        const formData = new FormData();
        formData.append('bucket', bucket);
        formData.append('file', file);
        formData.append('name', name);

        const response = await fetch('/api/minio', {
            method: 'PUT',
            body: formData
        });

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Upload error:', error);
    }
}

export async function downloadFile(bucket, file) {
    try {
        const response = await fetch('/api/minio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: 'download', bucket, file })
        });

        if (!response.ok) {
            throw new Error('Download failed');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = file;
        document.body.appendChild(a);
        a.click();
        a.remove();
    } catch (error) {
        console.error('Download error:', error);
    }
}

export function listFiles(bucket) {
    return fetch('/api/minio', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'list', bucket })
    }).then(response => response.json());
}

export async function removeFile(bucket, file) {
    try {
        const response = await fetch('/api/minio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: 'remove', bucket, file })
        });

        if (!response.ok) {
            throw new Error('Remove failed');
        }

        return await response.json();
    } catch (error) {
        console.error('Remove error:', error);
    }
}
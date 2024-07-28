import { json } from '@sveltejs/kit';
import * as Minio from 'minio';
import { Readable } from 'stream';

const minioClient = new Minio.Client({
    endPoint: 'localhost',
    port: 9000,
    useSSL: false,
    accessKey: 'minioadmin',
    secretKey: 'minioadmin'
});

// POST endpoint for actions other than upload
export async function POST({ request }) {
    const { action, bucket, file, name } = await request.json();

    if (action === 'download') {
        try {
            const stream = await minioClient.getObject(bucket, file);
            return new Response(stream, { headers: { 'Content-Type': 'application/octet-stream' } });
        } catch (error) {
            return json({ error: 'Download failed', details: error.message }, { status: 500 });
        }
    }

    if (action === 'list') {
        try {
            const objectsList = [];
            const objectsStream = minioClient.listObjects(bucket, '', true);

            for await (const obj of objectsStream) {
                objectsList.push(obj);
            }

            return json(objectsList);
        } catch (error) {
            return json({ error: 'List objects failed', details: error.message }, { status: 500 });
        }
    }

    if (action === 'remove') {
        try {
            await minioClient.removeObject(bucket, file);
            return json({ message: 'File removed successfully' });
        } catch (error) {
            return json({ error: 'Remove failed', details: error.message }, { status: 500 });
        }
    }

    return json({ error: 'Invalid action' }, { status: 400 });
}
export async function PUT({ request }) {
    const formData = await request.formData();
    const bucket = formData.get('bucket');
    const name = formData.get('name');
    const file = formData.get('file');

    if (!bucket || !name || !file) {
        return json({ error: 'Missing required fields' }, { status: 400 });
    }

    const metaData = {
        'Content-Type': 'application/octet-stream'
    };

    try {
        const buffer = await file.arrayBuffer();
        const stream = new Readable();
        stream.push(Buffer.from(buffer));
        stream.push(null);

        await minioClient.putObject(bucket, name, stream, metaData);
        return json({ message: 'File uploaded successfully' });
    } catch (error) {
        return json({ error: 'Upload failed', details: error.message }, { status: 500 });
    }
}
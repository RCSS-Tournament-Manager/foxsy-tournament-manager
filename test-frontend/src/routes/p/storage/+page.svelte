<script>
    import { onMount } from "svelte";
    import DataTable from "./data-table.svelte";
    import { listFiles, uploadFile } from "$lib/minio.js";
    import * as Tabs from "$lib/components/ui/tabs";
    import { pushToast } from "$lib/toast";
    import { Button } from "$lib/components/ui/button";
    import { reloadTableSignal } from "$lib/signals";

    let files = [];
    let logs = [];

    

    function handleUpload(bucket) {
        return () => {
            // create a file input element
            const input = document.createElement("input");
            input.type = "file";
            // tar.gz
            input.accept = ".tar.gz";
            input.multiple = true;
            input.onchange = async (e) => {
                const files = e.target.files;
                for (let i = 0; i < files.length; i++) {
                    const file = files[i];
                    // upload the file
                    try {
                        await uploadFile(bucket, file, file.name);

                        pushToast({
                            title: "Success",
                            description: "File uploaded successfully",
                            type: "info",
                        });
                    } catch (e) {
                        console.error(e);
                        pushToast({
                            title: "Error",
                            description: "Failed to upload file",
                            type: "error",
                        });
                    }

                    updateFiles();
                }
            };
            input.click();
        };
    }

    function handleDelete(bucket) {
        return async (file) => {
            try {
                await deleteFile(bucket, file.name);
                pushToast({
                    title: "Success",
                    description: "File deleted successfully",
                    type: "info",
                });
            } catch (e) {
                console.error(e);
                pushToast({
                    title: "Error",
                    description: "Failed to delete file",
                    type: "error",
                });
            }

            updateFiles();
        };
    }

    function updateFiles() {
        listFiles("test").then((result) => {
            files = result;
        });
    }

    onMount(() => {
        updateFiles();
        listFiles("test").then((result) => {
            logs = result;
        });

        reloadTableSignal.subscribe(() => {
            updateFiles();
        });
    });
</script>

<div class="container mx-auto py-10">
    <Tabs.Root value="teams" class="w-full">
        <Tabs.List>
            <Tabs.Trigger value="baseteam">Base Team</Tabs.Trigger>
            <Tabs.Trigger value="gamelog">Game Log</Tabs.Trigger>
            <Tabs.Trigger value="server">Server</Tabs.Trigger>
            <Tabs.Trigger value="teamconfig">Team Config</Tabs.Trigger>
        </Tabs.List>
        <Tabs.Content value="teams">
            <DataTable {files} onUpload={handleUpload("test")} />
        </Tabs.Content>
        <Tabs.Content value="logs">
            <DataTable files={logs} onUpload={handleUpload("test")} />
        </Tabs.Content>
    </Tabs.Root>
</div>

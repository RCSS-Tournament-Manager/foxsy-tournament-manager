<script>
    import DotsHorizontal from "svelte-radix/DotsHorizontal.svelte";
    import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
    import { Button } from "$lib/components/ui/button/index.js";
    import { downloadFile, removeFile } from "$lib/minio.js";
    import {reloadTableSignal} from "$lib/signals.js"

    export let name;

    function handleDownload() {
        downloadFile("test", name);
    }

    export let handleRemove = () => {
        if (confirm(`Are you sure you want to delete the file ${name}?`)) {
            removeFile("test", name).then(() => {
                // Handle UI update or notify the user
                console.log(`File ${name} removed`);
                reloadTableSignal.update(s=> new Date());
            });
        }
    };
</script>

<DropdownMenu.Root>
    <DropdownMenu.Trigger asChild let:builder>
        <Button
            variant="outline"
            size="icon"
            builders={[builder]}
            class="relative h-8 w-8"
        >
            <span class="sr-only">Open menu</span>
            <DotsHorizontal class=" h-[1.2rem] w-[1.2rem] " />
        </Button>
    </DropdownMenu.Trigger>
    <DropdownMenu.Content>
        <DropdownMenu.Group>
            <DropdownMenu.Label>Actions</DropdownMenu.Label>
            <DropdownMenu.Item on:click={handleDownload}>
                Download
            </DropdownMenu.Item>
            <DropdownMenu.Item on:click={handleRemove}>
                Remove
            </DropdownMenu.Item>
        </DropdownMenu.Group>
    </DropdownMenu.Content>
</DropdownMenu.Root>

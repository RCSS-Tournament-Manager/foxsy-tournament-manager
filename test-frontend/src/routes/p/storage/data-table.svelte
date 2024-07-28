<script>
    import {
        Render,
        Subscribe,
        createRender,
        createTable,
    } from "svelte-headless-table";
    import {
        addHiddenColumns,
        addPagination,
        addSelectedRows,
        addSortBy,
        addTableFilter,
    } from "svelte-headless-table/plugins";
    import { writable } from "svelte/store";
    import CaretSort from "svelte-radix/CaretSort.svelte";
    import ChevronDown from "svelte-radix/ChevronDown.svelte";
    import Actions from "./data-table-actions.svelte";
    import DataTableCheckbox from "./data-table-checkbox.svelte";
    import * as Table from "$lib/components/ui/table/index.js";
    import { Button } from "$lib/components/ui/button/index.js";
    import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
    import { cn } from "$lib/utils.js";
    import { Input } from "$lib/components/ui/input/index.js";

    export let files = [];
    export let onUpload = () => {};
    let _filesW = writable(files);
    $: _filesW.set(files);
    const table = createTable(_filesW, {
        sort: addSortBy({ disableMultiSort: true }),
        page: addPagination(),
        filter: addTableFilter({
            fn: ({ filterValue, value }) => value.includes(filterValue),
        }),
        select: addSelectedRows(),
        hide: addHiddenColumns(),
    });

    const columns = table.createColumns([
        table.column({
            header: "Name",
            accessor: "name",
        }),
        table.column({
            header: "Last Modified",
            accessor: "lastModified",
            cell: ({ value }) => {
                return new Date(value).toLocaleString();
            },
        }),
        table.column({
            header: "Size",
            accessor: "size",
            cell: ({ value }) => {
                return `${(value / (1024 * 1024)).toFixed(2)} MB`;
            },
        }),
        table.column({
            header: "Actions",
            accessor: "actions",
            cell: (item) => {
                return createRender(Actions, { name: item.row.original.name });
            },
            plugins: {
                sort: {
                    disable: true,
                },
            },
        }),
    ]);

    const {
        headerRows,
        pageRows,
        tableAttrs,
        tableBodyAttrs,
        flatColumns,
        pluginStates,
        rows,
    } = table.createViewModel(columns);

    const { sortKeys } = pluginStates.sort;

    const { hiddenColumnIds } = pluginStates.hide;
    const ids = flatColumns.map((c) => c.id);
    let hideForId = Object.fromEntries(ids.map((id) => [id, true]));

    $: $hiddenColumnIds = Object.entries(hideForId)
        .filter(([, hide]) => !hide)
        .map(([id]) => id);

    const { hasNextPage, hasPreviousPage, pageIndex } = pluginStates.page;
    const { filterValue } = pluginStates.filter;

    const { selectedDataIds } = pluginStates.select;

    const hideableCols = ["name", "lastModified", "size"];
    let newRowId = null;

    $: if (files.length > $rows.length) {
        newRowId = files[files.length - 1].id;
    }
</script>

<div class="w-full">
    <div class="mb-4 flex items-center gap-4">
        <Input
            class="max-w-sm"
            placeholder="Filter files..."
            type="text"
            bind:value={$filterValue}
        />
        <DropdownMenu.Root>
            <DropdownMenu.Trigger asChild let:builder>
                <!-- upload button -->
                <Button variant="outline" on:click={onUpload}>
                    <span class="sr-only">Upload new file</span>
                    Upload
                </Button>

                <Button variant="outline" class="ml-auto" builders={[builder]}>
                    Columns <ChevronDown class="ml-2 h-4 w-4" />
                </Button>
            </DropdownMenu.Trigger>
            <DropdownMenu.Content>
                {#each flatColumns as col}
                    {#if hideableCols.includes(col.id)}
                        <DropdownMenu.CheckboxItem
                            bind:checked={hideForId[col.id]}
                        >
                            {col.header}
                        </DropdownMenu.CheckboxItem>
                    {/if}
                {/each}
            </DropdownMenu.Content>
        </DropdownMenu.Root>
    </div>
    <div class="rounded-md border">
        <Table.Root {...$tableAttrs}>
            <Table.Header>
                {#each $headerRows as headerRow}
                    <Subscribe rowAttrs={headerRow.attrs()}>
                        <Table.Row>
                            {#each headerRow.cells as cell (cell.id)}
                                <Subscribe
                                    attrs={cell.attrs()}
                                    let:attrs
                                    props={cell.props()}
                                    let:props
                                >
                                    <Table.Head
                                        {...attrs}
                                        class={cn(
                                            "[&:has([role=checkbox])]:pl-3",
                                        )}
                                    >
                                        {#if props.sort.disabled}
                                            <Render of={cell.render()} />
                                        {:else}
                                            <Button
                                                variant="ghost"
                                                on:click={props.sort.toggle}
                                            >
                                                <Render of={cell.render()} />
                                                <CaretSort
                                                    class={cn(
                                                        $sortKeys[0]?.id ===
                                                            cell.id &&
                                                            "text-foreground",
                                                        "ml-2 h-4 w-4",
                                                    )}
                                                />
                                            </Button>
                                        {/if}
                                    </Table.Head>
                                </Subscribe>
                            {/each}
                        </Table.Row>
                    </Subscribe>
                {/each}
            </Table.Header>

            <Table.Body {...$tableBodyAttrs}>
                {#each $pageRows as row (row.id)}
                    <Subscribe rowAttrs={row.attrs()} let:rowAttrs>
                        <Table.Row
                            {...rowAttrs}
                            class={row.id === newRowId ? "flash" : ""}
                            data-state={$selectedDataIds[row.id] && "selected"}
                        >
                            {#each row.cells as cell (cell.id)}
                                <Subscribe attrs={cell.attrs()} let:attrs>
                                    <Table.Cell
                                        class="[&:has([role=checkbox])]:pl-3"
                                        {...attrs}
                                    >
                                        <Render of={cell.render()} />
                                    </Table.Cell>
                                </Subscribe>
                            {/each}
                        </Table.Row>
                    </Subscribe>
                {/each}
            </Table.Body>
        </Table.Root>
    </div>
    <div class="flex items-center justify-end space-x-2 py-4">
        <div class="flex-1 text-sm text-muted-foreground">
            {Object.keys($selectedDataIds).length} of {$rows.length} row(s) selected.
        </div>
        <Button
            variant="outline"
            size="sm"
            on:click={() => ($pageIndex = $pageIndex - 1)}
            disabled={!$hasPreviousPage}>Previous</Button
        >
        <Button
            variant="outline"
            size="sm"
            disabled={!$hasNextPage}
            on:click={() => ($pageIndex = $pageIndex + 1)}>Next</Button
        >
    </div>
</div>

<style>
    @keyframes flash {
        0% {
            background-color: yellow;
        }
        100% {
            background-color: transparent;
        }
    }

    .flash {
        animation: flash 1s ease-in-out;
    }
</style>

<script>
    import Sun from "svelte-radix/Sun.svelte";
    import Moon from "svelte-radix/Moon.svelte";
    import { toggleMode } from "mode-watcher";
    import { Button } from "$lib/components/ui/button/index.js";
    import { page } from "$app/stores";
    import { cn } from "$lib/utils.js";
    import {
        connectionStateStore,
        connect,
        disconnect,
        credentialsStore,
    } from "$lib/stomp.js";
    import { DotFilled, Dot } from "svelte-radix";
    import * as Popover from "$lib/components/ui/popover";
    import { Input } from "$lib/components/ui/input/index.js";

    let routes = [
        {
            name: "Build",
            path: "/p/build",
        },
        {
            name: "Run Games",
            path: "/p/run",
        },
        {
            name: "Storage",
            path: "/p/storage",
        },
        {
            name: "Manual",
            path: "/p/manual",
        },
    ];
    let websiteTitle = "Foxsy Test Tournament Manager";

    let credentials;
    credentialsStore.subscribe((value) => {
        credentials = value;
    });

    let connectionState;
    connectionStateStore.subscribe((value) => {
        connectionState = value;
    });

    function handleConnect() {
        credentialsStore.update((_) => credentials);
        connect($credentialsStore);
    }
</script>

<div class="flex flex-row justify-between p-4 border-b">
    <div class="container flex flex-row justify-between">
        <div class="flex flex-row">
            <a href="/" class="mr-6 flex items-center space-x-2">
                <span class="font-bold sm:inline-block"> 
                    {websiteTitle}
                </span>
            </a>
            <nav class="flex items-center gap-6 text-sm">
                {#each routes as { name, path }}
                    <a
                        href={path}
                        class={cn(
                            "transition-colors hover:text-foreground/80",
                            $page.url.pathname.startsWith(path)
                                ? "text-foreground"
                                : "text-foreground/60",
                        )}
                    >
                        {name}
                    </a>
                {/each}
            </nav>
        </div>
        <div class="flex items-center space-x-4">
            <Popover.Root>
                <Popover.Trigger>
                    {#if connectionState === "connected"}
                        <DotFilled class="text-green-500" />
                    {:else if connectionState === "connecting"}
                        <Dot class="animate-ping text-yellow-500" />
                    {:else if connectionState === "failed"}
                        <DotFilled class="text-red-500" />
                    {:else}
                        <Dot class="text-gray-500" />
                    {/if}
                </Popover.Trigger>
                <Popover.Content class="p-4 shadow-lg rounded-lg">
                    <div class="flex flex-col space-y-2">
                        {#if connectionState === "connected"}
                            <p>RabbitMQ is connected</p>
                        {:else if connectionState === "connecting"}
                            <p>Connecting to RabbitMQ</p>
                        {:else if connectionState === "failed"}
                            <p>RabbitMQ connection failed</p>
                        {:else if connectionState === "disconnected"}
                            <p>RabbitMQ is disconnected</p>
                        {:else if connectionState === "init"}
                            <p>RabbitMQ is initializing</p>
                        {/if}

                        {#if connectionState !== "connected"}
                            <Input
                                type="text"
                                placeholder="Username"
                                bind:value={credentials.username}
                                class="max-w-xs"
                            />
                            <Input
                                type="password"
                                placeholder="Password"
                                bind:value={credentials.password}
                                class="max-w-xs"
                            />
                            <Input
                                type="text"
                                placeholder="Host"
                                bind:value={credentials.host}
                                class="max-w-xs"
                            />
                            <label class="flex items-center space-x-2">
                                <input
                                    type="checkbox"
                                    bind:checked={credentials.remember}
                                />
                                <span>Remember</span>
                            </label>
                            <Button on:click={handleConnect}>Connect</Button>
                        {:else if connectionState === "connected"}
                            <Button on:click={disconnect}>Disconnect</Button>
                        {/if}
                    </div>
                </Popover.Content>
            </Popover.Root>
            <Button on:click={toggleMode} variant="outline" size="icon">
                <Sun
                    class="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0"
                />
                <Moon
                    class="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100"
                />
                <span class="sr-only">Toggle theme</span>
            </Button>
        </div>
    </div>
</div>

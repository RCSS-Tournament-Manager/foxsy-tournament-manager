<script>
    import { onMount } from 'svelte';
    import { toasts } from '$lib/toast';
    import { fly } from 'svelte/transition';
    import * as Alert from "$lib/components/ui/alert";

    let toastList = [];

    onMount(() => {
        const unsubscribe = toasts.subscribe(value => {
            toastList = value;
        });

        return () => {
            unsubscribe();
        };
    });
</script>

<style>
    .toast-container {
        position: fixed;
        bottom: 1rem;
        right: 1rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        z-index: 9999;
    }
</style>

<div class="toast-container">
    {#each toastList as toast (toast.id)}
        <div class="toast" in:fly={{ y: 50, duration: 300 }} out:fly={{ y: 50, duration: 300 }}>
            <Alert.Root variant="{toast.type === 'error' ? 'destructive' : 'default'}">
                {#if toast.icon}
                    <img src={toast.icon} alt="icon" />
                {/if}
                <Alert.Title>{toast.title}</Alert.Title>
                <Alert.Description>{toast.description}</Alert.Description>
            </Alert.Root>
        </div>
    {/each}
</div>
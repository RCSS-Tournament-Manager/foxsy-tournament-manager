<script>
    import * as Alert from "$lib/components/ui/alert";
    import Header from "./Header.svelte";
    import ToastComponent from "$lib/components/ToastComponent.svelte";
    import { toasts } from "$lib/toast";
</script>

<div></div>

<main>
    <ToastComponent {toasts} />
    <Header />
    <div class="content"> 
    <slot />
    </div>
</main>


<style>
    .content{
        height: calc(100vh - 70px);
    }
</style>
<script>
	import { Checkbox } from "$lib/components/ui/checkbox/index.js";

	export let checked;
</script>

<Checkbox bind:checked={$checked} />

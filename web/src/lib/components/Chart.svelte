<script lang="ts">
	import { onMount } from 'svelte';
	import type { Chart, ChartConfiguration } from 'chart.js';

	interface Props {
		config: ChartConfiguration;
	}

	let { config }: Props = $props();

	let canvas: HTMLCanvasElement;
	let chart: Chart | null = null;

	onMount(async () => {
		// Dynamic import to avoid SSR issues
		const ChartJS = await import('chart.js/auto');
		
		if (canvas) {
			chart = new ChartJS.default(canvas, config);
		}

		return () => {
			if (chart) {
				chart.destroy();
			}
		};
	});

	// Update chart when config changes
	$effect(() => {
		if (chart && config) {
			chart.data = config.data!;
			chart.options = config.options!;
			chart.update();
		}
	});
</script>

<canvas bind:this={canvas}></canvas>


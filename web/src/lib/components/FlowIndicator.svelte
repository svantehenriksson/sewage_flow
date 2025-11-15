<script lang="ts">
	interface Props {
		label: string;
		value: number;
		unit?: string;
		color?: string;
		isInflow?: boolean;
	}

	let { label, value, unit = 'm³/h', color = 'blue', isInflow = false }: Props = $props();

	let colorClasses = $derived(
		color === 'blue'
			? 'text-blue-600 bg-blue-50 border-blue-300'
			: color === 'red'
				? 'text-red-600 bg-red-50 border-red-300'
				: 'text-green-600 bg-green-50 border-green-300'
	);
</script>

<div class="flex flex-col items-center">
	<div class="mb-2 text-sm font-semibold text-gray-700">{label}</div>
	<div class="relative">
		<!-- Arrow -->
		<svg class="h-20 w-12" viewBox="0 0 50 100">
			{#if isInflow}
				<!-- Downward arrow for inflow -->
				<defs>
					<marker
						id="arrowhead-down"
						markerWidth="10"
						markerHeight="10"
						refX="5"
						refY="5"
						orient="auto"
					>
						<polygon points="0 0, 10 5, 0 10" fill={color === 'blue' ? '#3b82f6' : '#22c55e'} />
					</marker>
				</defs>
				<line
					x1="25"
					y1="10"
					x2="25"
					y2="80"
					stroke={color === 'blue' ? '#3b82f6' : '#22c55e'}
					stroke-width="4"
					marker-end="url(#arrowhead-down)"
					class="animate-pulse"
				/>
			{:else}
				<!-- Upward arrow for outflow -->
				<defs>
					<marker
						id="arrowhead-up"
						markerWidth="10"
						markerHeight="10"
						refX="5"
						refY="5"
						orient="auto"
					>
						<polygon points="0 0, 10 5, 0 10" fill={color === 'red' ? '#ef4444' : '#3b82f6'} />
					</marker>
				</defs>
				<line
					x1="25"
					y1="80"
					x2="25"
					y2="10"
					stroke={color === 'red' ? '#ef4444' : '#3b82f6'}
					stroke-width="4"
					marker-end="url(#arrowhead-up)"
					class="animate-pulse"
				/>
			{/if}
		</svg>
	</div>
	<div class="rounded-lg border-2 px-4 py-2 {colorClasses}">
		<div class="text-center text-2xl font-bold">
			{value.toFixed(1)}
		</div>
		<div class="text-center text-xs">{unit}</div>
	</div>
</div>


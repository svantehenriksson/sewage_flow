<script lang="ts">
	interface Props {
		label: string;
		flow: number;
		power: number;
		frequency: number;
		isActive: boolean;
		isHighCapacity: boolean;
	}

	let { label, flow, power, frequency, isActive, isHighCapacity }: Props = $props();
</script>

<div
	class="flex flex-col items-center rounded-lg border-2 p-3 transition-all duration-300 {isActive
		? 'border-green-500 bg-green-50'
		: 'border-gray-300 bg-gray-50'}"
	class:shadow-lg={isActive}
	style="min-width: 140px; width: 140px;"
>
	<div class="mb-1 text-xs font-bold text-gray-700">
		{label}
		{isHighCapacity ? '(HC)' : '(LC)'}
	</div>

	<!-- Pump icon -->
	<svg class="h-12 w-12" viewBox="0 0 100 100">
		<circle
			cx="50"
			cy="50"
			r="35"
			fill={isActive ? '#22c55e' : '#d1d5db'}
			class="transition-colors duration-300"
		/>
		{#if isActive}
			<circle cx="50" cy="50" r="35" fill="#22c55e" opacity="0.3" class="animate-ping" />
		{/if}
		<path
			d="M 50 25 L 65 50 L 50 50 L 65 75 M 50 25 L 35 50 L 50 50 L 35 75"
			stroke="white"
			stroke-width="3"
			fill="none"
		/>
	</svg>

	<div class="mt-2 w-full text-xs" style="height: 60px;">
		{#if isActive}
			<div class="space-y-1">
				<div class="flex justify-between">
					<span class="text-gray-600">Flow:</span>
					<span class="font-semibold text-blue-600">{flow.toFixed(1)} m³/h</span>
				</div>
				<div class="flex justify-between">
					<span class="text-gray-600">Power:</span>
					<span class="font-semibold text-orange-600">{power.toFixed(1)} kW</span>
				</div>
				<div class="flex justify-between">
					<span class="text-gray-600">Freq:</span>
					<span class="font-semibold text-purple-600">{frequency.toFixed(1)} Hz</span>
				</div>
			</div>
		{:else}
			<div class="flex h-full items-center justify-center font-semibold text-gray-500">OFF</div>
		{/if}
	</div>
</div>


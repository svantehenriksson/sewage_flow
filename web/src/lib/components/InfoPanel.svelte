<script lang="ts">
	interface Props {
		electricityPriceHigh: number;
		electricityPriceNormal: number;
		weather?: string;
	}

	let { electricityPriceHigh, electricityPriceNormal, weather = 'Clear' }: Props = $props();
</script>

<div class="absolute right-4 top-4 rounded-lg border-2 border-gray-300 bg-white p-4 shadow-lg">
	<h3 class="mb-2 text-sm font-bold text-gray-800">Current Info</h3>

	<div class="mb-3 space-y-2">
		<div class="flex items-center justify-between">
			<span class="text-xs text-gray-600">⚡ High:</span>
			<span class="font-semibold text-orange-600">{electricityPriceHigh.toFixed(3)} €/kWh</span>
		</div>
		<div class="flex items-center justify-between">
			<span class="text-xs text-gray-600">⚡ Normal:</span>
			<span class="font-semibold text-green-600">{electricityPriceNormal.toFixed(3)} €/kWh</span>
		</div>
	</div>

	<div class="border-t border-gray-200 pt-2">
		<div class="flex items-center justify-between">
			<span class="text-xs text-gray-600">🌤️ Weather:</span>
			<span class="font-semibold text-blue-600">{weather}</span>
		</div>
	</div>
</div>


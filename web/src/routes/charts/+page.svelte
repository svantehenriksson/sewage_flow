<script lang="ts">
	import OptimizationCharts from '$lib/components/OptimizationCharts.svelte';
	import optimizationResult from '$lib/data/optimization_result.json';
</script>

<div class="min-h-screen bg-gradient-to-br from-blue-50 to-gray-100 p-6">
	<div class="mx-auto max-w-7xl space-y-6">
		<!-- Header -->
		<div class="flex items-center justify-between">
			<h1 class="text-4xl font-bold text-gray-800">Optimization Analysis</h1>
			<a
				href="/"
				class="rounded-lg bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700"
			>
				← Back to Simulation
			</a>
		</div>

		<!-- Summary Stats -->
		<div
			class="grid grid-cols-1 gap-4 rounded-lg border-2 border-gray-300 bg-white p-6 shadow-lg md:grid-cols-4"
		>
			<div class="text-center">
				<div class="text-sm text-gray-600">Total Cost</div>
				<div class="text-2xl font-bold text-green-600">
					€{optimizationResult.total_cost_eur.toFixed(2)}
				</div>
			</div>
			<div class="text-center">
				<div class="text-sm text-gray-600">Initial Water Level</div>
				<div class="text-2xl font-bold text-blue-600">
					{optimizationResult.initial_water_level_m.toFixed(2)} m
				</div>
			</div>
			<div class="text-center">
				<div class="text-sm text-gray-600">Initial Volume</div>
				<div class="text-2xl font-bold text-purple-600">
					{optimizationResult.initial_volume_m3.toFixed(0)} m³
				</div>
			</div>
			<div class="text-center">
				<div class="text-sm text-gray-600">Time Intervals</div>
				<div class="text-2xl font-bold text-orange-600">
					{optimizationResult.schedule.length} × 15min
				</div>
			</div>
		</div>

		<!-- Charts -->
		<OptimizationCharts
			schedule={optimizationResult.schedule}
			totalCost={optimizationResult.total_cost_eur}
		/>
	</div>
</div>


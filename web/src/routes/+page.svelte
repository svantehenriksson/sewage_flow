<script lang="ts">
	import { onDestroy } from 'svelte';
	import type { TimelineData } from '$lib/types';
	import { optimizationData } from './optimizationData';
	import WaterTank from '$lib/components/WaterTank.svelte';
	import PumpGroup from '$lib/components/PumpGroup.svelte';
	import FlowIndicator from '$lib/components/FlowIndicator.svelte';
	import Timeline from '$lib/components/Timeline.svelte';

	let currentIndex = $state(0);
	let isPlaying = $state(false);
	let intervalId: number | null = null;

	let timelineData = $state<TimelineData[]>(optimizationData);
	let currentData = $derived(timelineData[currentIndex]);

	// Pump data for Group 1
	let group1Pumps = $derived([
		{
			label: 'P11',
			flow: currentData.pumpFlow11,
			power: currentData.pumpPower11,
			frequency: currentData.pumpFrequency11,
			isHighCapacity: true
		},
		{
			label: 'P12',
			flow: currentData.pumpFlow12,
			power: currentData.pumpPower12,
			frequency: currentData.pumpFrequency12,
			isHighCapacity: true
		},
		{
			label: 'P13',
			flow: currentData.pumpFlow13,
			power: currentData.pumpPower13,
			frequency: currentData.pumpFrequency13,
			isHighCapacity: true
		},
		{
			label: 'P14',
			flow: currentData.pumpFlow14,
			power: currentData.pumpPower14,
			frequency: currentData.pumpFrequency14,
			isHighCapacity: false
		}
	]);

	// Pump data for Group 2
	let group2Pumps = $derived([
		{
			label: 'P21',
			flow: currentData.pumpFlow21,
			power: currentData.pumpPower21,
			frequency: currentData.pumpFrequency21,
			isHighCapacity: true
		},
		{
			label: 'P22',
			flow: currentData.pumpFlow22,
			power: currentData.pumpPower22,
			frequency: currentData.pumpFrequency22,
			isHighCapacity: true
		},
		{
			label: 'P23',
			flow: currentData.pumpFlow23,
			power: currentData.pumpPower23,
			frequency: currentData.pumpFrequency23,
			isHighCapacity: true
		},
		{
			label: 'P24',
			flow: currentData.pumpFlow24,
			power: currentData.pumpPower24,
			frequency: currentData.pumpFrequency24,
			isHighCapacity: false
		}
	]);

	function handleIndexChange(newIndex: number) {
		currentIndex = newIndex;
	}

	function handlePlayPause() {
		isPlaying = !isPlaying;
	}

	// Auto-play functionality
	$effect(() => {
		if (isPlaying) {
			intervalId = window.setInterval(() => {
				if (currentIndex < timelineData.length - 1) {
					currentIndex++;
				} else {
					// Loop back to start
					currentIndex = 0;
				}
			}, 250); // Update every second
		} else {
			if (intervalId !== null) {
				clearInterval(intervalId);
				intervalId = null;
			}
		}

		return () => {
			if (intervalId !== null) {
				clearInterval(intervalId);
			}
		};
	});

	onDestroy(() => {
		if (intervalId !== null) {
			clearInterval(intervalId);
		}
	});
</script>

<div class="bg-linear-to-br from-blue-50 to-gray-100 p-4">
	<div class="mx-auto max-w-7xl space-y-3">
		<!-- Title and Navigation -->
		<div class="flex items-center justify-between gap-4">
			<h1 class="text-3xl font-bold text-gray-800">Pumping Station Flow Diagram</h1>
			<div class="flex items-center gap-3">
				<!-- Info Panel -->
				<div class="rounded-lg border-2 border-gray-300 bg-white px-3 py-2 shadow-lg">
					<div class="flex items-center gap-3">
						<span class="text-xs text-gray-600">⚡ Price:</span>
						<span class="font-semibold text-green-600"
							>{currentData.electricityPrice2Normal.toFixed(3)} c/kWh</span
						>
					</div>
				</div>
				<a
					href="/charts"
					class="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white transition-colors hover:bg-blue-700"
				>
					View Analysis Charts →
				</a>
			</div>
		</div>

		<!-- Timeline -->
		<Timeline
			{currentIndex}
			totalPoints={timelineData.length}
			currentDate={currentData.date}
			{isPlaying}
			onIndexChange={handleIndexChange}
			onPlayPause={handlePlayPause}
		/>

		<!-- Main Diagram -->
		<div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
			<!-- Left Column: Pump Group 1 -->
			<div class="flex flex-col items-center justify-center space-y-3">
				<PumpGroup groupName="Pump Group 1" pumps={group1Pumps} />
			</div>

			<!-- Center Column: Water Tank and Flow -->
			<div class="flex flex-col items-center justify-center space-y-3">
				<!-- Inflow -->
				<FlowIndicator
					label="Water Inflow"
					value={currentData.waterInflow}
					color="green"
					isInflow={true}
				/>

				<!-- Water Tank -->
				<WaterTank waterLevel={currentData.waterLevel} waterVolume={currentData.waterVolume} />

				<!-- Outflow -->
				<FlowIndicator
					label="Total Pumped Flow"
					value={currentData.totalPumpedFlow}
					color="red"
					isInflow={false}
				/>
			</div>

			<!-- Right Column: Pump Group 2 -->
			<div class="flex flex-col items-center justify-center space-y-3">
				<PumpGroup groupName="Pump Group 2" pumps={group2Pumps} />
			</div>
		</div>

		<!-- Statistics Panel -->
		<div
			class="mx-auto grid max-w-4xl grid-cols-1 gap-4 rounded-lg border-2 border-gray-300 bg-white p-4 shadow-lg md:grid-cols-3"
		>
			<div class="text-center">
				<div class="text-sm text-gray-600">Active Pumps</div>
				<div class="text-3xl font-bold text-green-600">
					{[...group1Pumps, ...group2Pumps].filter((p) => p.flow > 0).length}
				</div>
			</div>
			<div class="text-center">
				<div class="text-sm text-gray-600">Total Power Consumption</div>
				<div class="text-3xl font-bold text-orange-600">
					{(
						currentData.pumpPower11 +
						currentData.pumpPower12 +
						currentData.pumpPower13 +
						currentData.pumpPower14 +
						currentData.pumpPower21 +
						currentData.pumpPower22 +
						currentData.pumpPower23 +
						currentData.pumpPower24
					).toFixed(1)} kW
				</div>
			</div>
			<div class="text-center">
				<div class="text-sm text-gray-600">Net Flow Rate</div>
				<div class="text-3xl font-bold text-blue-600">
					{(currentData.waterInflow - currentData.totalPumpedFlow).toFixed(1)} m³/h
				</div>
			</div>
		</div>
	</div>
</div>

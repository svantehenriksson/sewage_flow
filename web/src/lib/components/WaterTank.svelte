<script lang="ts">
	interface Props {
		waterLevel: number; // in meters, 0-8
		waterVolume: number;
	}

	let { waterLevel, waterVolume }: Props = $props();

	// Convert water level to percentage (0-8m becomes 0-100%)
	let waterPercentage = $derived((waterLevel / 8) * 100);
</script>

<div class="flex flex-col items-center">
	<h3 class="mb-2 text-lg font-semibold">Water Tank</h3>
	<div class="relative h-64 w-64">
		<!-- Tank outline (circle) -->
		<svg class="h-full w-full" viewBox="0 0 200 200">
			<!-- Background circle -->
			<circle
				cx="100"
				cy="100"
				r="90"
				fill="none"
				stroke="#374151"
				stroke-width="4"
				class="dark:stroke-gray-600"
			/>

			<!-- Water fill (clipped circle) -->
			<defs>
				<clipPath id="water-clip">
					<circle cx="100" cy="100" r="88" />
				</clipPath>
			</defs>

			<g clip-path="url(#water-clip)">
				<rect
					x="10"
					y={200 - (waterPercentage / 100) * 180}
					width="180"
					height={(waterPercentage / 100) * 180}
					fill="#3b82f6"
					class="transition-all duration-500"
					opacity="0.7"
				/>
				<!-- Water surface with wave effect -->
				<path
					d="M 10 {200 - (waterPercentage / 100) * 180} Q 55 {200 - (waterPercentage / 100) * 180 - 3} 100 {200 - (waterPercentage / 100) * 180} T 190 {200 - (waterPercentage / 100) * 180}"
					fill="#60a5fa"
					opacity="0.9"
					class="transition-all duration-500"
				/>
			</g>

			<!-- Level markers -->
			{#each [0, 2, 4, 6, 8] as level}
				<line
					x1="15"
					y1={200 - (level / 8) * 180}
					x2="30"
					y2={200 - (level / 8) * 180}
					stroke="#9ca3af"
					stroke-width="2"
				/>
				<text
					x="5"
					y={205 - (level / 8) * 180}
					font-size="12"
					fill="#6b7280"
					text-anchor="end"
				>
					{level}m
				</text>
			{/each}
		</svg>
	</div>
	<div class="mt-2 text-center">
		<div class="text-2xl font-bold text-blue-600">
			{waterLevel.toFixed(2)}m
		</div>
		<div class="text-sm text-gray-600">
			{waterVolume.toFixed(1)} m³
		</div>
	</div>
</div>


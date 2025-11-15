<script lang="ts">
	interface Props {
		currentIndex: number;
		totalPoints: number;
		currentDate: Date;
		isPlaying: boolean;
		onIndexChange: (index: number) => void;
		onPlayPause: () => void;
	}

	let { currentIndex, totalPoints, currentDate, isPlaying, onIndexChange, onPlayPause }: Props =
		$props();

	let progress = $derived((currentIndex / Math.max(totalPoints - 1, 1)) * 100);

	function formatDate(date: Date): string {
		return date.toLocaleString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function handleSliderChange(event: Event) {
		const target = event.target as HTMLInputElement;
		onIndexChange(parseInt(target.value));
	}
</script>

<div class="w-full rounded-lg border-2 border-gray-300 bg-white p-4 shadow-md">
	<div class="mb-3 flex items-center justify-between">
		<h2 class="text-xl font-bold text-gray-800">Timeline</h2>
		<div class="text-lg font-semibold text-blue-600">
			{formatDate(currentDate)}
		</div>
	</div>

	<div class="mb-3 flex items-center gap-4">
		<!-- Play/Pause button -->
		<button
			onclick={onPlayPause}
			class="flex h-12 w-12 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg transition-all hover:bg-blue-700 active:scale-95"
		>
			{#if isPlaying}
				<!-- Pause icon -->
				<svg class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
					<path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
				</svg>
			{:else}
				<!-- Play icon -->
				<svg class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
					<path d="M8 5v14l11-7z" />
				</svg>
			{/if}
		</button>

		<!-- Timeline slider -->
		<div class="flex-1">
			<div class="relative">
				<input
					type="range"
					min="0"
					max={totalPoints - 1}
					value={currentIndex}
					oninput={handleSliderChange}
					class="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200"
					style="background: linear-gradient(to right, #3b82f6 0%, #3b82f6 {progress}%, #e5e7eb {progress}%, #e5e7eb 100%)"
				/>
			</div>
			<div class="mt-1 flex justify-between text-xs text-gray-600">
				<span>Point {currentIndex + 1} of {totalPoints}</span>
				<span>{progress.toFixed(1)}%</span>
			</div>
		</div>
	</div>
</div>

<style>
	input[type='range']::-webkit-slider-thumb {
		appearance: none;
		width: 20px;
		height: 20px;
		border-radius: 50%;
		background: #3b82f6;
		cursor: pointer;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
	}

	input[type='range']::-moz-range-thumb {
		width: 20px;
		height: 20px;
		border-radius: 50%;
		background: #3b82f6;
		cursor: pointer;
		border: none;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
	}
</style>


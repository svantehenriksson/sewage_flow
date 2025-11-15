<script lang="ts">
	import Pump from './Pump.svelte';

	interface Props {
		groupName: string;
		pumps: Array<{
			label: string;
			flow: number;
			power: number;
			frequency: number;
			isHighCapacity: boolean;
		}>;
	}

	let { groupName, pumps }: Props = $props();
</script>

<div class="rounded-lg border-2 border-gray-300 bg-white p-4 shadow-md">
	<h3 class="mb-3 text-center text-lg font-bold text-gray-800">{groupName}</h3>
	<div class="grid grid-cols-2 gap-3">
		{#each pumps as pump}
			<Pump
				label={pump.label}
				flow={pump.flow}
				power={pump.power}
				frequency={pump.frequency}
				isActive={pump.flow > 0}
				isHighCapacity={pump.isHighCapacity}
			/>
		{/each}
	</div>
</div>


<script lang="ts">
	import Chart from './Chart.svelte';
	import type { ChartConfiguration } from 'chart.js';

	interface Props {
		schedule: any[];
		totalCost: number;
	}

	let { schedule, totalCost }: Props = $props();

	// Extract data from schedule
	let intervals = $derived(schedule.map((item, idx) => idx));
	let waterLevels = $derived([
		...schedule.map((item) => item.water_level_start_m),
		schedule[schedule.length - 1]?.water_level_end_m || 0
	]);
	let volumes = $derived([
		...schedule.map((item) => item.volume_start_m3),
		schedule[schedule.length - 1]?.volume_end_m3 || 0
	]);
	let inflows = $derived(schedule.map((item) => item.inflow_m3));
	let outflows = $derived(schedule.map((item) => item.outflow_m3));
	let prices = $derived(
		schedule.map(
			(item) => item.electricity_price_eur_per_kwh || item.electricity_price_cents_per_kwh / 100.0
		)
	);
	let costs = $derived(schedule.map((item) => item.interval_cost_eur));

	// Extract pump schedules
	const pumpNames = ['1.1', '1.2', '1.3', '1.4', '2.1', '2.2', '2.3', '2.4'];
	const pumpColors = {
		'1.1': '#FF6B6B',
		'1.2': '#4ECDC4',
		'1.3': '#45B7D1',
		'1.4': '#96CEB4',
		'2.1': '#FFEAA7',
		'2.2': '#DFE6E9',
		'2.3': '#74B9FF',
		'2.4': '#A29BFE'
	};

	let pumpSchedules = $derived.by(() => {
		const schedules: Record<string, number[]> = {};
		pumpNames.forEach((pump) => {
			schedules[pump] = schedule.map((item) => (item.active_pumps.includes(pump) ? 1 : 0));
		});
		return schedules;
	});

	// Chart 1: Water Level and Volume
	let waterLevelConfig = $derived<ChartConfiguration>({
		type: 'line',
		data: {
			labels: [...intervals, intervals.length],
			datasets: [
				{
					label: 'Water Level (m)',
					data: waterLevels,
					borderColor: 'rgb(59, 130, 246)',
					backgroundColor: 'rgba(59, 130, 246, 0.3)',
					fill: true,
					yAxisID: 'y',
					tension: 0.1
				},
				{
					label: 'Volume (m³)',
					data: volumes,
					borderColor: 'rgb(34, 197, 94)',
					backgroundColor: 'rgba(34, 197, 94, 0.1)',
					borderDash: [5, 5],
					fill: false,
					yAxisID: 'y1',
					tension: 0.1
				}
			]
		},
		options: {
			responsive: true,
			maintainAspectRatio: false,
			interaction: {
				mode: 'index',
				intersect: false
			},
			plugins: {
				title: {
					display: true,
					text: `Water Level and Volume - Total Cost: €${totalCost.toFixed(2)}`,
					font: { size: 16, weight: 'bold' }
				},
				legend: {
					position: 'top'
				},
				tooltip: {
					callbacks: {
						label: function (context) {
							const label = context.dataset.label || '';
							const value = context.parsed!.y.toFixed(2);
							return `${label}: ${value}`;
						}
					}
				}
			},
			scales: {
				x: {
					title: {
						display: true,
						text: 'Time Interval (15 min each)'
					},
					ticks: {
						callback: function (value) {
							const num = Number(value);
							if (num % 12 === 0) {
								return `${num / 4}h`;
							}
							return '';
						}
					}
				},
				y: {
					type: 'linear',
					display: true,
					position: 'left',
					title: {
						display: true,
						text: 'Water Level (m)'
					},
					min: 0,
					max: 8
				},
				y1: {
					type: 'linear',
					display: true,
					position: 'right',
					title: {
						display: true,
						text: 'Volume (m³)'
					},
					grid: {
						drawOnChartArea: false
					}
				}
			}
		}
	});

	// Chart 2: Pump Schedule (Stacked Area)
	let pumpScheduleConfig = $derived<ChartConfiguration>({
		type: 'line',
		data: {
			labels: intervals,
			datasets: pumpNames.map((pump) => ({
				label: `Pump ${pump}`,
				data: pumpSchedules[pump],
				backgroundColor: pumpColors[pump as keyof typeof pumpColors],
				borderColor: pumpColors[pump as keyof typeof pumpColors],
				fill: true,
				tension: 0
			}))
		},
		options: {
			responsive: true,
			maintainAspectRatio: false,
			interaction: {
				mode: 'index',
				intersect: false
			},
			plugins: {
				title: {
					display: true,
					text: 'Pump Schedule (Stacked)',
					font: { size: 14, weight: 'bold' }
				},
				legend: {
					position: 'top',
					labels: {
						boxWidth: 12,
						font: { size: 10 }
					}
				}
			},
			scales: {
				x: {
					title: {
						display: true,
						text: 'Time Interval'
					},
					ticks: {
						callback: function (value) {
							const num = Number(value);
							if (num % 12 === 0) {
								return `${num / 4}h`;
							}
							return '';
						}
					}
				},
				y: {
					stacked: true,
					title: {
						display: true,
						text: 'Active Pumps'
					}
				}
			}
		}
	});

	// Chart 2b: Individual Pump Schedules (Gantt-style Timeline)
	let pumpTimelineData = $derived.by(() => {
		const allSegments: any[] = [];
		
		pumpNames.forEach((pump, pumpIdx) => {
			const scheduleData = pumpSchedules[pump];
			let start: number | null = null;
			let segmentCount = 0;
			
			for (let i = 0; i <= scheduleData.length; i++) {
				if (i < scheduleData.length && scheduleData[i] && start === null) {
					start = i;
				} else if ((i >= scheduleData.length || !scheduleData[i]) && start !== null) {
					// Create a dataset for this segment
					allSegments.push({
						label: `Pump ${pump} - Segment ${segmentCount}`,
						data: [
							{ x: [start, i], y: pumpIdx }
						],
						backgroundColor: pumpColors[pump as keyof typeof pumpColors],
						borderColor: '#000',
						borderWidth: 0.5,
						barThickness: 15,
						pumpName: pump,
						segmentStart: start,
						segmentEnd: i
					});
					start = null;
					segmentCount++;
				}
			}
		});
		
		return allSegments;
	});

	// Chart 3: Electricity Price
	let priceConfig = $derived<ChartConfiguration>({
		type: 'line',
		data: {
			labels: intervals,
			datasets: [
				{
					label: 'Electricity Price (€/kWh)',
					data: prices,
					borderColor: 'rgb(59, 130, 246)',
					backgroundColor: 'rgba(59, 130, 246, 0.4)',
					fill: true,
					tension: 0.1
				}
			]
		},
		options: {
			responsive: true,
			maintainAspectRatio: false,
			plugins: {
				title: {
					display: true,
					text: 'Electricity Price',
					font: { size: 14, weight: 'bold' }
				},
				legend: {
					position: 'top'
				}
			},
			scales: {
				x: {
					title: {
						display: true,
						text: 'Time Interval'
					},
					ticks: {
						callback: function (value) {
							const num = Number(value);
							if (num % 12 === 0) {
								return `${num / 4}h`;
							}
							return '';
						}
					}
				},
				y: {
					title: {
						display: true,
						text: 'Price (€/kWh)'
					}
				}
			}
		}
	});

	// Chart 4: Flow and Cost
	let flowConfig = $derived<ChartConfiguration>({
		type: 'bar',
		data: {
			labels: intervals,
			datasets: [
				{
					label: 'Inflow (m³)',
					data: inflows,
					backgroundColor: 'rgba(34, 197, 94, 0.7)',
					yAxisID: 'y'
				},
				{
					label: 'Outflow (m³)',
					data: outflows.map((o) => -o),
					backgroundColor: 'rgba(239, 68, 68, 0.7)',
					yAxisID: 'y'
				}
			]
		},
		options: {
			responsive: true,
			maintainAspectRatio: false,
			interaction: {
				mode: 'index',
				intersect: false
			},
			plugins: {
				title: {
					display: true,
					text: 'Water Inflow vs Outflow',
					font: { size: 14, weight: 'bold' }
				},
				legend: {
					position: 'top'
				}
			},
			scales: {
				x: {
					title: {
						display: true,
						text: 'Time Interval (15 min each)'
					},
					ticks: {
						callback: function (value) {
							const num = Number(value);
							if (num % 12 === 0) {
								return `${num / 4}h`;
							}
							return '';
						}
					}
				},
				y: {
					title: {
						display: true,
						text: 'Flow (m³/15min)'
					}
				}
			}
		}
	});

	// Chart 5: Cost over time
	let costConfig = $derived<ChartConfiguration>({
		type: 'line',
		data: {
			labels: intervals,
			datasets: [
				{
					label: 'Interval Cost (€)',
					data: costs,
					borderColor: 'rgb(249, 115, 22)',
					backgroundColor: 'rgba(249, 115, 22, 0.3)',
					fill: true,
					tension: 0.1
				}
			]
		},
		options: {
			responsive: true,
			maintainAspectRatio: false,
			plugins: {
				title: {
					display: true,
					text: 'Cost per Interval',
					font: { size: 14, weight: 'bold' }
				},
				legend: {
					position: 'top'
				}
			},
			scales: {
				x: {
					title: {
						display: true,
						text: 'Time Interval'
					},
					ticks: {
						callback: function (value) {
							const num = Number(value);
							if (num % 12 === 0) {
								return `${num / 4}h`;
							}
							return '';
						}
					}
				},
				y: {
					title: {
						display: true,
						text: 'Cost (€/15min)'
					}
				}
			}
		}
	});
</script>

<div class="space-y-6">
	<!-- Chart 1: Water Level and Volume -->
	<div class="rounded-lg border-2 border-gray-300 bg-white p-4 shadow-lg">
		<div style="height: 400px;">
			<Chart config={waterLevelConfig} />
		</div>
	</div>

	<!-- Charts 3 & 5: Price and Cost side by side -->
	<div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
		<!-- Chart 3: Electricity Price -->
		<div class="rounded-lg border-2 border-gray-300 bg-white p-4 shadow-lg">
			<div style="height: 300px;">
				<Chart config={priceConfig} />
			</div>
		</div>

		<!-- Chart 5: Cost -->
		<div class="rounded-lg border-2 border-gray-300 bg-white p-4 shadow-lg">
			<div style="height: 300px;">
				<Chart config={costConfig} />
			</div>
		</div>
	</div>

	<!-- Chart 4: Flow -->
	<div class="rounded-lg border-2 border-gray-300 bg-white p-4 shadow-lg">
		<div style="height: 350px;">
			<Chart config={flowConfig} />
		</div>
	</div>
</div>

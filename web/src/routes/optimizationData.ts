import type { TimelineData } from '$lib/types';
import optimizationResult from '$lib/data/optimization_result.json';

// Pump specifications matching the optimizer
function getPumpSpecs(pumpName: string, waterLevel: number): { power: number; flow: number } {
	const isSmall = pumpName === '1.1' || pumpName === '2.1';
	
	if (isSmall) {
		// Small pump: flow varies from 1150-1750 m³/h based on water level
		const flow = 1150 + 600 * Math.max(0, Math.min(4, waterLevel)) / 4;
		return { power: 185, flow };
	} else {
		// Big pump: flow varies from 2500-3500 m³/h based on water level
		const flow = 2500 + 1000 * Math.max(0, Math.min(5, waterLevel)) / 5;
		return { power: 350, flow };
	}
}

// Transform optimization result to TimelineData format
function transformOptimizationData(): TimelineData[] {
	return optimizationResult.schedule.map((interval) => {
		const waterLevel = interval.water_level_start_m;
		const activePumps = new Set(interval.active_pumps);
		
		// Initialize all pump flows and powers to 0
		const pumpData: Record<string, { flow: number; power: number }> = {
			'1.1': { flow: 0, power: 0 },
			'1.2': { flow: 0, power: 0 },
			'1.3': { flow: 0, power: 0 },
			'1.4': { flow: 0, power: 0 },
			'2.1': { flow: 0, power: 0 },
			'2.2': { flow: 0, power: 0 },
			'2.3': { flow: 0, power: 0 },
			'2.4': { flow: 0, power: 0 }
		};
		
		// Set flows and powers for active pumps
		for (const pump of activePumps) {
			const specs = getPumpSpecs(pump, waterLevel);
			pumpData[pump] = specs;
		}
		
		return {
			date: new Date(interval.date),
			waterLevel: waterLevel,
			waterVolume: interval.volume_start_m3,
			totalPumpedFlow: interval.outflow_m3 * 4, // Convert from m³/15min to m³/h
			waterInflow: interval.inflow_m3 * 4, // Convert from m³/15min to m³/h
			pumpFlow11: pumpData['1.1'].flow,
			pumpFlow12: pumpData['1.2'].flow,
			pumpFlow13: pumpData['1.3'].flow,
			pumpFlow14: pumpData['1.4'].flow,
			pumpFlow21: pumpData['2.1'].flow,
			pumpFlow22: pumpData['2.2'].flow,
			pumpFlow23: pumpData['2.3'].flow,
			pumpFlow24: pumpData['2.4'].flow,
			pumpPower11: pumpData['1.1'].power,
			pumpPower12: pumpData['1.2'].power,
			pumpPower13: pumpData['1.3'].power,
			pumpPower14: pumpData['1.4'].power,
			pumpPower21: pumpData['2.1'].power,
			pumpPower22: pumpData['2.2'].power,
			pumpPower23: pumpData['2.3'].power,
			pumpPower24: pumpData['2.4'].power,
			pumpFrequency11: pumpData['1.1'].flow > 0 ? 50 : 0,
			pumpFrequency12: pumpData['1.2'].flow > 0 ? 50 : 0,
			pumpFrequency13: pumpData['1.3'].flow > 0 ? 50 : 0,
			pumpFrequency14: pumpData['1.4'].flow > 0 ? 50 : 0,
			pumpFrequency21: pumpData['2.1'].flow > 0 ? 50 : 0,
			pumpFrequency22: pumpData['2.2'].flow > 0 ? 50 : 0,
			pumpFrequency23: pumpData['2.3'].flow > 0 ? 50 : 0,
			pumpFrequency24: pumpData['2.4'].flow > 0 ? 50 : 0,
			// Handle both old and new field names for electricity price
			electricityPrice1High: (interval as any).electricity_price_cents_per_kwh 
				? (interval as any).electricity_price_cents_per_kwh / 100 
				: (interval as any).electricity_price_eur_per_kwh,
			electricityPrice2Normal: (interval as any).electricity_price_cents_per_kwh 
				? (interval as any).electricity_price_cents_per_kwh / 100 
				: (interval as any).electricity_price_eur_per_kwh
		};
	});
}

export const optimizationData = transformOptimizationData();


import { createEffect, onCleanup } from 'solid-js';
import type { Component } from 'solid-js';
import Chart from 'chart.js/auto';
import type { ChartTypeRegistry } from 'chart.js/auto';

export const PulseChart: Component<{ mode: 'sales' | 'inventory', dynamicData?: any }> = (props) => {
  let mainCanvasRef: HTMLCanvasElement | undefined;
  let breakdownCanvasRef: HTMLCanvasElement | undefined;
  let mainChart: Chart | null = null;
  let breakdownChart: Chart | null = null;

  createEffect(() => {
    if (!mainCanvasRef) return;
    
    if (mainChart) mainChart.destroy();
    if (breakdownChart) breakdownChart.destroy();

    const isCurrency = props.mode !== 'inventory';
    const dynData = props.dynamicData;
    
    // Formatting utilities
    const formatValue = (val: number) => {
      if (isCurrency) {
        return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);
      }
      return new Intl.NumberFormat('en-IN').format(val) + ' kg';
    };

    const commonTooltipOptions = {
      callbacks: {
        label: function(context: any) {
          const val = context.parsed.y !== undefined ? context.parsed.y : context.parsed;
          const formatted = formatValue(val);
          
          if (context.chart.config.type === 'pie' || context.chart.config.type === 'doughnut') {
            const dataset = context.dataset;
            const total = dataset.data.reduce((a: number, b: number) => a + Number(b), 0);
            const percentage = ((val / total) * 100).toFixed(1) + '%';
            return `${context.label}: ${formatted} (${percentage})`;
          }
          return `${context.dataset.label || context.label}: ${formatted}`;
        }
      }
    };
    
    // 1. Render Main Chart (Line or Bar)
    if (dynData) {
      if (dynData.type && dynData.data) {
        // Render explicit Absolute/Bar chart
        mainChart = new Chart(mainCanvasRef, {
          type: dynData.type as keyof ChartTypeRegistry,
          data: {
            labels: dynData.labels,
            datasets: [{
              label: 'Metric Value',
              data: dynData.data,
              backgroundColor: ['#ef4444', '#10b981', '#3b82f6', '#f59e0b', '#8b5cf6'],
              borderWidth: 0,
              borderRadius: dynData.type === 'bar' ? 6 : 0
            }]
          },
          options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
              legend: { position: 'bottom', labels: { color: '#cbd5e1' } },
              tooltip: commonTooltipOptions
            },
            scales: dynData.type === 'bar' ? {
              y: { 
                grid: { color: 'rgba(255,255,255,0.05)' }, 
                beginAtZero: true,
                ticks: { callback: function(value) { return formatValue(Number(value)); }, color: '#94a3b8' },
                title: { display: true, text: isCurrency ? 'Amount (₹)' : 'Total Quantity (k/g)', color: '#cbd5e1', font: { weight: 'bold' } }
              },
              x: { 
                grid: { display: false }, 
                ticks: { color: '#94a3b8' },
                title: { display: true, text: 'Categories', color: '#cbd5e1', font: { weight: 'bold' } }
              }
            } : undefined
          }
        });
      } else if (dynData.labels) {
        // Render standard Historical Line chart
        const datasetActual = {
          label: 'Historical Sales Data',
          data: dynData.historical,
          borderColor: '#60a5fa',
          backgroundColor: 'rgba(96, 165, 250, 0.15)',
          borderWidth: 2,
          pointRadius: 0,
          pointHitRadius: 10,
          tension: 0.4, fill: true
        };
        const datasets = [datasetActual];
        let lineLabels = [...dynData.labels];

        if (dynData.forecast) {
          const forecastLabels = ['Next Mth', '+2 Mths', '+3 Mths'];
          lineLabels.push(...forecastLabels);
          datasets.push({
            label: 'AI Forecast',
            data: dynData.forecast,
            borderColor: '#f59e0b',
            backgroundColor: 'transparent',
            borderDash: [5, 5],
            borderWidth: 2,
            pointRadius: 4,
            pointHitRadius: 10,
            tension: 0.4, fill: false
          } as any);
        }

        mainChart = new Chart(mainCanvasRef, {
          type: 'line',
          data: { labels: lineLabels, datasets: datasets as any },
          options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
              legend: { position: 'top', labels: { color: '#cbd5e1', font: { weight: 'bold' } } },
              tooltip: commonTooltipOptions
            },
            scales: {
              y: { 
                grid: { color: 'rgba(255,255,255,0.05)' },
                ticks: { callback: function(value) { return formatValue(Number(value)); }, color: '#94a3b8' },
                title: { display: true, text: isCurrency ? 'Amount (₹)' : 'Total Weight (kg)', color: '#cbd5e1', font: { weight: 'bold' } }
              },
              x: { 
                grid: { display: false }, 
                ticks: { maxTicksLimit: 12, color: '#94a3b8' },
                title: { display: true, text: 'Time Period', color: '#cbd5e1', font: { weight: 'bold' } }
              }
            }
          }
        });
      }
    }

    // 2. Render Secondary Pie Chart
    if (breakdownCanvasRef && dynData && dynData.pie_labels && dynData.pie_data) {
      breakdownChart = new Chart(breakdownCanvasRef, {
        type: (dynData.pie_type || 'pie') as keyof ChartTypeRegistry,
        data: {
          labels: dynData.pie_labels,
          datasets: [{
            data: dynData.pie_data,
            backgroundColor: ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#6366f1', '#ec4899', '#14b8a6', '#f43f5e', '#84cc16'],
            borderWidth: 0,
            hoverOffset: 4
          }]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: { position: 'bottom', labels: { color: '#cbd5e1', font: { size: 10 } } },
            title: { display: true, text: 'Distribution Breakdown', color: '#f8fafc' },
            tooltip: commonTooltipOptions
          }
        }
      });
    }
  });

  onCleanup(() => {
    if (mainChart) mainChart.destroy();
    if (breakdownChart) breakdownChart.destroy();
  });

  return (
    <div class="flex flex-col xl:flex-row gap-6 h-full w-full">
      <div class="flex-1 min-h-[300px] h-full relative">
        <canvas ref={mainCanvasRef}></canvas>
      </div>
      <div class={`w-full xl:w-1/3 min-h-[300px] h-full relative bg-black/20 rounded-2xl p-4 border border-white/5 ${props.dynamicData?.pie_labels && props.dynamicData?.pie_data ? 'block' : 'hidden'}`}>
        <canvas ref={breakdownCanvasRef}></canvas>
      </div>
    </div>
  );
};

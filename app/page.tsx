// page.tsx
"use client"
import { useState, useEffect } from 'react';
import Temperature from '../components/temp';
import Humidity from '../components/Humidty';
import SpO2 from '../components/SpO2';
import MetricsOverTime from '../components/metrics';

export default function HealthDashboard() {
  const [metrics, setMetrics] = useState({
    temperature: { value: 0, change: 0 },
    humidity: { value: 0, change: 0 },
    spo2: { value: 0, change: 0 }
  });
  const [metricsHistory, setMetricsHistory] = useState([]);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8786');
    
    ws.onopen = () => {
      console.log('Connected to WebSocket server');
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Update current metrics and calculate changes
        setMetrics(prev => {
          const calculateChange = (oldVal, newVal) => {
            return oldVal === 0 ? 0 : ((newVal - oldVal) / oldVal * 100).toFixed(1);
          };

          return {
            temperature: {
              value: data.temperature,
              change: calculateChange(prev.temperature.value, data.temperature)
            },
            humidity: {
              value: data.humidity,
              change: calculateChange(prev.humidity.value, data.humidity)
            },
            spo2: {
              value: data.spo2,
              change: calculateChange(prev.spo2.value, data.spo2)
            }
          };
        });

        // Update metrics history
        setMetricsHistory(prev => {
          const timestamp = new Date().toLocaleTimeString('en-US', { 
            hour12: true,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
          });
          
          const newData = [...prev, {
            timestamp,
            temperature: data.temperature,
            humidity: data.humidity,
            spo2: data.spo2
          }];
          
          // Keep last 60 readings
          return newData.slice(-60);
        });
      } catch (error) {
        console.error('Error parsing message:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('Disconnected from WebSocket server');
    };
    
    return () => {
      ws.close();
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Health Monitoring Dashboard</h1>
          <p className="text-sm text-gray-900">Real-time health metrics</p>
        </div>
        <div className="flex items-center text-blue-900">
          <span className="mr-1">Live Monitoring</span>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18" />
          </svg>
        </div>
      </div>
      
      <div className="grid grid-cols-3 gap-4 mb-4">
        <Temperature value={metrics.temperature.value} change={metrics.temperature.change} />
        <Humidity value={metrics.humidity.value} change={metrics.humidity.change} />
        <SpO2 value={metrics.spo2.value} change={metrics.spo2.change} />
      </div>
      
      <MetricsOverTime data={metricsHistory} />
    </div>
  );
}

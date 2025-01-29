// metrics.js
"use client"
import React, { useState, useEffect } from 'react';
import { LineChart, Line, YAxis, ResponsiveContainer } from 'recharts';

const MetricsOverTime = ({ data }) => {
  return (
    <div className="bg-white rounded-lg p-4 shadow-sm">
      <div className="font-medium text-gray-700 mb-4">Metrics Over Time</div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <YAxis 
              domain={[0, 100]} 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#9CA3AF', fontSize: 12 }}
              tickCount={5}
            />
            <Line 
              type="monotone"
              dataKey="temperature"
              stroke="#FF9999"
              dot={false}
              strokeWidth={1.5}
            />
            <Line 
              type="monotone"
              dataKey="humidity"
              stroke="#9999FF"
              dot={false}
              strokeWidth={1.5}
            />
            <Line 
              type="monotone"
              dataKey="spo2"
              stroke="#FF99FF"
              dot={false}
              strokeWidth={1.5}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default MetricsOverTime;

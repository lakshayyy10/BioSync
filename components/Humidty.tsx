// src/components/Humidity.jsx
"use client"
import React from 'react';

const Humidity = ({ value, change }) => {
  return (
    <div className="bg-white rounded-lg p-8 shadow-sm">
      <div className="flex justify-between items-center">
        <div className="flex items-center">
          <span className="text-blue-500 mr-2">💧</span>
          <span className="text-gray-600">Heart Rate</span>
        </div>
        <span className={`text-xs ${change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
          {change}%
        </span>
      </div>
      <div className="flex items-baseline mt-2">
        <span className="text-3xl font-bold">{value.toFixed(1)}</span>
        <span className="text-sm ml-1 text-gray-500">%</span>
      </div>
    </div>
  );
};

export default Humidity;

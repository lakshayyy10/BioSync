"use client"
import React from 'react';

const Temperature = ({ value, change }) => {
  return (
    <div className="bg-white rounded-lg p-3 shadow-sm">
      <div className="flex justify-between items-center">
        <div className="flex items-center">
          <span className="text-red-500 mr-2">🌡️</span>
          <span className="text-gray-600">Temperature</span>
        </div>
        <span className={`text-xs ${change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
          {change}%
        </span>
      </div>
      <div className="flex items-baseline mt-2">
        <span className="text-3xl font-bold">{value.toFixed(1)}</span>
        <span className="text-sm ml-1 text-gray-500">°C</span>
      </div>
    </div>
  );
};

export default Temperature;

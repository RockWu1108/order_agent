
import React from 'react';

const LoadingSpinner: React.FC<{ message?: string }> = ({ message = "Finding delicious options..." }) => {
  return (
    <div className="flex flex-col justify-center items-center p-10 text-center">
      <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-orange-500 mb-4"></div>
      <p className="text-xl text-gray-700 font-semibold">{message}</p>
    </div>
  );
};
export default LoadingSpinner;


import React from 'react';
import { PreferenceFilters } from '../types.ts';
import { AVAILABLE_CUISINES, PRICE_RANGES_OPTIONS, RATING_OPTIONS } from '../constants.ts';

interface FilterControlsProps {
  filters: PreferenceFilters;
  onFilterChange: <K extends keyof PreferenceFilters>(key: K, value: PreferenceFilters[K]) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

const FilterControls: React.FC<FilterControlsProps> = ({ filters, onFilterChange, onSubmit, isLoading }) => {
  
  const handleCuisineChange = (cuisine: string) => {
    const newCuisines = filters.cuisine.includes(cuisine)
      ? filters.cuisine.filter(c => c !== cuisine)
      : [...filters.cuisine, cuisine];
    onFilterChange('cuisine', newCuisines);
  };

  const handlePriceChange = (price: string) => {
    const newPrices = filters.priceRange.includes(price)
      ? filters.priceRange.filter(p => p !== price)
      : [...filters.priceRange, price];
    onFilterChange('priceRange', newPrices);
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-lg mb-8">
      <h2 className="text-2xl font-semibold text-gray-800 mb-6">Find Your Next Meal</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
        {/* Search Term */}
        <div className="lg:col-span-3">
          <label htmlFor="searchTerm" className="block text-sm font-medium text-gray-700 mb-1">
            What are you craving? (e.g., "spicy noodles downtown", "cozy cafe")
          </label>
          <input
            type="text"
            id="searchTerm"
            value={filters.searchTerm}
            onChange={(e) => onFilterChange('searchTerm', e.target.value)}
            placeholder="e.g., Best pizza nearby"
            className="w-full p-3 border border-gray-300 rounded-lg shadow-sm focus:ring-orange-500 focus:border-orange-500 transition duration-150"
          />
        </div>

        {/* Cuisine Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Cuisine</label>
          <div className="max-h-40 overflow-y-auto bg-gray-50 p-3 rounded-md border border-gray-200 space-y-2">
            {AVAILABLE_CUISINES.map(cuisine => (
              <div key={cuisine} className="flex items-center">
                <input
                  id={`cuisine-${cuisine}`}
                  type="checkbox"
                  checked={filters.cuisine.includes(cuisine)}
                  onChange={() => handleCuisineChange(cuisine)}
                  className="h-4 w-4 text-orange-600 border-gray-300 rounded focus:ring-orange-500"
                />
                <label htmlFor={`cuisine-${cuisine}`} className="ml-2 text-sm text-gray-700">{cuisine}</label>
              </div>
            ))}
          </div>
        </div>

        {/* Price Range Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Price Range</label>
          <div className="bg-gray-50 p-3 rounded-md border border-gray-200 space-y-2">
            {PRICE_RANGES_OPTIONS.map(option => (
              <div key={option.value} className="flex items-center">
                <input
                  id={`price-${option.value}`}
                  type="checkbox"
                  checked={filters.priceRange.includes(option.value)}
                  onChange={() => handlePriceChange(option.value)}
                  className="h-4 w-4 text-orange-600 border-gray-300 rounded focus:ring-orange-500"
                />
                <label htmlFor={`price-${option.value}`} className="ml-2 text-sm text-gray-700">{option.label}</label>
              </div>
            ))}
          </div>
        </div>
        
        {/* Rating Filter */}
        <div>
          <label htmlFor="minRating" className="block text-sm font-medium text-gray-700 mb-2">Minimum Rating</label>
          <select
            id="minRating"
            value={filters.minRating}
            onChange={(e) => onFilterChange('minRating', parseFloat(e.target.value))}
            className="w-full p-3 border border-gray-300 rounded-lg shadow-sm focus:ring-orange-500 focus:border-orange-500 transition duration-150"
          >
            {RATING_OPTIONS.map(option => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>
      </div>

      <button
        onClick={onSubmit}
        disabled={isLoading}
        className="w-full bg-orange-500 hover:bg-orange-600 text-white font-semibold py-3 px-6 rounded-lg shadow-md hover:shadow-lg transition duration-150 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center text-lg"
      >
        {isLoading ? (
          <>
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Searching...
          </>
        ) : "Find Restaurants"}
      </button>
    </div>
  );
};

export default FilterControls;


import React from 'react';
import { FoodItem } from '../types.ts';
import StarRating from './StarRating.tsx';

interface FoodCardProps {
  foodItem: FoodItem;
  onSelectForOrder: (item: FoodItem) => void;
  isSelected: boolean;
}

const FoodCard: React.FC<FoodCardProps> = ({ foodItem, onSelectForOrder, isSelected }) => {
  return (
    <div className={`bg-white rounded-xl shadow-lg overflow-hidden transition-all duration-300 hover:shadow-2xl flex flex-col ${isSelected ? 'ring-4 ring-orange-500' : 'ring-1 ring-gray-200'}`}>
      <img 
        src={foodItem.imageUrl} 
        alt={`Image of ${foodItem.name}`} 
        className="w-full h-48 object-cover" 
        onError={(e) => (e.currentTarget.src = 'https://picsum.photos/400/300?grayscale')} // Fallback image
      />
      <div className="p-5 flex flex-col flex-grow">
        <h3 className="text-xl font-semibold text-gray-800 mb-1 truncate" title={foodItem.name}>{foodItem.name}</h3>
        <p className="text-sm text-orange-600 font-medium mb-2">{foodItem.cuisine}</p>
        
        <div className="flex items-center justify-between mb-3">
          <StarRating rating={foodItem.rating} />
          <span className="text-lg font-bold text-gray-700">{foodItem.priceRange}</span>
        </div>
        
        <p className="text-gray-600 text-sm mb-4 flex-grow leading-relaxed">{foodItem.description}</p>
        <p className="text-xs text-gray-500 mb-4 truncate" title={foodItem.address}>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 inline mr-1 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
            </svg>
            {foodItem.address}
        </p>
        
        <button
          onClick={() => onSelectForOrder(foodItem)}
          className={`w-full mt-auto py-2 px-4 rounded-lg font-semibold transition-colors duration-150 text-sm
            ${isSelected 
              ? 'bg-red-500 hover:bg-red-600 text-white' 
              : 'bg-orange-500 hover:bg-orange-600 text-white'}`}
        >
          {isSelected ? 'Remove from Order' : 'Select for Group Order'}
        </button>
      </div>
    </div>
  );
};

export default FoodCard;

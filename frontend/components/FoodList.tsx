
import React from 'react';
import { FoodItem } from '../types.ts';
import FoodCard from './FoodCard.tsx';

interface FoodListProps {
  recommendations: FoodItem[];
  onSelectForOrder: (item: FoodItem) => void;
  selectedItems: FoodItem[];
}

const FoodList: React.FC<FoodListProps> = ({ recommendations, onSelectForOrder, selectedItems }) => {
  if (recommendations.length === 0) {
    return <p className="text-center text-gray-600 py-10 text-lg">No recommendations match your criteria. Try adjusting your filters!</p>;
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {recommendations.map(item => (
        <FoodCard 
          key={item.id} 
          foodItem={item} 
          onSelectForOrder={onSelectForOrder}
          isSelected={selectedItems.some(selected => selected.id === item.id)}
        />
      ))}
    </div>
  );
};

export default FoodList;

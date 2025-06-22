import React from 'react';
import { FoodItem } from '../types';
import StarRating from './StarRating';

interface FoodCardProps {
  item: FoodItem;
  onSelect: (name: string) => void;
}

/**
 * 用於顯示單一餐廳資訊的卡片元件。
 */
const FoodCard: React.FC<FoodCardProps> = ({ item, onSelect }) => {
  return (
    <div
      className="bg-white rounded-xl shadow-lg overflow-hidden transform hover:-translate-y-1 transition-all duration-300 cursor-pointer flex flex-col justify-between"
      onClick={() => onSelect(item.name)}
    >
      <div className="p-4">
        {/* --- 新增的元素：顯示餐廳種類 --- */}
        <p className="text-xs font-semibold text-orange-500 uppercase tracking-wide mb-1" title={item.cuisine}>
          {item.cuisine}
        </p>
        {/* --- 新增結束 --- */}
        <h3 className="text-lg font-bold text-gray-900 truncate" title={item.name}>{item.name}</h3>
        <p className="text-sm text-gray-500 mt-1 truncate" title={item.address}>{item.address}</p>
        <div className="flex items-center justify-between mt-4">
          <StarRating rating={item.rating} />
          <span className="text-sm font-semibold text-gray-700">{item.rating.toFixed(1)}</span>
        </div>
      </div>
       <div className="px-4 pb-4">
         <button
            onClick={(e) => {
                e.stopPropagation();
                onSelect(item.name);
            }}
            className="w-full bg-blue-500 text-white rounded-md px-4 py-2 text-sm font-semibold hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
        >
            選擇這家
        </button>
       </div>
    </div>
  );
};

export default FoodCard;
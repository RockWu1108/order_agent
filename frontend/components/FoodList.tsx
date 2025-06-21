import React from 'react';
import { FoodItem, FoodListProps } from '../types';
import FoodCard from './FoodCard';

/**
 * 顯示餐廳卡片列表的容器元件。
 * @param items - 要顯示的餐廳項目陣列。
 * @param onSelect - 當使用者選擇一家餐廳時觸發的回呼函式。
 */
const FoodList: React.FC<FoodListProps> = ({ items, onSelect }) => {
  return (
    <div className="my-4">
      <h2 className="text-xl font-semibold text-gray-700 mb-3">為您找到的餐廳:</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {/* 修正：為 'item' 參數加上明確的 FoodItem 型別，以解決 TS7006 錯誤 */}
        {items.map((item: FoodItem) => (
          <FoodCard key={item.name} item={item} onSelect={onSelect} />
        ))}
      </div>
    </div>
  );
};

export default FoodList;

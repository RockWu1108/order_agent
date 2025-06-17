
import React from 'react';

interface StarRatingProps {
  rating: number;
}

const StarIcon: React.FC<{ filled: boolean; half?: boolean }> = ({ filled, half }) => (
  <svg
    className={`w-5 h-5 ${filled ? 'text-yellow-400' : 'text-gray-300'}`}
    fill="currentColor"
    viewBox="0 0 20 20"
    xmlns="http://www.w3.org/2000/svg"
  >
    {half ? (
      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8-2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292zM10 15V5l-1.632 5.031L4.205 10.5l3.237 2.345L6.368 18.09 10 15z" />
    ) : (
      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
    )}
  </svg>
);


const StarRating: React.FC<StarRatingProps> = ({ rating }) => {
  const totalStars = 5;
  const displayRating = Math.max(0, Math.min(rating, totalStars));
  const fullStars = Math.floor(displayRating);
  const hasHalfStar = displayRating % 1 >= 0.25 && displayRating % 1 <= 0.75; // Adjust threshold for half star
  
  return (
    <div className="flex items-center">
      {[...Array(totalStars)].map((_, index) => {
        if (index < fullStars) {
          return <StarIcon key={`full-${index}`} filled={true} />;
        }
        if (index === fullStars && hasHalfStar) {
          return <StarIcon key={`half-${index}`} filled={true} half={true} />;
        }
        return <StarIcon key={`empty-${index}`} filled={false} />;
      })}
      <span className="ml-2 text-sm text-gray-700 font-medium">{displayRating.toFixed(1)}</span>
    </div>
  );
};

export default StarRating;

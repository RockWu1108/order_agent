
import React from 'react';

const Header: React.FC = () => {
  return (
    <header className="bg-gradient-to-r from-orange-500 to-red-600 text-white p-6 shadow-xl sticky top-0 z-50">
      <div className="container mx-auto flex flex-col sm:flex-row justify-between items-center">
        <div>
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight">🍽️ Local Eats Group Order</h1>
            <p className="text-sm md:text-base mt-1 text-orange-100">Discover, Share, and Enjoy Food Together!</p>
        </div>
        {/* Placeholder for future nav items if needed */}
      </div>
    </header>
  );
};

export default Header;

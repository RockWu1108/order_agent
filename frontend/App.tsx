
import React, { useState, useCallback, useEffect } from 'react';
import Header from './components/Header';
import FilterControls from './components/FilterControls';
import FoodList from './components/FoodList';
import LoadingSpinner from './components/LoadingSpinner';
import GroupOrderSetupForm from './components/GroupOrderSetupForm';
import ConfirmationMessage from './components/ConfirmationMessage';
import { fetchFoodRecommendations } from './services/geminiService';
import { FoodItem, PreferenceFilters, AppView, GroupOrderEventDetails } from './types.ts';
import { DEFAULT_SEARCH_TERM } from './constants.ts';

const App: React.FC = () => {
  const [appView, setAppView] = useState<AppView>(AppView.SEARCH_FILTERS);
  const [filters, setFilters] = useState<PreferenceFilters>({
    searchTerm: DEFAULT_SEARCH_TERM,
    cuisine: [],
    priceRange: [],
    minRating: 0,
  });
  const [recommendations, setRecommendations] = useState<FoodItem[]>([]);
  const [selectedForGroupOrder, setSelectedForGroupOrder] = useState<FoodItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSubmittedEvent, setLastSubmittedEvent] = useState<GroupOrderEventDetails | null>(null);

  const handleFilterChange = useCallback(<K extends keyof PreferenceFilters>(
    key: K, 
    value: PreferenceFilters[K]
  ) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const handleFetchRecommendations = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setRecommendations([]); 
    try {
      const results = await fetchFoodRecommendations(filters);
      setRecommendations(results);
      setAppView(AppView.SHOWING_RECOMMENDATIONS);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred.');
      }
      setAppView(AppView.SEARCH_FILTERS); // Stay on search/filter page on error
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  const handleSelectForOrder = useCallback((item: FoodItem) => {
    setSelectedForGroupOrder(prev =>
      prev.find(selected => selected.id === item.id)
        ? prev.filter(selected => selected.id !== item.id)
        : [...prev, item]
    );
  }, []);

  const handleInitiateGroupOrder = () => {
    if (selectedForGroupOrder.length > 0) {
      setAppView(AppView.GROUP_ORDER_SETUP);
    } else {
      alert("Please select at least one restaurant to include in your group order.");
    }
  };
  
  const handleGroupOrderSubmit = (details: GroupOrderEventDetails) => {
    setLastSubmittedEvent(details);
    setAppView(AppView.CONFIRMATION);
    // Reset selections for next time
    setSelectedForGroupOrder([]); 
  };

  const handleReturnToSearch = () => {
    setAppView(AppView.SEARCH_FILTERS);
    // Optionally clear recommendations or keep them
    // setRecommendations([]); 
    setError(null);
  };
  
  // Effect to clear error when filters change, allowing retry
   useEffect(() => {
    if (error) {
      setError(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.searchTerm, filters.cuisine, filters.priceRange, filters.minRating]);


  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="container mx-auto p-4 md:p-6 flex-grow">
        {appView === AppView.SEARCH_FILTERS && (
          <>
            <FilterControls 
              filters={filters} 
              onFilterChange={handleFilterChange} 
              onSubmit={handleFetchRecommendations}
              isLoading={isLoading}
            />
            {error && <p className="text-red-500 text-center mt-4 p-3 bg-red-100 rounded-md">{error}</p>}
          </>
        )}

        {appView === AppView.SHOWING_RECOMMENDATIONS && (
          <>
            {/* Optionally, show filters again or a button to modify filters */}
             <button 
                onClick={() => setAppView(AppView.SEARCH_FILTERS)}
                className="mb-6 bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-4 rounded-lg transition duration-150 flex items-center"
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3a1 1 0 01-.293.707L13 10.414V15a1 1 0 01-.293.707l-2 2A1 1 0 019 17v-1.586L4.293 10.707A1 1 0 014 10V3z" clipRule="evenodd" />
                </svg>
                Modify Search & Filters
            </button>
            {isLoading && <LoadingSpinner />}
            {error && <p className="text-red-500 text-center my-4 p-3 bg-red-100 rounded-md">{error}</p>}
            {!isLoading && !error && recommendations.length > 0 && (
              <FoodList 
                recommendations={recommendations} 
                onSelectForOrder={handleSelectForOrder}
                selectedItems={selectedForGroupOrder}
              />
            )}
            {!isLoading && !error && recommendations.length === 0 && (
                 <p className="text-center text-gray-600 py-10 text-lg">No recommendations found. Try broadening your search or filters!</p>
            )}
            {selectedForGroupOrder.length > 0 && !isLoading && (
              <div className="fixed bottom-0 left-0 right-0 bg-white p-4 border-t-2 border-orange-500 shadow-2xl z-40">
                <div className="container mx-auto flex justify-center items-center">
                  <button
                    onClick={handleInitiateGroupOrder}
                    className="bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-8 rounded-lg shadow-lg text-lg transition duration-150"
                  >
                    Initiate Group Order ({selectedForGroupOrder.length} selected)
                  </button>
                </div>
              </div>
            )}
          </>
        )}

        {appView === AppView.GROUP_ORDER_SETUP && (
          <GroupOrderSetupForm 
            selectedRestaurants={selectedForGroupOrder}
            onSubmit={handleGroupOrderSubmit}
            onCancel={() => setAppView(AppView.SHOWING_RECOMMENDATIONS)}
          />
        )}

        {appView === AppView.CONFIRMATION && lastSubmittedEvent && (
          <ConfirmationMessage 
            eventDetails={lastSubmittedEvent}
            onReturnToSearch={handleReturnToSearch}
          />
        )}
      </main>
      <footer className="text-center p-4 text-sm text-gray-500 bg-gray-200">
        Powered by Gemini API & React. Created for delicious group meals!
      </footer>
    </div>
  );
};

export default App;

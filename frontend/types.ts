
export interface FoodItem {
  id: string;
  name: string;
  cuisine: string;
  rating: number; // 1-5
  priceRange: string; // e.g., "$", "$$", "$$$"
  description: string;
  address: string;
  imageUrl: string;
}

export interface PreferenceFilters {
  searchTerm: string;
  cuisine: string[];
  priceRange: string[];
  minRating: number; // 0-5
}

export interface SelectedFoodItemForOrder extends FoodItem {
  // Potentially add quantity or notes if selecting specific dishes,
  // for now, we select whole restaurants for the event.
}

export interface GroupOrderEventDetails {
  organizerName: string;
  organizerEmail: string;
  eventTitle: string;
  eventDateTime: string;
  notesForGroup: string;
  selectedRestaurants: FoodItem[];
}

export enum AppView {
  SEARCH_FILTERS = 'SEARCH_FILTERS',
  SHOWING_RECOMMENDATIONS = 'SHOWING_RECOMMENDATIONS',
  GROUP_ORDER_SETUP = 'GROUP_ORDER_SETUP',
  CONFIRMATION = 'CONFIRMATION',
}

// For Gemini API response parsing
export interface GeminiFoodRecommendation {
  name: string;
  cuisine: string;
  rating: number; // Expecting 1-5, can be decimal
  priceRange: string; // e.g., "$", "$$", "$$$"
  description: string;
  address: string;
}

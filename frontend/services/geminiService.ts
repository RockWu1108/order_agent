import { GoogleGenAI } from "@google/genai";
import { FoodItem, PreferenceFilters, GeminiFoodRecommendation } from '../types.ts';
import { GEMINI_MODEL_NAME } from '../constants.ts';

const API_KEY = process.env.API_KEY;

if (!API_KEY) {
  console.error("API_KEY environment variable is not set. Gemini API calls will fail.");
}

const ai = new GoogleGenAI({ apiKey: API_KEY || "MISSING_API_KEY" });

const generatePrompt = (filters: PreferenceFilters): string => {
  let prompt = `You are a helpful local food expert. I'm looking for restaurant recommendations.
My primary search query is: "${filters.searchTerm}".`;

  if (filters.cuisine.length > 0 && !filters.cuisine.includes("Any")) {
    prompt += `\nI'm interested in the following cuisines: ${filters.cuisine.join(', ')}.`;
  }
  if (filters.priceRange.length > 0) {
    prompt += `\nMy preferred price range(s) are: ${filters.priceRange.join(', ')}.`;
  }
  if (filters.minRating > 0) {
    prompt += `\nI'm looking for restaurants with at least a ${filters.minRating} out of 5 star rating.`;
  }

  prompt += `

Please suggest 5 to 8 diverse restaurants that best match these criteria.
For each restaurant, provide the following details in a JSON array format. Each object in the array should have these exact keys: "name", "cuisine" (the main type of cuisine), "rating" (a number between 1 and 5, e.g., 4.5), "priceRange" (e.g., "$", "$$", "$$$"), "description" (a brief, enticing summary, 1-2 sentences), and "address" (a plausible street address in a major city, be creative).

Example of a single item in the JSON array:
{
  "name": "Luigi's Pizzeria",
  "cuisine": "Italian",
  "rating": 4.5,
  "priceRange": "$$",
  "description": "Authentic Italian pizzas with fresh ingredients. A local favorite for families and late-night snacks.",
  "address": "123 Pizza St, Anytown, USA"
}

Ensure the output is ONLY the JSON array. Do not include any other text, markdown formatting for the JSON block, or explanations before or after the JSON array.
The rating should be a numerical value. The priceRange should be one of "$", "$$", "$$$", or "$$$$".
`;
  return prompt;
};

export const fetchFoodRecommendations = async (filters: PreferenceFilters): Promise<FoodItem[]> => {
  if (!API_KEY) {
    throw new Error("Gemini API Key is not configured. Please set the API_KEY environment variable.");
  }
  
  const prompt = generatePrompt(filters);

  try {
    const result = await ai.models.generateContent({
        model: GEMINI_MODEL_NAME,
        contents: prompt,
        config: {
            responseMimeType: "application/json",
            temperature: 0.7, // Add some creativity
        }
    });

    let jsonStr = result.text().trim();

    // Remove potential markdown fences (e.g., ```json ... ``` or ``` ... ```)
    const fenceRegex = /^```(?:json)?\s*\n?(.*?)\n?\s*```$/s;
    const match = jsonStr.match(fenceRegex);
    if (match && match[1]) {
      jsonStr = match[1].trim();
    }
    
    // Sometimes the API might still wrap it or return plain text not perfectly parseable
    // Add a check to ensure it's an array bracket start
    if (!jsonStr.startsWith('[')) {
        // Attempt to find JSON array within the string if it's not starting with [
        const arrayMatch = jsonStr.match(/(\[.*\])/s);
        if (arrayMatch && arrayMatch[1]) {
            jsonStr = arrayMatch[1];
        } else {
            console.error("Gemini response is not a JSON array:", result.text());
            throw new Error("The AI returned data in an unexpected format. It might be plain text instead of JSON. Try rephrasing your search.");
        }
    }

    const parsedData = JSON.parse(jsonStr) as GeminiFoodRecommendation[];

    if (!Array.isArray(parsedData)) {
        console.error("Parsed data is not an array:", parsedData);
        throw new Error("The AI returned data that is not a list of recommendations.");
    }
    
    return parsedData.map((item, index) => ({
      ...item,
      id: crypto.randomUUID(), // Generate a unique ID
      rating: Number(item.rating) || 0, // Ensure rating is a number
      imageUrl: `https://picsum.photos/seed/${encodeURIComponent(item.name.slice(0,20))}/${400 + index}/${300 + index}` // Placeholder image
    }));

  } catch (error) {
    console.error("Error fetching food recommendations from Gemini:", error);
    if (error instanceof Error) {
        if(error.message.includes("API_KEY_INVALID")){
             throw new Error("The Gemini API key is invalid. Please check your API_KEY environment variable.");
        }
         throw new Error(`Failed to get recommendations from AI: ${error.message}. Raw response might be in console.`);
    }
    throw new Error("An unknown error occurred while fetching recommendations.");
  }
};

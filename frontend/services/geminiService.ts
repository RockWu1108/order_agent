import { GoogleGenerativeAI } from "@google/generative-ai";
import { FoodItem, PreferenceFilters, GeminiFoodRecommendation } from '../types.ts';
import { GEMINI_MODEL_NAME } from '../constants.ts';

// 使用 Vite 的 import.meta.env 來讀取加上前綴的環境變數
const API_KEY = import.meta.env.VITE_GOOGLE_API_KEY;

if (!API_KEY) {
  // 這個錯誤訊息會在開發伺服器的終端機中顯示
  console.error("VITE_GOOGLE_API_KEY 環境變數未設定。Gemini API 呼叫將會失敗。");
}

// 如果 API_KEY 不存在，傳遞一個空字串以避免初始化失敗，錯誤將在後續呼叫時被捕捉
const ai = new GoogleGenerativeAI(API_KEY || "");

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
    throw new Error("Gemini API Key is not configured. Please set the VITE_GOOGLE_API_KEY environment variable in your .env file.");
  }

  const prompt = generatePrompt(filters);

  try {
    const model = ai.getGenerativeModel({ model: GEMINI_MODEL_NAME});
    const result = await model.generateContent({
        contents: [{role: "user", parts: [{text: prompt}]}],
        generationConfig: {
            responseMimeType: "application/json",
            temperature: 0.7, // Add some creativity
        }
    });

    const response = result.response;
    let jsonStr = response.text().trim();

    // 移除潛在的 markdown 格式 (e.g., ```json ... ``` or ``` ... ```)
    const fenceRegex = /^```(?:json)?\s*\n?(.*?)\n?\s*```$/s;
    const match = jsonStr.match(fenceRegex);
    if (match && match[1]) {
      jsonStr = match[1].trim();
    }

    // 有時 API 可能仍然會回傳不完美的 JSON 格式
    // 檢查它是否以陣列的括號開頭
    if (!jsonStr.startsWith('[')) {
        // 如果不是，嘗試在字串中尋找 JSON 陣列
        const arrayMatch = jsonStr.match(/(\[.*\])/s);
        if (arrayMatch && arrayMatch[1]) {
            jsonStr = arrayMatch[1];
        } else {
            console.error("Gemini response is not a JSON array:", response.text());
            throw new Error("AI 回傳的資料格式不正確，可能為純文字而非 JSON。請嘗試更換搜尋關鍵字。");
        }
    }

    const parsedData = JSON.parse(jsonStr) as GeminiFoodRecommendation[];

    if (!Array.isArray(parsedData)) {
        console.error("解析後的資料不是一個陣列:", parsedData);
        throw new Error("AI 回傳的資料並非一個推薦列表。");
    }

    return parsedData.map((item, index) => ({
      ...item,
      id: crypto.randomUUID(), // 產生唯一的 ID
      rating: Number(item.rating) || 0, // 確保評分是數字
      imageUrl: `https://picsum.photos/seed/${encodeURIComponent(item.name.slice(0,20))}/${400 + index}/${300 + index}` // 預留圖片位置
    }));

  } catch (error) {
    console.error("從 Gemini 取得食物推薦時發生錯誤:", error);
    if (error instanceof Error) {
        if(error.message.includes("API_KEY_INVALID")){
             throw new Error("此 Gemini API 金鑰無效。請檢查你的 VITE_GOOGLE_API_KEY 環境變數。");
        }
         throw new Error(`無法從 AI 取得推薦： ${error.message}。詳細回應可能顯示在 console 中。`);
    }
    throw new Error("取得推薦時發生未知錯誤。");
  }
};

import React from 'react';
import { GroupOrderEventDetails } from '../types.ts';

interface ConfirmationMessageProps {
  eventDetails: GroupOrderEventDetails;
  onReturnToSearch: () => void;
}

const ConfirmationMessage: React.FC<ConfirmationMessageProps> = ({ eventDetails, onReturnToSearch }) => {
  const formattedDateTime = new Date(eventDetails.eventDateTime).toLocaleString([], {
    year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit'
  });

  return (
    <div className="bg-white p-8 rounded-xl shadow-xl max-w-2xl mx-auto my-10 text-center">
      <div className="text-6xl mb-6">✅</div>
      <h2 className="text-3xl font-bold text-green-600 mb-4">Success!</h2>
      <p className="text-lg text-gray-700 mb-2">
        Your group order event <strong className="text-orange-600">"{eventDetails.eventTitle}"</strong> has been initiated.
      </p>
      <p className="text-gray-600 mb-6">Proposed Date & Time: <strong>{formattedDateTime}</strong></p>

      <div className="bg-orange-50 p-6 rounded-lg border border-orange-200 text-left mb-8">
        <h3 className="text-xl font-semibold text-orange-700 mb-3">Next Steps:</h3>
        <ol className="list-decimal list-inside space-y-2 text-gray-700">
          <li>
            Manually create a way for your group to submit their choices (e.g., a Google Form, shared document, or simple message group poll).
          </li>
          <li>
            Include these selected restaurants as options:
            <ul className="list-disc list-inside ml-6 mt-1 text-sm">
              {eventDetails.selectedRestaurants.map(r => <li key={r.id}>{r.name}</li>)}
            </ul>
          </li>
          {eventDetails.notesForGroup && (
            <li>Share these instructions: "{eventDetails.notesForGroup}"</li>
          )}
          <li>
            Inform your group about the deadline (ideally before {formattedDateTime}).
          </li>
          <li>Collect responses, place the final order, and enjoy your meal!</li>
        </ol>
        <p className="mt-4 text-xs text-gray-500">
            (This app has simulated the event creation. Actual notifications and form sharing are manual steps.)
        </p>
      </div>

      <button
        onClick={onReturnToSearch}
        className="bg-orange-500 hover:bg-orange-600 text-white font-semibold py-3 px-8 rounded-lg shadow-md hover:shadow-lg transition duration-150 text-lg"
      >
        Find More Restaurants
      </button>
    </div>
  );
};

export default ConfirmationMessage;

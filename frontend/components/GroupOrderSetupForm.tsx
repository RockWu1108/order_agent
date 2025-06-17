
import React, { useState } from 'react';
import { FoodItem, GroupOrderEventDetails } from '../types.ts';

interface GroupOrderSetupFormProps {
  selectedRestaurants: FoodItem[];
  onSubmit: (details: GroupOrderEventDetails) => void;
  onCancel: () => void;
}

const GroupOrderSetupForm: React.FC<GroupOrderSetupFormProps> = ({ selectedRestaurants, onSubmit, onCancel }) => {
  const [organizerName, setOrganizerName] = useState('');
  const [organizerEmail, setOrganizerEmail] = useState('');
  const [eventTitle, setEventTitle] = useState('');
  const [eventDateTime, setEventDateTime] = useState('');
  const [notesForGroup, setNotesForGroup] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!organizerName || !organizerEmail || !eventTitle || !eventDateTime || selectedRestaurants.length === 0) {
        alert("Please fill in all required fields and select at least one restaurant.");
        return;
    }
    onSubmit({
      organizerName,
      organizerEmail,
      eventTitle,
      eventDateTime,
      notesForGroup,
      selectedRestaurants,
    });
  };

  if (selectedRestaurants.length === 0) {
    return (
        <div className="bg-white p-8 rounded-xl shadow-xl max-w-2xl mx-auto my-10 text-center">
            <h2 className="text-2xl font-semibold text-gray-800 mb-6">Setup Group Order Event</h2>
            <p className="text-red-500 mb-4">Please select at least one restaurant before setting up a group order.</p>
            <button
                onClick={onCancel}
                className="bg-gray-500 hover:bg-gray-600 text-white font-semibold py-2 px-4 rounded-lg transition duration-150"
            >
                Back to Recommendations
            </button>
        </div>
    );
  }

  return (
    <div className="bg-white p-6 md:p-8 rounded-xl shadow-xl max-w-2xl mx-auto my-10">
      <h2 className="text-2xl md:text-3xl font-semibold text-gray-800 mb-6 text-center">🎉 Setup Your Group Order Event 🎉</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="eventTitle" className="block text-sm font-medium text-gray-700 mb-1">Event Title</label>
          <input
            type="text"
            id="eventTitle"
            value={eventTitle}
            onChange={(e) => setEventTitle(e.target.value)}
            placeholder="e.g., Friday Team Lunch, Birthday Dinner"
            required
            className="w-full p-3 border border-gray-300 rounded-lg shadow-sm focus:ring-orange-500 focus:border-orange-500"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
            <label htmlFor="organizerName" className="block text-sm font-medium text-gray-700 mb-1">Your Name (Organizer)</label>
            <input
                type="text"
                id="organizerName"
                value={organizerName}
                onChange={(e) => setOrganizerName(e.target.value)}
                placeholder="John Doe"
                required
                className="w-full p-3 border border-gray-300 rounded-lg shadow-sm focus:ring-orange-500 focus:border-orange-500"
            />
            </div>
            <div>
            <label htmlFor="organizerEmail" className="block text-sm font-medium text-gray-700 mb-1">Your Email (Organizer)</label>
            <input
                type="email"
                id="organizerEmail"
                value={organizerEmail}
                onChange={(e) => setOrganizerEmail(e.target.value)}
                placeholder="john.doe@example.com"
                required
                className="w-full p-3 border border-gray-300 rounded-lg shadow-sm focus:ring-orange-500 focus:border-orange-500"
            />
            </div>
        </div>
        
        <div>
          <label htmlFor="eventDateTime" className="block text-sm font-medium text-gray-700 mb-1">Proposed Date & Time</label>
          <input
            type="datetime-local"
            id="eventDateTime"
            value={eventDateTime}
            onChange={(e) => setEventDateTime(e.target.value)}
            required
            className="w-full p-3 border border-gray-300 rounded-lg shadow-sm focus:ring-orange-500 focus:border-orange-500"
          />
        </div>

        <div>
            <h4 className="text-md font-medium text-gray-700 mb-2">Selected Restaurants ({selectedRestaurants.length}):</h4>
            <ul className="list-disc list-inside bg-gray-50 p-3 rounded-md border border-gray-200 max-h-40 overflow-y-auto">
                {selectedRestaurants.map(r => <li key={r.id} className="text-sm text-gray-600">{r.name} ({r.cuisine})</li>)}
            </ul>
        </div>
        
        <div>
          <label htmlFor="notesForGroup" className="block text-sm font-medium text-gray-700 mb-1">Notes/Instructions for Group (Optional)</label>
          <textarea
            id="notesForGroup"
            value={notesForGroup}
            onChange={(e) => setNotesForGroup(e.target.value)}
            rows={3}
            placeholder="e.g., Please submit your choices by Thursday 5 PM. Mention any dietary restrictions."
            className="w-full p-3 border border-gray-300 rounded-lg shadow-sm focus:ring-orange-500 focus:border-orange-500"
          ></textarea>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-4 pt-4">
          <button
            type="button"
            onClick={onCancel}
            className="w-full sm:w-auto bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-3 px-6 rounded-lg transition duration-150"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="w-full sm:w-auto bg-orange-500 hover:bg-orange-600 text-white font-semibold py-3 px-6 rounded-lg shadow-md hover:shadow-lg transition duration-150"
          >
            Create Event & Get Next Steps
          </button>
        </div>
      </form>
    </div>
  );
};

export default GroupOrderSetupForm;

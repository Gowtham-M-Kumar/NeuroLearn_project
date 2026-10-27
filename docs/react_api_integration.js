/**
 * REACT INTEGRATION CODE FOR ALPHABET LEARNING APP
 * 
 * This file contains API utility functions and React hooks for integrating
 * the Alphabet Learning React app with Django backend.
 * 
 * IMPORTANT: 
 * - Use session authentication (Django cookies)
 * - Include credentials in all fetch requests
 * - CSRF token handling is required for POST requests
 */

// ============================================================================
// CSRF TOKEN UTILITY
// ============================================================================

/**
 * Get CSRF token from Django cookie
 * Required for all POST requests to Django backend
 */
function getCsrfToken() {
  const name = 'csrftoken';
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// ============================================================================
// API FUNCTIONS
// ============================================================================

/**
 * Mark a letter as completed
 * 
 * @param {string} letter - The letter to mark as completed (e.g., "A", "B")
 * @returns {Promise<object>} Response data
 * 
 * Example usage:
 * ```js
 * try {
 *   const result = await markLetterComplete("A");
 *   console.log(result.message); // "Progress saved successfully"
 * } catch (error) {
 *   console.error("Failed to save progress:", error);
 * }
 * ```
 */
export async function markLetterComplete(letter) {
  const response = await fetch('/learning/api/complete/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    credentials: 'include', // Include cookies for session auth
    body: JSON.stringify({
      module: 'alphabet',
      item: letter,
      completed: true,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to save progress');
  }

  return response.json();
}

/**
 * Get all learning progress for the current user
 * 
 * @param {string} module - Optional module filter (e.g., "alphabet")
 * @returns {Promise<object>} Progress data with count and results
 * 
 * Example usage:
 * ```js
 * // Get all progress
 * const allProgress = await getUserProgress();
 * 
 * // Get alphabet progress only
 * const alphabetProgress = await getUserProgress("alphabet");
 * console.log(alphabetProgress.results); // Array of completed items
 * ```
 */
export async function getUserProgress(module = null) {
  const url = module 
    ? `/learning/api/progress/?module=${encodeURIComponent(module)}`
    : '/learning/api/progress/';

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // Include cookies for session auth
  });

  if (!response.ok) {
    throw new Error('Failed to fetch progress');
  }

  return response.json();
}

// ============================================================================
// REACT HOOKS (OPTIONAL)
// ============================================================================

/**
 * React hook for managing alphabet progress
 * 
 * Example usage in a React component:
 * ```jsx
 * import { useAlphabetProgress } from './api';
 * 
 * function AlphabetApp() {
 *   const { progress, loading, error, markComplete, refresh } = useAlphabetProgress();
 * 
 *   const handleLetterComplete = async (letter) => {
 *     try {
 *       await markComplete(letter);
 *       console.log(`Letter ${letter} completed!`);
 *     } catch (err) {
 *       console.error(err);
 *     }
 *   };
 * 
 *   if (loading) return <div>Loading...</div>;
 *   if (error) return <div>Error: {error}</div>;
 * 
 *   return (
 *     <div>
 *       {progress.map(item => (
 *         <div key={item.id}>
 *           {item.item} - Completed: {item.completed ? '✓' : '✗'}
 *         </div>
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useAlphabetProgress() {
  const [progress, setProgress] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  // Fetch progress on mount
  const fetchProgress = React.useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getUserProgress('alphabet');
      setProgress(data.results);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    fetchProgress();
  }, [fetchProgress]);

  // Mark letter as complete and refresh
  const markComplete = React.useCallback(async (letter) => {
    await markLetterComplete(letter);
    await fetchProgress(); // Refresh data after marking complete
  }, [fetchProgress]);

  return {
    progress,
    loading,
    error,
    markComplete,
    refresh: fetchProgress,
  };
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Check if a specific letter is completed
 * 
 * @param {Array} progressData - Array of progress items from getUserProgress()
 * @param {string} letter - Letter to check (e.g., "A")
 * @returns {boolean} True if completed
 */
export function isLetterCompleted(progressData, letter) {
  return progressData.some(
    item => item.module === 'alphabet' && 
            item.item === letter && 
            item.completed
  );
}

/**
 * Get completion percentage for alphabet
 * 
 * @param {Array} progressData - Array of progress items
 * @returns {number} Percentage (0-100)
 */
export function getAlphabetCompletionPercentage(progressData) {
  const totalLetters = 26;
  const completedCount = progressData.filter(
    item => item.module === 'alphabet' && item.completed
  ).length;
  
  return Math.round((completedCount / totalLetters) * 100);
}

// ============================================================================
// EXAMPLE USAGE IN REACT COMPONENT
// ============================================================================

/**
 * Example React component showing complete integration
 */
/*
import React, { useEffect, useState } from 'react';
import { getUserProgress, markLetterComplete, isLetterCompleted } from './api';

function AlphabetLearning() {
  const [progressData, setProgressData] = useState([]);
  const [loading, setLoading] = useState(true);
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');

  // Load progress on mount
  useEffect(() => {
    async function loadProgress() {
      try {
        const data = await getUserProgress('alphabet');
        setProgressData(data.results);
      } catch (error) {
        console.error('Failed to load progress:', error);
      } finally {
        setLoading(false);
      }
    }
    loadProgress();
  }, []);

  // Handle letter completion
  const handleLetterClick = async (letter) => {
    // Check if already completed
    if (isLetterCompleted(progressData, letter)) {
      console.log(`${letter} already completed`);
      return;
    }

    try {
      // Mark as complete in backend
      await markLetterComplete(letter);
      
      // Update local state
      const data = await getUserProgress('alphabet');
      setProgressData(data.results);
      
      console.log(`Letter ${letter} completed successfully!`);
    } catch (error) {
      console.error(`Failed to complete ${letter}:`, error);
    }
  };

  if (loading) {
    return <div>Loading your progress...</div>;
  }

  return (
    <div className="alphabet-learning">
      <h1>Learn the Alphabet</h1>
      <div className="letter-grid">
        {alphabet.map(letter => {
          const completed = isLetterCompleted(progressData, letter);
          return (
            <button
              key={letter}
              onClick={() => handleLetterClick(letter)}
              className={completed ? 'letter completed' : 'letter'}
              disabled={completed}
            >
              {letter}
              {completed && ' ✓'}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default AlphabetLearning;
*/

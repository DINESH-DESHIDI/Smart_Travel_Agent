import React, { useState } from 'react';

function App() {
  // --- React State Hooks for Trip Parameters ---
  const [city, setCity] = useState('New York');
  const [days, setDays] = useState(3);
  const [budget, setBudget] = useState(120000);
  const [travelers, setTravelers] = useState(2);
  const [travelType, setTravelType] = useState('friends');
  const [preferredTransport, setPreferredTransport] = useState('transit');

  // --- React State Hooks for Tag Preferences ---
  const [preferences, setPreferences] = useState(['vegetarian', 'loves museums', 'budget traveler']);
  const [newPref, setNewPref] = useState('');

  // --- React State Hooks for Server Response Data ---
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // --- UI Layout active tab manager state ---
  const [activeTab, setActiveTab] = useState('timeline');

  /**
   * Appends a new customized preference tag to the user's checklist.
   */
  const addPreference = (e) => {
    e.preventDefault();
    if (newPref.trim() && !preferences.includes(newPref.trim().toLowerCase())) {
      setPreferences([...preferences, newPref.trim().toLowerCase()]);
      setNewPref('');
    }
  };

  /**
   * Deletes a preference tag by filtering it out from the active states list.
   */
  const removePreference = (pref) => {
    setPreferences(preferences.filter((p) => p !== pref));
  };

  /**
   * Dispatches a POST request to `/api/plan` on the FastAPI server to build a travel plan.
   */
  const fetchPlan = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: jsonRequestPayload()
      });
      if (!response.ok) {
        throw new Error('Failed to generate plan. Please verify the backend status and API keys.');
      }
      const data = await response.json();
      setPlan(data);
      // Automatically switch to the Day-wise Timeline tab on successful loading
      setActiveTab('timeline');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Requests the backend to update specific sections (Budget limit, Weather change simulation, Hotel rotates).
   */
  const regeneratePart = async (changeType) => {
    if (!plan) return;
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/regenerate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          city,
          days,
          budget,
          travelers,
          travel_type: travelType,
          preferred_transport: preferredTransport,
          preferences,
          change_type: changeType,
          current_plan: plan
        })
      });
      if (!response.ok) {
        throw new Error('Failed to update itinerary.');
      }
      const data = await response.json();
      setPlan(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Helper that compiles state hooks parameters into a standardized JSON payload structure.
   */
  const jsonRequestPayload = () => {
    return JSON.stringify({
      city,
      days,
      budget: parseFloat(budget),
      travelers: parseInt(travelers),
      travel_type: travelType,
      preferred_transport: preferredTransport,
      preferences
    });
  };


  return (
    <div className="app-container">
      <header>
        <h1>AI Smart Travel Companion</h1>
        <p>Your weather-aware, safety-scored, and budget-optimized destination planning assistant</p>
      </header>

      <div className="dashboard-grid">
        {/* Left Side: Sidebar Inputs */}
        <div className="sidebar-panel">
          <div className="panel-title">Trip Configurations</div>

          <div className="form-group">
            <label>Destination City</label>
            <input
              type="text"
              className="form-control"
              value={city}
              onChange={(e) => setCity(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Days</label>
            <input
              type="number"
              className="form-control"
              min="1"
              max="5"
              value={days}
              onChange={(e) => setDays(parseInt(e.target.value) || 1)}
            />
          </div>

          <div className="form-group">
            <label>Total Budget (₹)</label>
            <input
              type="number"
              className="form-control"
              value={budget}
              onChange={(e) => setBudget(parseFloat(e.target.value) || 0)}
            />
          </div>

          <div className="form-group">
            <label>Travelers</label>
            <input
              type="number"
              className="form-control"
              min="1"
              value={travelers}
              onChange={(e) => setTravelers(parseInt(e.target.value) || 1)}
            />
          </div>

          <div className="form-group">
            <label>Travel Type</label>
            <select className="form-control" value={travelType} onChange={(e) => setTravelType(e.target.value)}>
              <option value="solo">Solo</option>
              <option value="family">Family</option>
              <option value="friends">Friends</option>
            </select>
          </div>

          <div className="form-group">
            <label>Preferred Transport</label>
            <select className="form-control" value={preferredTransport} onChange={(e) => setPreferredTransport(e.target.value)}>
              <option value="transit">Public Metro/Bus</option>
              <option value="cab">Taxi / Cab</option>
              <option value="walking">Walking</option>
            </select>
          </div>

          <div className="form-group">
            <label>Personalized Memory / Preferences</label>
            <form onSubmit={addPreference} className="preference-input-group">
              <input
                type="text"
                className="form-control"
                placeholder="Add e.g. Loves parks"
                value={newPref}
                onChange={(e) => setNewPref(e.target.value)}
              />
              <button type="submit" className="btn-secondary" style={{ padding: '0.75rem' }}>+</button>
            </form>
            <div className="preferences-container">
              {preferences.map((pref) => (
                <span key={pref} className="preference-tag" onClick={() => removePreference(pref)}>
                  {pref} ✕
                </span>
              ))}
            </div>
          </div>

          <button onClick={fetchPlan} className="btn-primary" disabled={loading}>
            {loading ? 'Analyzing Plan...' : 'Generate AI Smart Itinerary'}
          </button>
        </div>

        {/* Right Side: Tabbed Results */}
        <div className="main-content">
          {error && (
            <div className="content-panel" style={{ borderColor: 'var(--danger)', color: 'var(--danger)' }}>
              <h3>Execution Error</h3>
              <p>{error}</p>
            </div>
          )}

          {loading && !plan && (
            <div className="loading-overlay">
              <div className="spinner"></div>
              <h3>Assembling components...</h3>
              <p>Fetching forecast warnings, places coordinates, route directions, and safety indicators...</p>
            </div>
          )}

          {!plan && !loading && (
            <div className="empty-state">
              <div className="empty-state-icon">🧭</div>
              <h3>No Active Trip Loaded</h3>
              <p>Modify the destination details and preferences in the panel and click Generate to run the AI Smart Companion orchestrator.</p>
            </div>
          )}

          {plan && (
            <>
              {/* Tab Navigation links */}
              <div className="tabs-navigation">
                <button
                  className={`tab-btn ${activeTab === 'timeline' ? 'active' : ''}`}
                  onClick={() => setActiveTab('timeline')}
                >
                  Day-wise Timeline
                </button>
                <button
                  className={`tab-btn ${activeTab === 'budget' ? 'active' : ''}`}
                  onClick={() => setActiveTab('budget')}
                >
                  Budget Breakdown
                </button>
                <button
                  className={`tab-btn ${activeTab === 'weather' ? 'active' : ''}`}
                  onClick={() => setActiveTab('weather')}
                >
                  Weather Alerts
                </button>
                <button
                  className={`tab-btn ${activeTab === 'hotels' ? 'active' : ''}`}
                  onClick={() => setActiveTab('hotels')}
                >
                  Hotels
                </button>
                <button
                  className={`tab-btn ${activeTab === 'restaurants' ? 'active' : ''}`}
                  onClick={() => setActiveTab('restaurants')}
                >
                  Restaurants
                </button>
                <button
                  className={`tab-btn ${activeTab === 'navigation' ? 'active' : ''}`}
                  onClick={() => setActiveTab('navigation')}
                >
                  Transit Details
                </button>
                <button
                  className={`tab-btn ${activeTab === 'safety' ? 'active' : ''}`}
                  onClick={() => setActiveTab('safety')}
                >
                  Safety Metrics
                </button>
              </div>

              {/* TIMELINE TAB */}
              {activeTab === 'timeline' && (
                <div className="content-panel">
                  <div className="panel-header-action">
                    <h2>Day-wise Timeline</h2>
                    <button className="btn-secondary" onClick={() => regeneratePart('weather')}>
                      🌧️ Simulate Weather Change
                    </button>
                  </div>

                  <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                    {plan.ai_reasoning?.executive_summary}
                  </p>

                  <div className="timeline">
                    {plan.itinerary?.map((day) => (
                      <div key={day.day} className={`timeline-day ${day.weather?.has_rain ? 'rainy-day' : ''}`}>
                        <div className="timeline-marker">{day.day}</div>
                        <div className="timeline-header">
                          <div className="timeline-title">Day {day.day} - {day.date}</div>
                          <span className="timeline-weather-tag">
                            🌡️ {day.weather?.avg_temp}°C | {day.weather?.description}
                          </span>
                        </div>
                        <div className="timeline-body">
                          <div className="activity-block">
                            <div className="activity-label">Morning Activity</div>
                            <div className="activity-text">{day.activities?.morning}</div>
                          </div>

                          <div className="activity-block">
                            <div className="activity-label">Lunch Recommendation</div>
                            <div className="activity-text">
                              🍴 <strong>{day.meals?.lunch?.name}</strong> - {day.meals?.lunch?.cuisine} (Average: ₹{day.meals?.lunch?.average_meal_cost})
                              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                                Popular: {day.meals?.lunch?.popular_dishes?.join(', ')}
                              </p>
                            </div>
                          </div>

                          <div className="activity-block">
                            <div className="activity-label">Afternoon Activity</div>
                            <div className="activity-text">{day.activities?.afternoon}</div>
                          </div>

                          <div className="activity-block">
                            <div className="activity-label">Dinner Recommendation</div>
                            <div className="activity-text">
                              🍴 <strong>{day.meals?.dinner?.name}</strong> - {day.meals?.dinner?.cuisine} (Average: ₹{day.meals?.dinner?.average_meal_cost})
                            </div>
                          </div>

                          {day.weather_adjustment_reason && (
                            <div className="safety-alert-box" style={{ background: 'rgba(245, 158, 11, 0.05)', borderColor: 'var(--warning)', marginTop: '1rem' }}>
                              ⚡ <strong>Weather Adjustments:</strong> {day.weather_adjustment_reason}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="reasoning-box">
                    <div className="reasoning-title">Weather Adaptation Reasoning</div>
                    <div className="reasoning-text">
                      {plan.ai_reasoning?.weather_adaptation_reason}
                    </div>
                  </div>
                </div>
              )}

              {/* BUDGET TAB */}
              {activeTab === 'budget' && (
                <div className="content-panel">
                  <div className="panel-header-action">
                    <h2>Budget Summary & Cost Breakdown</h2>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <input
                        type="number"
                        className="form-control"
                        style={{ width: '100px' }}
                        value={budget}
                        onChange={(e) => setBudget(parseFloat(e.target.value) || 0)}
                      />
                      <button className="btn-secondary" onClick={() => regeneratePart('budget')}>
                        💸 Adjust Budget Limit
                      </button>
                    </div>
                  </div>

                  <div className="budget-grid">
                    <div className="budget-card">
                      <div className="budget-label">Transport (30%)</div>
                      <div className="budget-value">₹{plan.budget_summary?.allocation?.transport}</div>
                    </div>
                    <div className="budget-card">
                      <div className="budget-label">Hotel (35%)</div>
                      <div className="budget-value">₹{plan.budget_summary?.allocation?.hotel}</div>
                    </div>
                    <div className="budget-card">
                      <div className="budget-label">Food (15%)</div>
                      <div className="budget-value">₹{plan.budget_summary?.allocation?.food}</div>
                    </div>
                    <div className="budget-card">
                      <div className="budget-label">Activities (10%)</div>
                      <div className="budget-value">₹{plan.budget_summary?.allocation?.activities}</div>
                    </div>
                    <div className="budget-card">
                      <div className="budget-label">Emergency (10%)</div>
                      <div className="budget-value">₹{plan.budget_summary?.allocation?.emergency}</div>
                    </div>
                  </div>

                  <div className="cost-breakdown-chart">
                    <h3>Percentage Allocation Visual</h3>

                    <div className="cost-bar-group" style={{ marginTop: '1rem' }}>
                      <div className="cost-bar-label">
                        <span>Transport</span>
                        <span>30%</span>
                      </div>
                      <div className="cost-bar-outer">
                        <div className="cost-bar-inner" style={{ width: '30%' }}></div>
                      </div>
                    </div>

                    <div className="cost-bar-group">
                      <div className="cost-bar-label">
                        <span>Hotel</span>
                        <span>35%</span>
                      </div>
                      <div className="cost-bar-outer">
                        <div className="cost-bar-inner" style={{ width: '35%', background: 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)' }}></div>
                      </div>
                    </div>

                    <div className="cost-bar-group">
                      <div className="cost-bar-label">
                        <span>Food</span>
                        <span>15%</span>
                      </div>
                      <div className="cost-bar-outer">
                        <div className="cost-bar-inner" style={{ width: '15%', background: 'linear-gradient(135deg, #10b981 0%, #3b82f6 100%)' }}></div>
                      </div>
                    </div>

                    <div className="cost-bar-group">
                      <div className="cost-bar-label">
                        <span>Activities</span>
                        <span>10%</span>
                      </div>
                      <div className="cost-bar-outer">
                        <div className="cost-bar-inner" style={{ width: '10%', background: 'linear-gradient(135deg, #f59e0b 0%, #10b981 100%)' }}></div>
                      </div>
                    </div>

                    <div className="cost-bar-group">
                      <div className="cost-bar-label">
                        <span>Emergency Backup</span>
                        <span>10%</span>
                      </div>
                      <div className="cost-bar-outer">
                        <div className="cost-bar-inner" style={{ width: '10%', background: 'linear-gradient(135deg, #ef4444 0%, #f59e0b 100%)' }}></div>
                      </div>
                    </div>
                  </div>

                  <div style={{ marginTop: '1.5rem', color: 'var(--text-secondary)' }}>
                    💵 <strong>Individual Cost Share:</strong> Per person total allocated budget is <strong>₹{plan.budget_summary?.per_person?.total}</strong>.
                  </div>
                </div>
              )}

              {/* WEATHER TAB */}
              {activeTab === 'weather' && (
                <div className="content-panel">
                  <div className="panel-header-action">
                    <h2>Live Weather & Weekly Forecast</h2>
                    <span className="weather-temp-badge" style={{ fontSize: '1rem', margin: 0 }}>
                      🌦️ {city} Alerts
                    </span>
                  </div>

                  <div className="weather-grid">
                    {plan.weather?.forecast?.map((day) => {
                      let typeClass = '';
                      if (day.has_rain) typeClass = 'rain-alert';
                      else if (day.high_temp) typeClass = 'heat-warning';

                      return (
                        <div key={day.date} className={`weather-day-card ${typeClass}`}>
                          <div className="weather-date">{day.date}</div>
                          <div className="weather-temp-badge">{day.max_temp}°C</div>
                          <p style={{ fontSize: '0.85rem', marginBottom: '0.5rem', textTransform: 'capitalize' }}>
                            {day.description}
                          </p>
                          <span className="weather-status-badge">{day.status}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* HOTELS TAB */}
              {activeTab === 'hotels' && (
                <div className="content-panel">
                  <div className="panel-header-action">
                    <h2>Hotel Recommendations</h2>
                    <button className="btn-secondary" onClick={() => regeneratePart('hotel')}>
                      🔄 Rotate Top Hotel Option
                    </button>
                  </div>

                  <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                    {plan.ai_reasoning?.hotel_choice_reason}
                  </p>

                  {plan.hotels?.map((hotel, idx) => (
                    <div key={hotel.name} className="hotel-card" style={{ borderColor: idx === 0 ? 'var(--accent-primary)' : 'var(--border-card)' }}>
                      <div className="hotel-header">
                        <div>
                          <span className="hotel-title">{hotel.name}</span>
                          {idx === 0 && <span style={{ marginLeft: '0.75rem', fontSize: '0.7rem', padding: '0.2rem 0.5rem', borderRadius: '4px', background: 'var(--accent-primary)', fontWeight: 'bold' }}>TOP PICK</span>}
                        </div>
                        <span className="hotel-rating-badge">★ {hotel.rating} ({hotel.review_count} reviews)</span>
                      </div>

                      <div className="hotel-price">₹{hotel.price_per_night} / night</div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>📍 {hotel.address}</div>

                      <div className="hotel-details">
                        <span>🏢 Center: {hotel.distance_from_center_km} km</span>
                        <span>🚇 Public Transit: {hotel.distance_to_transport_km} km</span>
                        <span>🏥 Medical Centre: {hotel.distance_to_hospital_km} km</span>
                        <span>👮 Police Unit: {hotel.distance_to_police_km} km</span>
                        <span>🛎️ 24h Reception: {hotel.has_24hr_reception ? 'Available' : 'Unavailable'}</span>
                      </div>

                      <div className="hotel-reason">
                        💡 {hotel.reason}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* RESTAURANTS TAB */}
              {activeTab === 'restaurants' && (
                <div className="content-panel">
                  <h2>Restaurant Recommendations</h2>
                  <p style={{ color: 'var(--text-secondary)', margin: '0.5rem 0 1.5rem' }}>
                    {plan.ai_reasoning?.restaurant_choice_reason}
                  </p>

                  <div className="restaurant-grid">
                    {plan.restaurants?.map((rest) => (
                      <div key={rest.name} className="restaurant-card">
                        <div className="restaurant-cuisine">{rest.cuisine}</div>
                        <h3 style={{ fontSize: '1.1rem', marginBottom: '0.25rem' }}>{rest.name}</h3>
                        <span className="hotel-rating-badge" style={{ fontSize: '0.75rem' }}>★ {rest.rating} ({rest.review_count})</span>

                        <div className="restaurant-dishes">
                          <strong>Popular items:</strong> {rest.popular_dishes?.join(', ')}
                        </div>

                        <div style={{ fontSize: '0.85rem', margin: '0.5rem 0' }}>
                          💵 Avg Cost: <strong>₹{rest.average_meal_cost}</strong>
                        </div>

                        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                          📍 Distance: {rest.distance_km} km
                        </div>

                        <div style={{ fontSize: '0.8rem', color: 'var(--success)', marginTop: '0.5rem' }}>
                          {rest.vegetarian_available ? '🌱 Vegetarian Options Available' : ''}
                        </div>

                        <div className="hotel-reason" style={{ fontSize: '0.8rem', padding: '0.5rem 0.75rem', marginTop: '0.75rem' }}>
                          💡 {rest.reason}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TRANSIT/NAVIGATION TAB */}
              {activeTab === 'navigation' && (
                <div className="content-panel">
                  <h2>Smart Navigation Assistant</h2>

                  {plan.navigation ? (
                    <div style={{ marginTop: '1.5rem' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                        <div className="budget-card" style={{ textAlign: 'left' }}>
                          <div className="budget-label">Total Distance</div>
                          <div className="budget-value" style={{ fontSize: '1.25rem' }}>{plan.navigation?.distance_text}</div>
                        </div>
                        <div className="budget-card" style={{ textAlign: 'left' }}>
                          <div className="budget-label">Transit Duration</div>
                          <div className="budget-value" style={{ fontSize: '1.25rem' }}>{plan.navigation?.duration_text}</div>
                        </div>
                      </div>

                      <div className="budget-card" style={{ textAlign: 'left', marginBottom: '1.5rem', background: 'rgba(59, 130, 246, 0.05)', borderColor: 'var(--info)' }}>
                        <div className="budget-label">Cab Estimate</div>
                        <div className="budget-value" style={{ fontSize: '1.25rem', color: 'var(--info)' }}>
                          ₹{plan.navigation?.cab_estimate_inr}
                        </div>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                          Estimated based on local taxi coefficients.
                        </p>
                      </div>

                      <div style={{ marginBottom: '1.5rem' }}>
                        <h4 style={{ marginBottom: '0.5rem' }}>🚶 Detailed Walking Directions</h4>
                        <ul className="nav-steps-list">
                          {plan.navigation?.walking_steps?.map((step, idx) => (
                            <li key={idx} className="nav-step-item">{step}</li>
                          ))}
                        </ul>
                      </div>

                      <div style={{ marginBottom: '1.5rem' }}>
                        <h4 style={{ marginBottom: '0.5rem' }}>🚇 Transit Connections</h4>
                        {plan.navigation?.transit_recommendations?.length > 0 ? (
                          <ul className="nav-steps-list">
                            {plan.navigation?.transit_recommendations?.map((transit, idx) => (
                              <li key={idx} className="nav-step-item" style={{ color: 'var(--accent-secondary)' }}>{transit}</li>
                            ))}
                          </ul>
                        ) : (
                          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>No direct subway or metro options. Walking or cab transit suggested.</p>
                        )}
                      </div>

                      <div className="safety-alert-box">
                        🚦 <strong>Traffic Alert:</strong> {plan.navigation?.traffic_info} (Leave {plan.navigation?.recommended_departure_buffer_mins} mins early to buffer delays).
                      </div>
                    </div>
                  ) : (
                    <p>No navigation parameters compiled. Please choose a hotel Pick first.</p>
                  )}
                </div>
              )}

              {/* SAFETY TAB */}
              {activeTab === 'safety' && (
                <div className="content-panel">
                  <h2>Smart Safety Assistant</h2>

                  {plan.safety ? (
                    <div style={{ marginTop: '1.5rem' }}>
                      <div className="safety-scoring">
                        <div className="safety-percentage-circle">
                          {plan.safety?.safety_score_percentage}%
                        </div>
                        <div>
                          <h3 style={{ color: 'var(--accent-secondary)' }}>{plan.safety?.safety_tier}</h3>
                          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.25rem' }}>
                            Safety index calculated using neighborhood service indexes and crowdsource activity.
                          </p>
                        </div>
                      </div>

                      <p style={{ fontSize: '1rem', marginBottom: '1.5rem' }}>
                        {plan.safety?.assessment_details}
                      </p>

                      <div className="hotel-details" style={{ fontSize: '0.85rem' }}>
                        <span>🏥 Nearest Hospital: {plan.safety?.nearby_services?.hospital_distance_km} km</span>
                        <span>👮 Nearest Police Unit: {plan.safety?.nearby_services?.police_distance_km} km</span>
                        <span>🚇 Nearest Public Transit: {plan.safety?.nearby_services?.public_transit_distance_km} km</span>
                      </div>

                      <div className="safety-alert-box" style={{ background: 'rgba(16, 185, 129, 0.05)', borderColor: 'var(--success)', color: 'var(--text-primary)' }}>
                        🛡️ <strong>Safety Disclaimer:</strong> {plan.safety?.disclaimer} We recommend cross-referencing regional warnings before departure.
                      </div>
                    </div>
                  ) : (
                    <p>No safety logs generated for this pick.</p>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
